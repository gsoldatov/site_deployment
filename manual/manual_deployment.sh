# A set of shell commands for deployment on a single server with Nginx as frontend server & backend reverse proxy.
# Listed commands are meant to be executed manually and in order of being listed via CLI on local & production machines (see NOTE comments).
# Required environment variables for local & production machines are listed in production.env.example.

############################# General #############################
# NOTE: run on production server
# Create site user
useradd -r -s /sbin/nologin $SITE_USER;

############################# Frontend #############################
# Install NodeJS
curl -O  https://nodejs.org/dist/$NODE_VERSION/node-$NODE_VERSION-$NODE_DISTRO.tar.xz;
mkdir -p /usr/local/lib/nodejs;
tar -xJvf node-$NODE_VERSION-$NODE_DISTRO.tar.xz -C /usr/local/lib/nodejs;

# Create symlinks for Node executables
ln -s /usr/local/lib/nodejs/node-$NODE_VERSION-$NODE_DISTRO/bin/node /usr/bin/node;
ln -s /usr/local/lib/nodejs/node-$NODE_VERSION-$NODE_DISTRO/bin/npm /usr/bin/npm;
ln -s /usr/local/lib/nodejs/node-$NODE_VERSION-$NODE_DISTRO/bin/npx /usr/bin/npx;

# Clone frontend repo
mkdir -p $SERVER_FRONTEND_FOLDER;
cd $SERVER_FRONTEND_FOLDER;
git clone https://github.com/gsoldatov/site_frontend.git .;
# git checkout master;  # clone checks out by default

# Install dependencies
npm install;

# Build and copy production config
# NOTE: run on local machine
envsubst <$LOCAL_SITE_FOLDER/deployment/manual/templates/frontend-config.json > $LOCAL_SITE_FOLDER/deployment/manual/build/frontend-config.json;
scp $LOCAL_SITE_FOLDER/deployment/manual/build/frontend-config.json $SERVER_USER@$SERVER_ADDR:$SERVER_FRONTEND_FOLDER/src;

# NOTE: run on production server
mv -f $SERVER_FRONTEND_FOLDER/src/frontend-config.json $SERVER_FRONTEND_FOLDER/src/config.json;

# Build frontend
npm run build;

# Set ownership & permissions
chown -R root:$SITE_USER $SERVER_FRONTEND_FOLDER;
chmod -R 774 $SERVER_FRONTEND_FOLDER;

############################# Backend #############################
# Python & dependencies
# NOTE: run on production server
apt update;
apt install -y python$PYTHON_VERSION python$PYTHON_VERSION-venv;

# Install & configure Postgresql
apt install -y postgresql-14;

# # ----------- 
# # Alter default role/linux user (not finished)
# # see https://stackoverflow.com/a/66782641 for SQL commands;
# # also requires renaming linux user "postgres" and updating it in pg_hba.conf (and, potentially, other files);
# # default database should also be renamed for full support of non-default postgres names
# TMP_USER=temp;
# TMP_PWD=password;
# sudo -u postgres psql -c "CREATE ROLE $TMP_USER LOGIN SUPERUSER PASSWORD '$TMP_PWD'";
# sudo -u postgres psql -c "ALTER USER $BACKEND_SETTING_DB_INIT_USERNAME PASSWORD '$BACKEND_SETTING_DB_INIT_PASSWORD';"    # default password only
# # -----------
cd /etc/postgresql;   # Update default superuser's password only (change directory which can be accessed by 'postgres' user to avoid permission deny)
sudo -u postgres psql -c "ALTER USER postgres PASSWORD '$BACKEND_SETTING_DB_INIT_PASSWORD';";

# # NOTE: run on production server via psql
# sudo -u $BACKEND_SETTING_DB_INIT_USERNAME psql;   # manual change of default password
# \password postgres

# Clone backend repo
# NOTE: run on production server
mkdir -p $SERVER_BACKEND_FOLDER;
cd $SERVER_BACKEND_FOLDER;
git clone https://github.com/gsoldatov/site_backend.git .;

# Init venv & install dependencies
python3 -m venv venv --prompt="Backend";
source venv/bin/activate;
pip install -r requirements.txt;

# Build and copy production config
# NOTE: run on local machine
envsubst <$LOCAL_SITE_FOLDER/deployment/manual/templates/backend-config.json > $LOCAL_SITE_FOLDER/deployment/manual/build/backend-config.json;
scp $LOCAL_SITE_FOLDER/deployment/manual/build/backend-config.json $SERVER_USER@$SERVER_ADDR:$SERVER_BACKEND_FOLDER/backend_main;

