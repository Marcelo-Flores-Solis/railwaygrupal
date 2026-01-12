import mysql.connector

import os

from mysql.connector import Error



def crear_conexion():

    """Conecta a la base de datos (Local o Railway)"""

    try:

        connection = mysql.connector.connect(

            # Railway nos da estas variables automáticamente

            host=os.getenv('MYSQLHOST', 'localhost'),

            user=os.getenv('MYSQLUSER', 'root'),

            password=os.getenv('MYSQLPASSWORD', ''),

            database=os.getenv('MYSQLDATABASE', 'biblioteca'),

            port=os.getenv('MYSQLPORT', 3306)

        )

        return connection

    except Error as e:

        print(f"Error al conectar a MySQL: {e}")

        return None



# --- LIBROS ---

def obtener_todos_los_libros():

    conn = crear_conexion()

    lista = []

    if conn and conn.is_connected():

        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM libros")

        lista = cursor.fetchall()

        cursor.close()

        conn.close()

    return lista



def obtener_libro_por_id(id_libro):

    conn = crear_conexion()

    libro = None

    if conn and conn.is_connected():

        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM libros WHERE id = %s", (id_libro,))

        libro = cursor.fetchone()

        cursor.close()

        conn.close()

    return libro



def prestar_libro(id_libro):

    """Cambia el estado del libro a NO DISPONIBLE (0)"""

    conn = crear_conexion()

    exito = False

    if conn and conn.is_connected():

        try:

            cursor = conn.cursor()

            query = "UPDATE libros SET disponible = 0 WHERE id = %s"

            cursor.execute(query, (id_libro,))

            conn.commit()

            exito = True

        except Error as e:

            print(f"Error prestando libro: {e}")

        finally:

            cursor.close()

            conn.close()

    return exito



# --- USUARIOS ---

def guardar_usuario(nombre, email, password):

    conn = crear_conexion()

    if conn and conn.is_connected():

        try:

            cursor = conn.cursor()

            query = "INSERT INTO usuarios (nombre, email, password) VALUES (%s, %s, %s)"

            cursor.execute(query, (nombre, email, password))

            conn.commit()

            cursor.close()

            conn.close()

            return True

        except Error as e:

            print(f"Error al guardar usuario: {e}")

            return False

    return False



def verificar_usuario(email, password):

    """Busca si el email y contraseña coinciden"""

    conn = crear_conexion()

    usuario = None

    if conn and conn.is_connected():

        cursor = conn.cursor(dictionary=True)

        # NOTA: En un proyecto real, la contraseña debería estar encriptada.

        query = "SELECT * FROM usuarios WHERE email = %s AND password = %s"

        cursor.execute(query, (email, password))

        usuario = cursor.fetchone()

        cursor.close()

        conn.close()

    return usuario