#!/bin/bash
# Runs a playbook with the name specified as the first argument
# Additional params for ansible-playbook can be passed after the playbook name

# Check playbook name
NAME=$1

if [ -z "$NAME" ]; then
    echo 'Runs a specified Ansible playbook in the script folder.'
    echo
    echo 'Syntax: run.sh <playbook>'
    echo 'where <playbook> is the name of one of the playbooks in the directory of this script.'

    exit 1
fi

DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )    # Script directory
PLAYBOOK="$DIR/$NAME"

if [[ ! -f $PLAYBOOK ]]; then
    echo "File '$PLAYBOOK' does not exist."
    exit 1
fi

# Activate venv & load environment variables
source $DIR/../venv/bin/activate
source $DIR/production.env

# Build inventory file for Ansible
envsubst < $DIR/hosts.yml.example > $DIR/hosts.yml

# Run playbook
ansible-playbook -i $DIR/hosts.yml $PLAYBOOK "${@:2}";  # pass the the rest of CLI args to ansible-playbook

# Deactivate venv
deactivate;
