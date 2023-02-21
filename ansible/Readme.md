# General
A collection of Ansible playbooks for automated [frontend](https://github.com/gsoldatov/site_frontend) & [backend](https://github.com/gsoldatov/site_backend) site deployment.

Playbooks can be run via `run.sh` script, which reads the environment variables, toggles Python venv and selects the appropriate user/auth method for the playbook being run.

```bash
bash run.sh <playbook name> [--env-file <env_filename>] [ansible-playbook options]
```

`<playbook name>` is the name of the playbook .yml file in the script folder.

# Playbook Description
## New Deployment
- `server_config.yml`: initial security & user configuration + dependency installation (should be executed before other playbooks);
- `deploy.yml`: new frontend & backend deployment on a single machine behind an Nginx reverse proxy (should be executed after `server_config.yml`);

## Updates
- `update_frontend.yml`: frontend update on an existing single machine deployment;
- `update_backend.yml`: backend update on an existing single machine deployment.

## SSL Setup
- `ssl_lets_encrypt.yml`: Let's Encrypt certificate setup & auto-update scheduling on an existing single machine deployment (NOTE: existing deployment should be snapshotted, since multiple attempts may be required to avoid Let's Encrypt generation limits);
- `ssl_self_signed.yml`: self-signed SSL certificate generation for Nginx.

## Monitoring & Backups
- `deployment_management_setup.yml`: automatic site backup & monitoring data fetch setup run from a copy on this repository;
- `deployment_management_uninstall.yml`: automatic site backup & monitoring unscheduling;
- `backup_execute.yml`: manual site backup execution (also used by scheduled backup in the repo copy).

# Additional Playbook Information
`server_config.yml` is run as root user with password authentication & creates a deployment user, which runs other playbooks.

Default .env filename is `production.env`. Custom filename can be provided with the `--env-file` option. `deployment_management_setup.yml` playbook copies the specified env file into the repository copy under `production.env` name.
