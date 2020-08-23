#!/bin/sh

# crontab: * * * * * /var/app/current/support/julian.sh

date > /tmp/lastcheck.log
FILE=/tmp/trigger.txt
if test -f "$FILE"; then

rm $FILE

# set env
`cat /opt/elasticbeanstalk/deployment/env | awk '{print "export",$1}'`

. /var/app/venv/staging-LQM1lest/bin/activate
cd /var/app/current
support/rebuild_test_data.sh >> /tmp/rebuild.log 2>&1
fi
