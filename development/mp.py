#import pypyodbc
# conn = pypyodbc.connect('Driver={SQL Server};'
#                       'Server=202.146.210.45,2433;'
#                       'Database=abfmpc_db;'
#                       'uid=abfmpc_db;;pwd=Br1dge1440;'
# )

#conn = pypyodbc.connect("DRIVER={SQL Server};SERVER=202.146.210.45,2433;UID=abfmpc_website;PWD=Br1dge1440;DATABASE=abfmpc_db")
# conn = pypyodbc.connect("DRIVER={SQL Server};SERVER=202.146.210.45;UID=abfmpc_website;PWD=Br1dge1440;DATABASE=abfmpc_db")

import pypyodbc

details = {
 'server' : '202.146.210.45',
 'database' : 'abfmpc_db',
 'username' : 'abfmpc_website',
 'password' : 'Br1dge1440'
 }

#connect_string = 'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};PORT=2443; DATABASE={database};UID={username};PWD={password})'.format(**details)
connect_string = 'DRIVER={{SQL Server}};SERVER={server};PORT=2443; DATABASE={database};UID={username};PWD={password})'.format(**details)

connect_string="DRIVER={SQL Server};SERVER=202.146.210.45;PORT=2443;UID=abfmpc_website;PWD=Br1dge1440;DATABASE=abfmpc_db"

connection = pypyodbc.connect(connect_string)
print(connection)

# import adodbapi

#conn = adodbapi.connect("PROVIDER=SQLOLEDB;Data Source={0};Database={1}; \
#       trusted_connection=yes;UID={2};PWD={3};".format("202.146.210.45,2433;","abfmpc_db;","abfmpc_db;","Br1dge1440;"s))

# conn = adodbapi.connect("PROVIDER=SQLOLEDB;Data Source=202.146.210.45,2433;Database=abfmpc_db;trusted_connection=yes;UID=abfmpc_website;PWD=Br1dge1440;")
#
# import pytds
# with pytds.connect('202.146.210.45,2433', 'abfmpc_db', 'abfmpc_website', 'Br1dge1440') as conn:
#     with conn.cursor() as cur:
#         cur.execute("select 1")
#         cur.fetchall()
# #cursor = conn.cursor()

# import pyodbc
#
#
# server = 'tcp:202.146.210.45,2433'
# database = 'abfmpc_db'
# username = 'abfmpc_website'
# password = 'Br1dge1440'


# connect_string = 'DRIVER={{ODBC Driver}};SERVER={server};PORT=2443; DATABASE={database};UID={username};PWD={password})'.format(**details)
#
# connection = pyodbc.connect(connect_string)
# print(connection)

# import pyodbc
# server = 'tcp:myserver.database.windows.net'
# database = 'mydb'
# username = 'myusername'
# password = 'mypassword'

#Connection String
# cnxn = pyodbc.connect('DRIVER={ODBC Driver 13 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
# cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
# cursor = cnxn.cursor()
