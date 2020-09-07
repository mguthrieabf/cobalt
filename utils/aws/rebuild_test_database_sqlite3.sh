#!/bin/sh

# set env
`cat /opt/elasticbeanstalk/deployment/env | awk '{print "export",$1}'`

# active virtualenv
. /var/app/venv/staging-LQM1lest/bin/activate

# change into app dir
cd /var/app/current

# Delete database
rm db.sqlite3

# include scripts
/var/app/current/utils/aws/rebuild_test_database_subcommands.sh

# Change permissions
chmod 777 db.sqlite3
