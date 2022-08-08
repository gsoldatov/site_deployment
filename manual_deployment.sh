# A set of shell commands for deployment on a single server with Nginx as frontend server & backend reverse proxy.
# Listed commands are meant to be executed manually and in order of being listed via CLI on local & production machines (see NOTE comments).
# Required environment variables are listed in production.env.example.

############################# General #############################
# NOTE: run on production server
# Create site user
useradd -r -s /sbin/nologin $SITE_USER;

############################# Frontend #############################
# Install NodeJS
curl -O  https://nodejs.org/dist/$NODE_VERSION/node-$NODE_VERSION-$NODE_DISTRO.tar.xz;
sudo mkdir -p /usr/local/lib/nodejs;
sudo tar -xJvf node-$NODE_VERSION-$NODE_DISTRO.tar.xz -C /usr/local/lib/nodejs;

# Create symlinks for Node executables
sudo ln -s /usr/local/lib/nodejs/node-$NODE_VERSION-$NODE_DISTRO/bin/node /usr/bin/node;
sudo ln -s /usr/local/lib/nodejs/node-$NODE_VERSION-$NODE_DISTRO/bin/npm /usr/bin/npm;
sudo ln -s /usr/local/lib/nodejs/node-$NODE_VERSION-$NODE_DISTRO/bin/npx /usr/bin/npx;

# Clone frontend repo
sudo mkdir -p $SERVER_FRONTEND_FOLDER;
cd $SERVER_FRONTEND_FOLDER;
git clone https://github.com/gsoldatov/site_frontend.git .;
# git checkout master;  # clone checks out by default

# Install dependencies
npm install;

# Build and copy production config
# NOTE: run on local machine
envsubst <$LOCAL_SITE_FOLDER/deployment/frontend-config.json > $LOCAL_SITE_FOLDER/deployment/build/frontend-config.json;
scp $LOCAL_SITE_FOLDER/deployment/build/frontend-config.json $SERVER_USER@$SERVER_ADDR:$SERVER_FRONTEND_FOLDER/src;

# NOTE: run on production server
sudo mv -f $SERVER_FRONTEND_FOLDER/src/frontend-config.json $SERVER_FRONTEND_FOLDER/src/config.json;

# Build frontend
sudo npm run build;

# Set ownership & permissions
sudo chown -R root:$SITE_USER $SERVER_FRONTEND_FOLDER;
sudo chmod -R 775 $SERVER_FRONTEND_FOLDER;

############################# Backend #############################
# Python & dependencies
# NOTE: run on production server
sudo apt update;
sudo apt install python$PYTHON_VERSION python$PYTHON_VERSION-venv;

# Install & configure Postgresql
sudo apt install postgresql-14;

# NOTE: run on production server via psql
sudo -u $BACKEND_SETTING_DB_INIT_USERNAME psql;
\password postgres

# Clone backend repo
# NOTE: run on production server
sudo mkdir -p $SERVER_BACKEND_FOLDER;
cd $SERVER_BACKEND_FOLDER;
git clone https://github.com/gsoldatov/site_backend.git .;

# Init venv & install dependencies
python3 -m venv venv --prompt="Backend";
source venv/bin/activate;
pip install -r requirements.txt;

# Build and copy production config
# NOTE: run on local machine
envsubst <$LOCAL_SITE_FOLDER/deployment/backend-config.json > $LOCAL_SITE_FOLDER/deployment/build/backend-config.json;
scp $LOCAL_SITE_FOLDER/deployment/build/backend-config.json $SERVER_USER@$SERVER_ADDR:$SERVER_BACKEND_FOLDER/backend_main;

# NOTE: run on production server
sudo mv -f $SERVER_BACKEND_FOLDER/backend_main/backend-config.json $SERVER_BACKEND_FOLDER/backend_main/config.json;

# Set ownership & permissions
sudo chown -R root:$SITE_USER $SERVER_BACKEND_FOLDER;
sudo chmod -R 775 $SERVER_BACKEND_FOLDER;

# Apply database migrations
python -m backend_main.db;

# Copy systemd backend unit configuration
# NOTE: run on local machine
envsubst <$LOCAL_SITE_FOLDER/deployment/site_backend.service > $LOCAL_SITE_FOLDER/deployment/build/site_backend.service;
scp $LOCAL_SITE_FOLDER/deployment/build/site_backend.service $SERVER_USER@$SERVER_ADDR:/etc/systemd/system;

# Reload systemd & start service
# NOTE: run on production server
sudo systemctl daemon-reload;
sudo systemctl start site_backend;
sudo systemctl enable site_backend;

############################# Nginx #############################
# Install
# NOTE: run on production server
sudo apt install nginx;

# Build & copy production config files
# NOTE: run on local machine
envsubst <$LOCAL_SITE_FOLDER/deployment/nginx.conf | tail -n +7 | sed -e 's/§/$/g' > $LOCAL_SITE_FOLDER/deployment/build/nginx.conf;    # Substitute environment variables -> remove starting comments -> substitute dollar signs
scp $LOCAL_SITE_FOLDER/deployment/build/nginx.conf $SERVER_USER@$SERVER_ADDR:/etc/nginx;
scp $LOCAL_SITE_FOLDER/deployment/nginx_forwarded_header $SERVER_USER@$SERVER_ADDR:/etc/nginx;

# HTTPS self-signed certificate & key
openssl req -x509 -noenc -newkey rsa:2048 -days 3650 -keyout $LOCAL_SITE_FOLDER/deployment/build/site.key -out $LOCAL_SITE_FOLDER/deployment/build/site.crt;
scp $LOCAL_SITE_FOLDER/deployment/build/site.crt $SERVER_USER@$SERVER_ADDR:/etc/ssl;
scp $LOCAL_SITE_FOLDER/deployment/build/site.key $SERVER_USER@$SERVER_ADDR:/etc/ssl;

# NOTE: run on production server
sudo systemctl reload nginx;

# Enable log rotation for Nginx (default is daily with 14 )
# NOTE: run on local machine
scp $LOCAL_SITE_FOLDER/deployment/logrotate_nginx $SERVER_USER@$SERVER_ADDR:/etc/logrotate.d;

# NOTE: run on production server
sudo mv -f /etc/logrotate.d/logrotate_nginx /etc/logrotate.d/nginx;

############################# Database scheduled jobs #############################
# Generate and copy crontab for the site user
# NOTE: run on local machine
envsubst <$LOCAL_SITE_FOLDER/deployment/crontab_site > $LOCAL_SITE_FOLDER/deployment/build/crontab_site;
scp $LOCAL_SITE_FOLDER/deployment/build/crontab_site $SERVER_USER@$SERVER_ADDR:$SERVER_BACKEND_FOLDER;

# NOTE: run on production server
# sudo mv -f /var/spool/cron/crontabs/crontab_site /var/spool/cron/crontabs/$SITE_USER;
sudo cat $SERVER_BACKEND_FOLDER/crontab_site | crontab -u $SITE_USER -;
sudo rm $SERVER_BACKEND_FOLDER/crontab_site;

