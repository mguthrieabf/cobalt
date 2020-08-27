#!/bin/bash

cat /opt/elasticbeanstalk/deployment/env >> /tmp/migrate 2>&1

. /var/app/venv/staging-LQM1lest/bin/activate
python manage.py migrate >> /tmp/migrate 2>&1 
