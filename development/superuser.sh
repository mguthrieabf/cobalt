#!/usr/bin/expect

set timeout -1

spawn python manage.py createsuperuser

expect "Username:"
send -- "admin\r"
expect "ABF Number:"
send -- "99\r"
# expect "Mobile Number:"
# send -- "0404040404\r"
expect "Email:"
send -- "a@b.com\r"
expect "Password:"
send "F1shcake\r"
expect "Password (again):"
send "F1shcake\r"
expect "Superuser created "
