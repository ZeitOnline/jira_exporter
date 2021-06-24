# docker build --tag eu.gcr.io/zeitonline-210413/jira-exporter:PACKAGEVERSION-DOCKERVERSION .
FROM python:3-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-deps -r requirements.txt
ENTRYPOINT ["jira_exporter"]
