import mysql.connector

config = {
    'host': 'mysql.railway.internal',     
    'user': 'root',      
    'password': 'hiOlGXJZEDkyQKWcrxzISOsRaXGcBpho', 
    'database': 'railway', 
    'port': 3306                               
}

try:
    # 1. Conectamos
    print("Conectando a la nube...")
    conexion = mysql.connector.connect(**config)
    cursor = conexion.cursor()

    # 2. El código SQL para crear la tabla
    sql = """
    CREATE TABLE IF NOT EXISTS mensajes (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nombre VARCHAR(100) NOT NULL,
        email VARCHAR(100) NOT NULL,
        mensaje TEXT NOT NULL,
        fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    cursor.execute(sql)
    print("tabla creada")

    cursor.execute("INSERT INTO mensajes (nombre, email, mensaje) VALUES ('Admin', 'test@railway.app', 'Base de datos conectada OK')")
    conexion.commit()
    print("Mensaje de prueba insertado.")

except Exception as e:
    print(f"Error: {e}")

finally:
    if 'conexion' in locals() and conexion.is_connected():
        cursor.close()
        conexion.close()