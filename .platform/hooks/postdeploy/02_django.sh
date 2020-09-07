#!/bin/bash

# commands to run after each deployment
# These MUST be re-runnable (not fail or create duplicates if run again)

. /var/app/venv/staging-LQM1lest/bin/activate

./manage.py migrate
./manage.py collectstatic --noinput
./manage.py createsu
./manage.py create_abf
./manage.py add_rbac_static_forums
./manage.py add_rbac_static_payments
./manage.py add_rbac_static_orgs
./manage.py add_rbac_static_events
./manage.py create_states
#./manage.py add_test_data
#./manage.py createdummyusers
#./manage.py importclubs
