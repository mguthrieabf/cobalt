#!/bin/sh

# crontab: * * * * * /var/app/current/support/julian.sh

FILE=/tmp/trigger.txt
if test -f "$FILE"; then

rm $FILE

/var/app/current/support/rebuild_test_data_postgres.sh

fi
