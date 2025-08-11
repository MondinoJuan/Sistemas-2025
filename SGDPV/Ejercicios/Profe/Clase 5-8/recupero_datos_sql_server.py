import pyodbc
conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost\SQLEXPRESS;DATABASE=WideWorldImportersDW;Trusted_Connection=yes;')
##conn = pyodbc.connect('DRIVER={SQL Server};SERVER=<tu_servidor>;DATABASE=<tu_bd>;UID=<tu_usuario>;PWD=<tu_contraseña>')
cursor = conn.cursor()
# Ahora puedes ejecutar consultas, por ejemplo:
cursor.execute("SELECT * FROM WideWorldImportersDW.Fact.Purchase")
for row in cursor:
    print(row)