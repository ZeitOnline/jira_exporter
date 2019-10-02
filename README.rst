====================================
Prometheus Jira issue count exporter
====================================

This package exports metrics about `Jira`_ issues as `Prometheus`_ metrics.

.. _`Jira`: https://jira.atlassian.com
.. _`Prometheus`: https://prometheus.io


Usage
=====

Configure API token
-------------------

You'll need to provide an API token to access the Jira REST API.
Currently HTTP Basic authentication is used.
See the `Jira documentation`_ for details.

.. _`Jira documentation`: https://developer.atlassian.com/cloud/jira/platform/jira-rest-api-basic-authentication/


Start HTTP service
------------------

Start the HTTP server like this::

    $ JIRA_URL=https://example.atlassian.net JIRA_USERNAME=test@example.com JIRA_PASSWORD=APITOKEN jira_exporter --host=127.0.0.1 --port=9653

Pass ``--ttl=SECONDS`` to cache API results for the given time or -1 to disable (default is 600).
Prometheus considers metrics stale after 300s, so that's the highest scrape_interval one should use.
However it's usually unnecessary to hit the API that often, since the vulnerability alert information does not change that rapidly.


Configure Prometheus
--------------------

::

    scrape_configs:
      - job_name: 'jira'
        scrape_interval: 300s
        static_configs:
          - targets: ['localhost:9653']

We export one metric, a gauge called ``jira_issues_total``,
with labels ``{project="PROJ", status="open"}``.

Additionally, a ``jira_scrape_duration_seconds`` gauge is exported.
