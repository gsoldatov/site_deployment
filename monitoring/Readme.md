# General
Monitoring utilities for site production deployment. Contains data fetching scripts and visualization files for Grafana.

# Monitoring Setup
Database and scheduled data fetching can be setup by running `ansible/deployment_management_setup.yml` playbook (see `ansible/Readme.md`). 

Grafana must be installed and configured manually. Configuration includes the following steps:
0. Run the `deployment_management_setup.yml` playbook.
1. Create a Grafana data source for the site logs database.
2. Import each dashboard from `grafana` folder (Dashboards > Browse > New > Import > Upload JSON file).
3. Open each imported dashboard, set `logs_db` variable and save the dashboard (**including the variable values**, which requires to select a corresponding checkbox in the save menu).

# Development How-tos
## Database Setup
1. Run `db/setup.py` script to create database & user:
```bash
source ../venv/bin/activate
# config path can be relative to `monitoring` folder
python db/setup.py [-c "/path/to/config.json/file"]
```
2. Apply Alembic migrations:
```bash
cd db
# config path can be relative to `monitoring` folder
alembic [-x monitoring_config="/path/to/config.json/file"] upgrade head
```

## Migration Script Generation
```bash
cd db
# config path can be relative to `monitoring` folder
alembic [-x monitoring_config="/path/to/config.json/file"] revision --autogenerate -m "<Revision description>"
```
