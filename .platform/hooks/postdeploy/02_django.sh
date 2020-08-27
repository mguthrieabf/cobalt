#!/bin/bash

. /var/app/venv/staging-LQM1lest/bin/activate
python manage.py migrate >> /tmp/migrate 2>&1 
