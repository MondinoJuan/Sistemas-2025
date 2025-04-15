# Por ahora debes empezar creando un script llamado restaurante.py y dentro una función crear_bd() que creará una pequeña base de datos 
# restaurante.db con las siguientes dos tablas:
# CREATE TABLE categoria(
#    id INTEGER PRIMARY KEY AUTOINCREMENT,
#    nombre VARCHAR(100) UNIQUE NOT NULL)

# CREATE TABLE plato(
#    id INTEGER PRIMARY KEY AUTOINCREMENT,
#    nombre VARCHAR(100) UNIQUE NOT NULL, 
#    categoria_id INTEGER NOT NULL,
#    FOREIGN KEY(categoria_id) REFERENCES categoria(id))

# Si ya existen deberá tratar la excepción y mostrar que las tablas ya existen, lo notarás porque en este caso no usamos el 
# IF NOT EXISTS y eso lanzará un error. En caso contrario mostrará que se han creado correctamente.


import pymysql


def crear_db():
    conn = pymysql.connect( host="localhost", port=3306, user="root", passwd="0717", db="restaurante" )
    cursor = conn.cursor()
    try:
        cursor.execute("""CREATE TABLE categoria(
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(100) UNIQUE NOT NULL)""")
        print("Tabla categoria creada correctamente.")
    except pymysql.err.InternalError as e:
        print("La tabla categoria ya existe.")
        cursor.execute("SELECT * FROM categoria")
        rows = cursor.fetchall()
        for row in rows:
            print(row)

    try:
        cursor.execute("""CREATE TABLE plato(
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(100) UNIQUE NOT NULL, 
            categoria_id INT NOT NULL,
            FOREIGN KEY(categoria_id) REFERENCES categoria(id))""")
        print("Tabla plato creada correctamente.")
    except pymysql.err.InternalError as e:
        print("La tabla plato ya existe.")
        cursor.execute("SELECT * FROM plato")
        rows = cursor.fetchall()
        for row in rows:
            print(row)

    cursor.close()
    conn.close()



if __name__ == '__main__':
    crear_db()