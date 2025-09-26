import mysql.connector
from mysql.connector import Error
from datetime import datetime
from bdd.conexionBDD import get_connection

def obtener_todas_puertas():
    """Obtener todas las puertas ordenadas por fecha de creación descendente"""
    conexion = get_connection()
    puertas = []
    
    if conexion:
        try:
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("""
                SELECT 
                    d.ID_door as id, 
                    d.door_name as nombre, 
                    d.door_isOpen as estado, 
                    d.creation_time as fecha_creacion, 
                    d.door_img as imagen,
                    (
                        SELECT COUNT(DISTINCT ua.ID_user)
                        FROM UserAtributes ua
                        INNER JOIN User u ON ua.ID_user = u.ID_user
                        WHERE u.user_status = TRUE
                        AND ua.nfc_code IS NOT NULL 
                        AND ua.nfc_code != ''
                        AND (
                            ua.ID_role IN (
                                SELECT rdp.ID_role 
                                FROM RoleDoorPermit rdp 
                                WHERE rdp.ID_door = d.ID_door
                            )
                            OR ua.ID_user IN (
                                SELECT udp.ID_user 
                                FROM userdoorpermit udp 
                                WHERE udp.ID_door = d.ID_door
                            )
                        )
                    ) as usuarios
                FROM Door d
                ORDER BY d.creation_time DESC
            """)
            puertas = cursor.fetchall()
            
            # Convertir booleano a string para compatibilidad
            for puerta in puertas:
                puerta['estado'] = 'activa' if puerta['estado'] else 'inactiva'
                # Asegurar que usuarios sea un entero
                puerta['usuarios'] = int(puerta['usuarios']) if puerta['usuarios'] is not None else 0
                
        except Error as e:
            print(f"Error al obtener puertas: {e}")
        finally:
            if conexion.is_connected():
                cursor.close()
                conexion.close()
    
    return puertas

def obtener_puerta_por_id(id_puerta):
    """Obtener una puerta específica por ID"""
    conexion = get_connection()
    puerta = None
    
    if conexion:
        try:
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("""
                SELECT ID_door as id, door_name as nombre, door_isOpen as estado, creation_time as fecha_creacion, door_img as imagen 
                FROM Door 
                WHERE ID_door = %s
            """, (id_puerta,))
            puerta = cursor.fetchone()
            
            if puerta:
                puerta['estado'] = 'activa' if puerta['estado'] else 'inactiva'
                
        except Error as e:
            print(f"Error al obtener puerta por ID: {e}")
        finally:
            if conexion.is_connected():
                cursor.close()
                conexion.close()
    
    return puerta

def crear_puerta(nombre, estado='inactiva', imagen=None):
    """
    Crea una nueva puerta en la base de datos
    
    Args:
        nombre (str): Nombre de la puerta
        estado (str): Estado de la puerta ('activa' o 'inactiva')
        imagen (str, optional): Nombre del archivo de imagen de la puerta
        
    Returns:
        int: ID de la puerta creada o None en caso de error
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        if not conn or not conn.is_connected():
            print("Error: No se pudo conectar a la base de datos")
            return None
            
        # Usar un cursor regular para las operaciones de inserción
        cursor = conn.cursor()
        
        # Insertar la nueva puerta con door_isOpen=0 por defecto
        query = """
        INSERT INTO Door (door_name, door_isOpen, door_img, creation_time)
        VALUES (%s, %s, %s, NOW())
        """
        # Convertir el estado a booleano (0 para inactiva, 1 para activa)
        is_open = 1 if estado == 'activa' else 0
        cursor.execute(query, (nombre, is_open, imagen))
        puerta_id = cursor.lastrowid
        
        # Cerrar el cursor actual
        cursor.close()
        
        # Crear un nuevo cursor con dictionary=True para la consulta de roles
        cursor = conn.cursor(dictionary=True)
        
        # Obtener roles que tienen acceso a todas las puertas existentes
        # Estos son roles que tienen acceso a todas las puertas excepto la que acabamos de crear
        query_roles = """
        SELECT r.ID_role 
        FROM Role r
        WHERE NOT EXISTS (
            SELECT d.ID_door 
            FROM Door d
            WHERE d.ID_door != %s
            AND NOT EXISTS (
                SELECT 1 
                FROM RoleDoorPermit rdp 
                WHERE rdp.ID_role = r.ID_role 
                AND rdp.ID_door = d.ID_door
            )
        )
        """
        cursor.execute(query_roles, (puerta_id,))
        roles_acceso_total = cursor.fetchall()
        
        # Cerrar el cursor de diccionario
        cursor.close()
        
        # Otorgar acceso a la nueva puerta para cada rol con acceso total
        if roles_acceso_total:
            # Usar un cursor regular para las inserciones
            cursor = conn.cursor()
            query_permiso = """
            INSERT IGNORE INTO RoleDoorPermit (ID_role, ID_door)
            VALUES (%s, %s)
            """
            for rol in roles_acceso_total:
                cursor.execute(query_permiso, (rol['ID_role'], puerta_id))

        # Asegurar explícitamente que el rol master (ID=3) tenga acceso a la nueva puerta
        try:
            if cursor is None or not conn.is_connected():
                cursor = conn.cursor()
            cursor.execute(
                """
                INSERT IGNORE INTO RoleDoorPermit (ID_role, ID_door)
                VALUES (%s, %s)
                """,
                (3, puerta_id)
            )
        except Error as e:
            # Loguear pero no fallar la creación de la puerta por esto
            print(f"Advertencia: no se pudo asignar permiso master a la puerta {puerta_id}: {e}")
        
        # Confirmar la transacción
        conn.commit()
        print(f"Puerta '{nombre}' creada exitosamente con ID: {puerta_id}")
        return puerta_id
        
    except Error as e:
        print(f"Error al crear la puerta: {e}")
        if conn and conn.is_connected():
            conn.rollback()
        return None
        
    finally:
        # Cerrar el cursor y la conexión
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

def actualizar_puerta(id_puerta, nombre, estado=None, imagen=None):
    """
    Actualiza una puerta existente
    
    Args:
        id_puerta (int): ID de la puerta a actualizar
        nombre (str): Nuevo nombre para la puerta
        estado (str, optional): Estado de la puerta ('activa' o 'inactiva')
        imagen (str, optional): Nombre del archivo de imagen de la puerta
        
    Returns:
        bool: True si la actualización fue exitosa, False en caso contrario
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        if not conn or not conn.is_connected():
            print("Error: No se pudo conectar a la base de datos")
            return False
            
        cursor = conn.cursor()
        
        # Construir la consulta dinámicamente basada en los parámetros proporcionados
        update_fields = []
        params = []
        
        if nombre is not None:
            update_fields.append("door_name = %s")
            params.append(nombre)
            
        if estado is not None:
            update_fields.append("door_isOpen = %s")
            params.append(estado == 'activa')
            
        if imagen is not None:
            update_fields.append("door_img = %s")
            params.append(imagen)
            
        # Agregar el ID al final para la cláusula WHERE
        params.append(id_puerta)
        
        if not update_fields:
            return False  # No hay nada que actualizar
            
        update_query = f"""
        UPDATE Door 
        SET {', '.join(update_fields)}
        WHERE ID_door = %s
        """
        
        cursor.execute(update_query, tuple(params))
        conn.commit()
        return cursor.rowcount > 0
        
    except Error as e:
        print(f"Error al actualizar la puerta: {e}")
        if conn and conn.is_connected():
            conn.rollback()
        return False
        
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

