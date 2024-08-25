# General
A collection of Ansible playbooks for automated [frontend](https://github.com/gsoldatov/site_frontend) & [backend](https://github.com/gsoldatov/site_backend) site deployment.


# Repository Setup & Update
0. The following dependencies are assumed to be install on the machine, where playbooks are going to be run:
    - **Postgresql 14** for storing site logs, after `deployment_management_setup.yml` playbooks is run;
    - **Grafana 9** for displaying monitoring dashboard;

1. Create virtual env, if it does not exist, & install dependencies:
    ```bash
    cd /path/to/repository/root
    python3 -m venv venv --prompt "Deployment management"
    source venv/bin/activate
    pip install -r requirements.txt
    ```

2. Create or update a `production.env` file (in the directory of this file) with valid site settings (see `production.env.example`);
3. Configure Grafana & import monitoring dashboards (see `<root_dir>/monitoring/Readme.md`).


# Running Playbooks
Playbooks can be run via `run.sh` script, which reads the environment variables, toggles Python venv and selects the appropriate user/auth method for the playbook being run.

```bash
./run.sh <playbook name> [--env-file <env_filename>] [ansible-playbook options]
```

`<playbook name>` is the name of the playbook .yml file in the script folder.


# Playbook Description
## New Deployment
- `server_config.yml`: runs initial security & user configuration + dependency installation (should be executed before other playbooks);
- `deploy.yml`: deploys new site frontend & backend instances on a single machine behind an Nginx reverse proxy (should be executed after `server_config.yml`);

## Updates
- `update_frontend.yml`: updates frontend on an existing single machine deployment;
- `update_backend.yml`: updates backend on an existing single machine deployment.

## SSL Setup
- `ssl_lets_encrypt.yml`: installs & schedules updates for a Let's Encrypt certificate on an existing single machine deployment (NOTE: existing deployment should be snapshotted, since multiple attempts may be required to avoid Let's Encrypt generation limits);
- `ssl_self_signed.yml`: generates a self-signed SSL certificate for Nginx.

## Monitoring & Backups
- `deployment_management_setup.yml`: configures automatic site backup & monitoring data fetches using this repository;
- `deployment_management_uninstall.yml`: disables cron jobs for automatic site backup & monitoring;
- `backup_execute.yml`: runs a manual site backup execution (also used by scheduled backup in the repo copy); 
    can be run with `backup_db` or `backup_static_files` tags to perform a specific part of backup;


# Additional Playbook Information
`server_config.yml` is run as root user with password authentication & creates a deployment user, which runs other playbooks.
Role for setting up the static folder, however, can be run separately by passing `-U` flag and `static` tag:
```bash
./run.sh run.sh server_config.yml -U --tags "static"
```

Default .env filename is `production.env`. Custom filename can be provided with the `--env-file` option.

Nginx configuration can be updated by running `deploy.yml` with `nginx` tag specified:
```bash
./run.sh run.sh deploy.yml --tags "nginx"
```
