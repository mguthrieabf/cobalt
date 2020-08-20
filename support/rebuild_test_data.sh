#!/bin/sh

./manage.py dbshell <support/rebuild_test_data.sql
./manage.py migrate
./manage.py createsu
./manage.py create_abf
./manage.py add_rbac_static_forums
./manage.py add_rbac_static_payments
./manage.py add_rbac_static_orgs
./manage.py add_rbac_static_events
./manage.py add_rbac_test_data
./manage.py create_states
#./manage.py createdummyusers
./manage.py importclubs
