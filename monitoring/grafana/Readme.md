# Overview
`dashboards` folder contains site monitoring dashboards exported from Grafana into JSON files:
- `healthcheck.json` is an overview dashboard with main site & server indicators;
- `auth.json` provides server & backend auth statistics & logs;
- `requests_and_scheduled_jobs.json` provides Nginx & backend request processing statistics;
- `log_fetching_and_backups.json` contains statistics & logs for the log fetching and local site backup jobs.

# Dashboard Import Steps
The following steps should be performed in order to manually import dashboards in another Grafana instance:
1. create data source for site logs database, if required;
2. on the `Dashboards > browse` panel import each dashboard from corresponding JSON file.
3. If a new datasource was created in step 1, open each dashboard, select the correct datasource in `logs_db` variable and save dashboard **with variables** (toggle checkbox in the save menu).
