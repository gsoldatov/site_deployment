A collection of Ansible playbooks for automated [frontend](https://github.com/gsoldatov/site_frontend) & [backend](https://github.com/gsoldatov/site_backend) site deployment.

Playbooks can be run via `run.sh` script, which reads the environment variables, toggles Python venv and selects the appropriate user/auth method for the playbook being run.

```bash
bash run.sh <playbook name> [--env-file <env_filename>] [ansible-playbook options]
```

`<playbook name>` is the name of the playbook .yml file in the script folder.

Playbooks include:
- deployment, update & ssl:
    - `deploy.yml`: deploys frontend & backend on a single machine behind an Nginx reverse proxy (should be executed after `server_config.yml`);
    - `server_config.yml`: performs initial security & user configuration + dependency installation (should be executed before other playbooks);
    - `ssl_self_signed.yml`: generates self-signed SSL certificate & keys used by Nginx;
    - `update_backend.yml`: updates backend on an existing single machine deployment;
    - `update_frontend.yml`: updates frontend on an existing single machine deployment;
- backups:
    - `backend_execute.yml`: runs site backup operations (manually or when scheduled);
    - `backup_schedule.yml`: schedules automatic site backup on local machine;
    - `backup_unschedule.yml`: removes scheduled automatic site backup on local machine.

`server_config.yml` is run as root user with password authentication & creates a deployment user, which runs other playbooks.

Default .env filename is `production.env`. Custom filename can be provided with the `--env-file` option.
