# General
Monitoring utilities for site production. Contains data fetching scripts and visualization files for Grafana.

# Database Setup
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

# Migration Script Generation
```bash
cd db
# config path can be relative to `monitoring` folder
alembic [-x monitoring_config="/path/to/config.json/file"] revision --autogenerate -m "<Revision description>"
```