def eliminar_puerta(id_puerta):
    """Eliminar puerta por ID"""
    conexion = get_connection()
    resultado = False
    
    if conexion:
        try:
            cursor = conexion.cursor(dictionary=True)
            
            # Primero eliminamos registros relacionados en activity
            cursor.execute("DELETE FROM activity WHERE ID_door = %s", (id_puerta,))
            print(f"Eliminados registros de actividad para la puerta ID {id_puerta}")
            
            # Luego eliminamos registros relacionados en roledoorpermit
            cursor.execute("DELETE FROM roledoorpermit WHERE ID_door = %s", (id_puerta,))
            print(f"Eliminados permisos de rol para la puerta ID {id_puerta}")
            
            # Luego eliminamos registros relacionados en userdoorpermit
            cursor.execute("DELETE FROM userdoorpermit WHERE ID_door = %s", (id_puerta,))
            print(f"Eliminados permisos de usuario para la puerta ID {id_puerta}")
            
            # Finalmente eliminamos la puerta
            cursor.execute("DELETE FROM Door WHERE ID_door = %s", (id_puerta,))
            
            conexion.commit()
            resultado = cursor.rowcount > 0
            if resultado:
                print(f"Puerta ID {id_puerta} eliminada exitosamente")
            else:
                print(f"No se encontró la puerta con ID {id_puerta} para eliminar")
                
        except Error as e:
            print(f"Error al eliminar puerta: {e}")
            if conexion:
                conexion.rollback()
            raise  # Relanzar la excepción para manejarla en la capa superior
            
        finally:
            if conexion and conexion.is_connected():
                cursor.close()
                conexion.close()
    
    return resultado

def obtener_puertas_activas():
    """Obtener solo puertas activas"""
    conexion = get_connection()
    puertas = []
    
    if conexion:
        try:
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("""
                SELECT ID_door as id, door_name as nombre, creation_time as fecha_creacion, door_img as imagen 
                FROM Door 
                WHERE door_isOpen = TRUE
                ORDER BY creation_time DESC
            """)
            puertas = cursor.fetchall()
        except Error as e:
            print(f"Error al obtener puertas activas: {e}")
        finally:
            if conexion.is_connected():
                cursor.close()
                conexion.close()
    
    return puertas

def contar_puertas():
    """Contar total de puertas"""
    conexion = get_connection()
    total = 0
    
    if conexion:
        try:
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("SELECT COUNT(*) as total FROM Door")
            result = cursor.fetchone()
            total = result['total'] if result else 0
        except Error as e:
            print(f"Error al contar puertas: {e}")
        finally:
            if conexion.is_connected():
                cursor.close()
                conexion.close()
    
    return total

