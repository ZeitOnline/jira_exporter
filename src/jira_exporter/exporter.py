from datetime import datetime
import argparse
import collections
import jira
import logging
import os
import prometheus_client
import prometheus_client.core
import prometheus_client.exposition
import prometheus_client.samples
import requests
import sys
import time


log = logging.getLogger(__name__)
LOG_FORMAT = '%(asctime)s %(levelname)-5.5s %(message)s'


class Cloneable(object):

    def clone(self):
        return type(self)(
            self.name, self.documentation, labels=self._labelnames)


class Gauge(prometheus_client.core.GaugeMetricFamily, Cloneable):
    pass


class IssueCollector:

    _cache_value = None
    _cache_updated_at = 0

    def configure(self, base_url, username, password, cache_ttl):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.cache_ttl = cache_ttl

    METRICS = {
        'issues': Gauge(
            'jira_issues_total',
            'Error events collected by Bugsnag, by project',
            labels=['project', 'status']),
        'scrape_duration': Gauge(
            'jira_scrape_duration_seconds',
            'Duration of Jira API scrape'),
    }

    def describe(self):
        return self.METRICS.values()

    def collect(self):
        start = time.time()

        if start - self._cache_updated_at <= self.cache_ttl:
            log.info('Returning cached result from %s',
                     datetime.fromtimestamp(self._cache_updated_at))
            return self._cache_value

        api = jira.JIRA(
            server=self.base_url, basic_auth=(self.username, self.password))

        # Use a separate instance for each scrape request, to prevent
        # race conditions with simultaneous scrapes.
        metrics = {
            key: value.clone() for key, value in self.METRICS.items()}

        log.info('Retrieving data from Jira API')
        statuses = api.statuses()

        for project in api.projects():
            for status in statuses:
                status = status.name
                try:
                    issues = api.search_issues(
                        'project="%s" AND status="%s"' % (project.key, status),
                        json_result=True, maxResults=0)
                    count = issues.get('total', 0)
                    if count:
                        # Statuses is the union of all possible statuses, not
                        # just the ones applicable for this project, so let's
                        # not create lots of zero-valued unhelpful time series.
                        metrics['issues'].add_metric(
                            (project.key, status), count)
                except Exception:
                    log.warning('Error for project %s, ignored.', project.key,
                                exc_info=True)
                    break

        stop = time.time()
        metrics['scrape_duration'].add_metric((), stop - start)
        self._cache_value = metrics.values()
        self._cache_updated_at = stop
        return self._cache_value


COLLECTOR = IssueCollector()
# We don't want the `process_` and `python_` metrics, we're a collector,
# not an exporter.
REGISTRY = prometheus_client.core.CollectorRegistry()
REGISTRY.register(COLLECTOR)
APP = prometheus_client.make_wsgi_app(REGISTRY)


def main():
    parser = argparse.ArgumentParser(
        description='Export Jira issues as prometheus metrics')
    parser.add_argument('--url', help='Jira base url')
    parser.add_argument('--username', help='Jira API username')
    parser.add_argument('--password', help='Jira API token')
    parser.add_argument('--host', default='', help='Listen host')
    parser.add_argument('--port', default=9642, type=int, help='Listen port')
    parser.add_argument('--ttl', default=600, type=int, help='Cache TTL')
    options = parser.parse_args()
    if not options.url:
        options.url = os.environ.get('JIRA_URL')
    if not options.username:
        options.username = os.environ.get('JIRA_USERNAME')
    if not options.password:
        options.password = os.environ.get('JIRA_PASSWORD')

    logging.basicConfig(
        stream=sys.stdout, level=logging.INFO, format=LOG_FORMAT)

    COLLECTOR.configure(
        options.url, options.username, options.password, options.ttl)

    log.info('Listening on 0.0.0.0:%s', options.port)
    httpd = prometheus_client.exposition.make_server(
        options.host, options.port, APP,
        handler_class=prometheus_client.exposition._SilentHandler)
    httpd.serve_forever()
