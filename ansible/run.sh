#!/bin/bash
: '
Runs a playbook with the name specified as the first argument.
Additional params for ansible-playbook can be passed after the playbook name.

Installs sshpass on the local machine if it is absent & password authentication is used.
'
# Default variable values
export ENV_FILE=production.env


# Get script options & filter Ansible options
declare -a ANSIBLE_OPTS
ANSIBLE_OPTS=()

NAME=$1; shift

while (( "$#" )); do    # Loop through input options, filter script options & save rest for Ansible
    case "$1" in
        -h|--help) HELP=1; shift;;

        --env-file) ENV_FILE=$2; shift; shift;;

        -U|--disable-ansible-user-override) DISABLE_ANSIBLE_USER_OVERRIDE=1; shift;;

        *) ANSIBLE_OPTS+=("$1"); shift;;
    esac
done


# Display usage
if [ -z "$NAME" ] || [[ $NAME == @(-h|--help) ]] || [ ! -z "$HELP" ]; then 
    echo 'Runs a specified Ansible playbook in the script folder.'
    echo 'Specifies, which user is used to run the playbook (root or deployment user) based on its name.'
    echo
    echo 'Syntax: run.sh <playbook> [ansible-playbook opts] [--env-file <custom_path_to_env_file>] [-U|--disable-ansible-user-override] [-h|--help] [more ansible-playbook opts]'
    echo '<playbook> is the name of one of the playbooks in the directory of this script.'
    echo '-h or --help to display this message and exit'
    echo '--env-file to override file with environment variables (defaults to $ENV_FILE)'
    echo '-U or --disable-ansible-user-override to disable automatic selection of a user, under which a playbook is run'
    echo 'Additional options can be passed for Ansible after the name of the playbook.'

    exit 1
fi


# Check if playbook & env file exist
DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )    # Script directory
PLAYBOOK="$DIR/$NAME"

if [[ ! -f $PLAYBOOK ]]; then
    echo "Playbook '$PLAYBOOK' does not exist."
    exit 1
fi

ENV_FILE_FULLPATH=$DIR/$ENV_FILE;
if [[ ! -f $ENV_FILE_FULLPATH ]]; then
    echo "Env file '$ENV_FILE_FULLPATH' does not exist."
    exit 1
fi


# Ensure that sshpass is installed on the local machine, if passowrd authentication is used (required by Ansible)
if [ $NAME == 'server_config.yml' ] && [ -z "$DISABLE_ANSIBLE_USER_OVERRIDE" ]; then
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
source $ENV_FILE_FULLPATH


# Set environment variables for inventory file based on the playbook being run
case $NAME in
    server_config.yml)
        # Server configuration is run under root user with passowrd authentication (unless this is disabled by the CLI flag)
        if [ -z "$DISABLE_ANSIBLE_USER_OVERRIDE" ]; then 
            export ANSIBLE_USER=root
            ANSIBLE_PASSWORD=$DEFAULT_ROOT_PASSWORD
        else
            export ANSIBLE_USER=$DEPLOYMENT_USER_NAME
            export ANSIBLE_BECOME_PASSWORD=$DEPLOYMENT_USER_PASSWORD
        fi
        ;;
        
    *)
        # Other playbooks are run under deployment user with key authentication
        export ANSIBLE_USER=$DEPLOYMENT_USER_NAME;
        export ANSIBLE_BECOME_PASSWORD=$DEPLOYMENT_USER_PASSWORD;;
esac

export ANSIBLE_HOST=$SERVER_ADDR;
if [[ $ANSIBLE_PASSWORD ]]; then export ANSIBLE_PASSWORD_LINE="ansible_password: $ANSIBLE_PASSWORD"; fi
if [[ $ANSIBLE_BECOME_PASSWORD ]]; then export ANSIBLE_BECOME_PASSWORD_LINE="ansible_become_password: $ANSIBLE_BECOME_PASSWORD"; fi


# Build inventory file for Ansible
envsubst < $DIR/hosts.yml.example > $DIR/hosts.yml


# Run playbook
ansible-playbook -i $DIR/hosts.yml $PLAYBOOK "${ANSIBLE_OPTS[@]}";
EXIT_CODE=$?;


# Deactivate venv
deactivate;

exit $EXIT_CODE;