import mysql.connector
import os
from mysql.connector import Error
from datetime import datetime

def crear_conexion():
    try:
        connection = mysql.connector.connect(
            host=os.getenv('MYSQLHOST', 'localhost'),
            user=os.getenv('MYSQLUSER', 'root'),
            password=os.getenv('MYSQLPASSWORD', ''),
            database=os.getenv('MYSQLDATABASE', 'railway'),
            port=int(os.getenv('MYSQLPORT', 3306))
        )
        return connection
    except Error as e:
        print(f"Error al conectar a MySQL: {e}")
        return None

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

def buscar_libros(termino):
    conn = crear_conexion()
    lista = []
    if conn and conn.is_connected():
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM libros WHERE titulo LIKE %s OR autor LIKE %s"
        param = f"%{termino}%"
        cursor.execute(query, (param, param))
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

def agregar_libro(titulo, autor, descripcion, imagen_url):
    conn = crear_conexion()
    if conn and conn.is_connected():
        try:
            cursor = conn.cursor()
            query = "INSERT INTO libros (titulo, autor, descripcion, imagen_url, disponible) VALUES (%s, %s, %s, %s, 1)"
            cursor.execute(query, (titulo, autor, descripcion, imagen_url))
            conn.commit()
            return True
        except Error as e:
            print(f"Error agregando libro: {e}")
        finally:
            cursor.close()
            conn.close()
    return False

def prestar_libro(id_libro, id_usuario):
    conn = crear_conexion()
    exito = False
    if conn and conn.is_connected():
        try:
            cursor = conn.cursor()
            query_update = "UPDATE libros SET disponible = 0 WHERE id = %s AND disponible = 1"
            cursor.execute(query_update, (id_libro,))
            if cursor.rowcount == 0:
                print("El libro no está disponible.")
                return False
            query_insert = "INSERT INTO prestamos (usuario_id, libro_id) VALUES (%s, %s)"
            cursor.execute(query_insert, (id_usuario, id_libro))
            conn.commit()
            exito = True
        except Error as e:
            conn.rollback()
            print(f"Error prestando libro: {e}")
        finally:
            cursor.close()
            conn.close()
    return exito

def devolver_libro(id_libro, id_usuario):
    conn = crear_conexion()
    exito = False
    if conn and conn.is_connected():
        try:
            cursor = conn.cursor()
            query_libro = "UPDATE libros SET disponible = 1 WHERE id = %s"
            cursor.execute(query_libro, (id_libro,))
            query_prestamo = """
                UPDATE prestamos 
                SET fecha_devolucion = NOW() 
                WHERE libro_id = %s AND usuario_id = %s AND fecha_devolucion IS NULL
            """
            cursor.execute(query_prestamo, (id_libro, id_usuario))
            conn.commit()
            exito = True
        except Error as e:
            conn.rollback()
            print(f"Error devolviendo libro: {e}")
        finally:
            cursor.close()
            conn.close()
    return exito

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
    conn = crear_conexion()
    usuario = None
    if conn and conn.is_connected():
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM usuarios WHERE email = %s AND password = %s"
        cursor.execute(query, (email, password))
        usuario = cursor.fetchone()
        cursor.close()
        conn.close()
    return usuario