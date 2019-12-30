find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc"  -delete
rm db.sqlite3

python manage.py makemigrations
python manage.py makemigrations payments
python manage.py migrate
./development/superuser.sh

cp development/add_static.py .
python add_static.py
rm add_static.py

# hack for now
cp development/masterpoint_import.py .
python masterpoint_import.py
rm masterpoint_import.py
