#!/bin/bash
: '
Runs a playbook with the name specified as the first argument.
Additional params for ansible-playbook can be passed after the playbook name.

Installs sshpass on the local machine if it is absent & password authentication is used.
'


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


# Ensure that sshpass is installed on the local machine, if passowrd authentication is used (required by Ansible)
if [ $NAME == 'server_config.yml' ]; then
    echo "Using SSH with password auth, ensuring sshpass is installed..."
    if ! [ -x "$(command -v sshpass)" ]; then
        echo "Installing sshpass..."
        sudo apt update 
        sudo apt install -y sshpass
        if [ $? -gt 0 ]; then
            echo "Failed to install sshpass."
            exit 1
        fi
    fi
fi


# Activate venv & load environment variables
source $DIR/../venv/bin/activate
source $DIR/production.env


# Set environment variables for inventory file based on the playbook being run
case $NAME in
    server_config.yml)
        # Server configuration is run under root user with passowrd authentication
        export ANSIBLE_USER=root;
        ANSIBLE_PASSWORD=$DEFAULT_ROOT_PASSWORD;;
    *)
        # Other playbooks are run under deployment user with key authentication
        export ANSIBLE_USER=$SERVER_USER;;
esac

export ANSIBLE_HOST=$SERVER_ADDR;
if [[ $ANSIBLE_PASSWORD ]]; then
    export ANSIBLE_PASSWORD_LINE="ansible_password: $ANSIBLE_PASSWORD"
fi


# Build inventory file for Ansible
envsubst < $DIR/hosts.yml.example > $DIR/hosts.yml


# Run playbook
ansible-playbook -i $DIR/hosts.yml $PLAYBOOK "${@:2}";  # pass the the rest of CLI args to ansible-playbook


# Deactivate venv
deactivate;