# NOTE: run on production server
mv -f $SERVER_BACKEND_FOLDER/backend_main/backend-config.json $SERVER_BACKEND_FOLDER/backend_main/config.json;

# Set ownership & permissions
chown -R root:$SITE_USER $SERVER_BACKEND_FOLDER;
chmod -R 774 $SERVER_BACKEND_FOLDER;

# Apply database migrations
python -m backend_main.db;

# Copy systemd backend unit configuration
# NOTE: run on local machine
envsubst <$LOCAL_SITE_FOLDER/deployment/manual/templates/site_backend.service > $LOCAL_SITE_FOLDER/deployment/manual/build/site_backend.service;
scp $LOCAL_SITE_FOLDER/deployment/manual/build/site_backend.service $SERVER_USER@$SERVER_ADDR:/etc/systemd/system;

# Reload systemd & start service
# NOTE: run on production server
systemctl daemon-reload;
systemctl start site_backend;
systemctl enable site_backend;

############################# Database scheduled jobs #############################
# Generate and copy crontab for the site user
# NOTE: run on local machine
envsubst <$LOCAL_SITE_FOLDER/deployment/manual/templates/crontab_site > $LOCAL_SITE_FOLDER/deployment/manual/build/crontab_site;
scp $LOCAL_SITE_FOLDER/deployment/manual/build/crontab_site $SERVER_USER@$SERVER_ADDR:$SERVER_BACKEND_FOLDER;

# NOTE: run on production server
cat $SERVER_BACKEND_FOLDER/crontab_site | crontab -u $SITE_USER -;
rm $SERVER_BACKEND_FOLDER/crontab_site;

############################# Nginx #############################
# Install
# NOTE: run on production server
apt install -y nginx;

# Build & copy production config files
# NOTE: run on local machine
envsubst <$LOCAL_SITE_FOLDER/deployment/manual/templates/nginx.conf | tail -n +7 | sed -e 's/§/$/g' > $LOCAL_SITE_FOLDER/deployment/manual/build/nginx.conf;    # Substitute environment variables -> remove starting comments -> substitute dollar signs
scp $LOCAL_SITE_FOLDER/deployment/manual/build/nginx.conf $SERVER_USER@$SERVER_ADDR:/etc/nginx;
scp $LOCAL_SITE_FOLDER/deployment/manual/immutable/nginx_forwarded_header $SERVER_USER@$SERVER_ADDR:/etc/nginx;

# HTTPS self-signed certificate & key
openssl req -x509 -noenc -newkey rsa:2048 -days 3650 -keyout $LOCAL_SITE_FOLDER/deployment/manual/build/site.key -out $LOCAL_SITE_FOLDER/deployment/manual/build/site.crt -subj "/";
scp $LOCAL_SITE_FOLDER/deployment/manual/build/site.crt $SERVER_USER@$SERVER_ADDR:/etc/ssl;
scp $LOCAL_SITE_FOLDER/deployment/manual/build/site.key $SERVER_USER@$SERVER_ADDR:/etc/ssl;

# NOTE: run on production server
systemctl reload nginx;

# Enable log rotation for Nginx (default is daily with 14 )
# NOTE: run on local machine
scp $LOCAL_SITE_FOLDER/deployment/manual/immutable/logrotate_nginx $SERVER_USER@$SERVER_ADDR:/etc/logrotate.d;

# NOTE: run on production server
mv -f /etc/logrotate.d/logrotate_nginx /etc/logrotate.d/nginx;

############################# UFW configuration #############################
# Build & copy site rules
# NOTE: run on local machine
envsubst <$LOCAL_SITE_FOLDER/deployment/manual/templates/ufw_site > $LOCAL_SITE_FOLDER/deployment/manual/build/ufw_site;
scp $LOCAL_SITE_FOLDER/deployment/manual/build/ufw_site $SERVER_USER@$SERVER_ADDR:/etc/ufw/applications.d;

# NOTE: run on production server
mv -f /etc/ufw/applications.d/ufw_site /etc/ufw/applications.d/site;

# Set rules & enable UFW
ufw allow "Site Frontend";
ufw allow "Site Backend";
ufw allow "OpenSSH";
ufw --force enable;
