"""
Módulo para gestionar la obtención de permisos de usuario desde la base de datos NotFC.
Este módulo reemplaza los datos hardcodeados en mis-permisos.js
"""

import mysql.connector
from mysql.connector import Error
from bdd.conexionBDD import get_connection as obtener_conexion

def obtener_permisos_usuario(user_id):
    """
    Obtiene todos los permisos de un usuario específico desde las tablas userdoorpermit y roledoorpermit.
    
    Args:
        user_id (int): ID del usuario desde la tabla User
        
    Returns:
        list: Lista de permisos con detalles de puertas
    """
    conexion = obtener_conexion()
    if not conexion:
        return []
    
    try:
        cursor = conexion.cursor(dictionary=True)
        
        # Query para obtener permisos directos del usuario (userdoorpermit)
        query_directos = """
        SELECT DISTINCT
            d.ID_door as doorId,
            d.door_name as doorName,
            'permanent' as accessType,
            NULL as expirationDate,
            'Direct' as grantedBy
        FROM userdoorpermit udp
        JOIN Door d ON udp.ID_door = d.ID_door
        WHERE udp.ID_user = %s
        """
        
        # Query para obtener permisos a través del rol del usuario (roledoorpermit)
        query_roles = """
        SELECT DISTINCT
            d.ID_door as doorId,
            d.door_name as doorName,
            'permanent' as accessType,
            NULL as expirationDate,
            'Role' as grantedBy
        FROM UserAtributes ua
        JOIN roledoorpermit rdp ON ua.ID_role = rdp.ID_role
        JOIN Door d ON rdp.ID_door = d.ID_door
        WHERE ua.ID_user = %s
        """
        
        # Combinar ambos resultados
        cursor.execute(query_directos, (user_id,))
        permisos_directos = cursor.fetchall()
        
        cursor.execute(query_roles, (user_id,))
        permisos_roles = cursor.fetchall()
        
        # Combinar y eliminar duplicados
        todos_permisos = permisos_directos + permisos_roles
        
        # Eliminar duplicados basados en doorId
        permisos_unicos = {}
        for permiso in todos_permisos:
            door_id = permiso['doorId']
            if door_id not in permisos_unicos:
                permisos_unicos[door_id] = permiso
        
        return list(permisos_unicos.values())
        
    except Error as e:
        print(f"Error al obtener permisos: {e}")
        return []
    finally:
        if conexion and conexion.is_connected():
            cursor.close()
            conexion.close()

def obtener_todas_las_puertas():
    """
    Obtiene todas las puertas disponibles en el sistema.
    
    Returns:
        list: Lista de puertas con id y nombre
    """
    conexion = obtener_conexion()
    if not conexion:
        return []
    
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT ID_door as id, door_name as name FROM Door WHERE 1")
        puertas = cursor.fetchall()
        
        return [{'id': str(p['id']), 'name': p['name']} for p in puertas]
        
    except Error as e:
        print(f"Error al obtener puertas: {e}")
        return []
    finally:
        if conexion and conexion.is_connected():
            cursor.close()
            conexion.close()

def obtener_usuario_por_dni_o_username(identifier):
    """
    Obtiene información básica de un usuario por su DNI o username.
    
    Args:
        identifier (str): DNI o username del usuario
        
    Returns:
        dict: Información del usuario o None si no existe
    """
    conexion = obtener_conexion()
    if not conexion:
        return None
    
    try:
        cursor = conexion.cursor(dictionary=True)
        
        # Buscar por DNI
        cursor.execute("""
            SELECT u.ID_user as id, ua.name, ua.surname, u.username, ua.dni
            FROM User u
            JOIN UserAtributes ua ON u.ID_user = ua.ID_user
            WHERE ua.dni = %s
        """, (identifier,))
        
        usuario = cursor.fetchone()
        
        if not usuario:
            # Buscar por username
            cursor.execute("""
                SELECT u.ID_user as id, ua.name, ua.surname, u.username, ua.dni
                FROM User u
                JOIN UserAtributes ua ON u.ID_user = ua.ID_user
                WHERE u.username = %s
            """, (identifier,))
            usuario = cursor.fetchone()
        
        return usuario
        
    except Error as e:
        print(f"Error al obtener usuario: {e}")
        return None
    finally:
        if conexion and conexion.is_connected():
            cursor.close()
            conexion.close()

def obtener_usuario_actual_por_username(username):
    """
    Obtiene el ID del usuario actual basado en el username de la sesión.
    
    Args:
        username (str): Username del usuario logueado
        
    Returns:
        int: ID del usuario o None si no existe
    """
    conexion = obtener_conexion()
    if not conexion:
        return None
    
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT ID_user FROM User WHERE username = %s", (username,))
        resultado = cursor.fetchone()
        
        return resultado['ID_user'] if resultado else None
        
    except Error as e:
        print(f"Error al obtener ID de usuario: {e}")
        return None
    finally:
        if conexion and conexion.is_connected():
            cursor.close()
            conexion.close()
