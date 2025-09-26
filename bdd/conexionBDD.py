import mysql.connector
from mysql.connector import Error
import bdd.config as config

def get_connection():
    """
    Establece y retorna la conexion a la base de datos usando parametros desde config.py.
    """
    try:
        connection = mysql.connector.connect(
            host=config.DB_HOST,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME,
            port=config.DB_PORT
        )
        if connection.is_connected():
            print("Conexion a la base de datos exitosa")
            return connection
    except Error as e:
        print(f"Error intentando conectar a la base de datos: {e}")
        return None
