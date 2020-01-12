#!/bin/sh
mssql-cli -S "tcp:202.146.210.45,2433" -d abfmpc_db -U abfmpc_website -P Br1dge1440 -i mp_detail.sql --mssqlclirc mssqlclirc.cfg -o MPDataDetails.tsv