def buscar_puertas(termino, limite=10):
    """Buscar puertas por nombre usando LIKE. Devuelve lista de dicts con id y nombre."""
    conexion = get_connection()
    resultados = []
    if not termino:
        return resultados

    patron = f"%{termino}%"
    if conexion:
        try:
            cursor = conexion.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT ID_door as id, door_name as nombre
                FROM Door
                WHERE door_name LIKE %s
                ORDER BY door_name ASC
                LIMIT %s
                """,
                (patron, int(limite)),
            )
            resultados = cursor.fetchall()
        except Error as e:
            print(f"Error al buscar puertas: {e}")
        finally:
            if conexion.is_connected():
                cursor.close()
                conexion.close()
    # normalizar tipos (id a str para el front)
    for r in resultados:
        try:
            r['id'] = str(r['id'])
        except Exception:
            pass
    return resultados

def obtener_usuarios_con_acceso_puerta(id_puerta):
    """
    Obtiene todos los usuarios que tienen acceso a una puerta específica
    Combina permisos por rol (RoleDoorPermit) y permisos directos (userdoorpermit)
    
    Args:
        id_puerta: ID de la puerta
        
    Returns:
        Lista de diccionarios con información de usuarios con acceso
    """
    conexion = get_connection()
    usuarios = []
    
    if conexion:
        try:
            cursor = conexion.cursor(dictionary=True)
            
            # Query que combina usuarios con acceso por rol y acceso directo
            query = """
            SELECT DISTINCT
                ua.ID_user as id_usuario,
                ua.name as nombre,
                ua.surname as apellido,
                ua.dni,
                r.role as rol,
                'Por rol' as tipo_acceso
            FROM UserAtributes ua
            INNER JOIN Role r ON ua.ID_role = r.ID_role
            INNER JOIN RoleDoorPermit rdp ON r.ID_role = rdp.ID_role
            INNER JOIN User u ON ua.ID_user = u.ID_user
            WHERE rdp.ID_door = %s 
            AND u.user_status = TRUE
            AND ua.nfc_code IS NOT NULL 
            AND ua.nfc_code != ''
            
            UNION
            
            SELECT DISTINCT
                ua.ID_user as id_usuario,
                ua.name as nombre,
                ua.surname as apellido,
                ua.dni,
                r.role as rol,
                'Otorgado' as tipo_acceso
            FROM UserAtributes ua
            INNER JOIN Role r ON ua.ID_role = r.ID_role
            INNER JOIN userdoorpermit udp ON ua.ID_user = udp.ID_user
            INNER JOIN User u ON ua.ID_user = u.ID_user
            WHERE udp.ID_door = %s 
            AND u.user_status = TRUE
            AND ua.nfc_code IS NOT NULL 
            AND ua.nfc_code != ''
            
            ORDER BY nombre, apellido
            """
            
            cursor.execute(query, (id_puerta, id_puerta))
            usuarios = cursor.fetchall()
            
        except Error as e:
            print(f"Error al obtener usuarios con acceso a puerta {id_puerta}: {e}")
        finally:
            if conexion.is_connected():
                cursor.close()
                conexion.close()
    
    return usuarios

def contar_usuarios_con_acceso_puerta(id_puerta):
    """
    Cuenta el número de usuarios que tienen acceso a una puerta específica
    
    Args:
        id_puerta: ID de la puerta
        
    Returns:
        Número entero de usuarios con acceso
    """
    conexion = get_connection()
    total = 0
    
    if conexion:
        try:
            cursor = conexion.cursor(dictionary=True)
            
            # Query que cuenta usuarios únicos con acceso por rol o directo
            query = """
            SELECT COUNT(DISTINCT ua.ID_user) as total
            FROM UserAtributes ua
            INNER JOIN User u ON ua.ID_user = u.ID_user
            WHERE u.user_status = TRUE
            AND ua.nfc_code IS NOT NULL 
            AND ua.nfc_code != ''
            AND (
                ua.ID_role IN (
                    SELECT rdp.ID_role 
                    FROM RoleDoorPermit rdp 
                    WHERE rdp.ID_door = %s
                )
                OR ua.ID_user IN (
                    SELECT udp.ID_user 
                    FROM userdoorpermit udp 
                    WHERE udp.ID_door = %s
                )
            )
            """
            
            cursor.execute(query, (id_puerta, id_puerta))
            result = cursor.fetchone()
            total = result['total'] if result else 0
            
        except Error as e:
            print(f"Error al contar usuarios con acceso a puerta {id_puerta}: {e}")
        finally:
            if conexion.is_connected():
                cursor.close()
                conexion.close()
    
    return total

def obtener_roles_con_acceso_total():
    """
    MSN: Obtiene los IDs de los roles que tienen acceso a todas las puertas
    Returns:
        list: Lista de IDs de roles con acceso total
    """
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = """
        SELECT ID_role 
        FROM roles 
        WHERE acceso_todas_las_puertas = 1
        """
        cursor.execute(query)
        roles = cursor.fetchall()
        
        return [role['ID_role'] for role in roles]
        
    except Exception as e:
        print(f"Error al obtener roles con acceso total: {str(e)}")
        return []
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
