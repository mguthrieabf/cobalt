#!/bin/sh
mssql-cli -S "tcp:IP,PORT" -d DB -U USER -P PWD -i mp_detail.sql --mssqlclirc mssqlclirc.cfg -o MPDataDetails.tsv
