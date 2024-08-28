# General
Monitoring utilities for site production deployment. Contains data fetching scripts and visualization files for Grafana.

# Monitoring Setup
Database and scheduled data fetching can be setup by running `ansible/deployment_management_setup.yml` playbook (see `<root_dir>/ansible/Readme.md`). 

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
# env_file path can be absolute or relative to `<project_root>/ansible` folder
python db/setup.py [-e "/path/to/env/file"]
```
2. Apply Alembic migrations:
```bash
cd db
# env_file path can be absolute or relative to `<project_root>/ansible` folder
alembic [-x env_file="/path/to/env/file"] upgrade head
```

## Migration Script Generation
```bash
cd db
# env_file path can be absolute or relative to `<project_root>/ansible` folder
alembic [-x env_file="/path/to/env/file"] revision --autogenerate -m "<Revision description>"
```
