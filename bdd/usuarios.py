import mysql.connector
from bdd.conexionBDD import get_connection

def obtener_todos_los_usuarios():
    """
    Obtiene todos los usuarios de la base de datos MySQL
    """
    connection = get_connection()
    if connection is None:
        return []
    
    cursor = connection.cursor()
    
    query = """
    SELECT 
        u.ID_user,
        ua.name,
        ua.surname,
        ua.dni,
        r.role as rol,
        ua.exit_permit
    FROM User u
    JOIN UserAtributes ua ON u.ID_user = ua.ID_user
    JOIN Role r ON ua.ID_role = r.ID_role
    WHERE ua.nfc_code IS NOT NULL AND ua.nfc_code != ''
    ORDER BY ua.name, ua.surname
    """
    
    cursor.execute(query)
    usuarios = cursor.fetchall()
    
    cursor.close()
    connection.close()
    
    # Convertir a lista de diccionarios
    usuarios_list = []
    for usuario in usuarios:
        usuarios_list.append({
            'id': usuario[0],
            'nombre': usuario[1],
            'apellido': usuario[2],
            'dni': usuario[3],
            'rol': usuario[4],
            'exit_permit': bool(usuario[5])
        })
    
    return usuarios_list

def obtener_usuario_por_id(id_usuario):
    """
    Obtiene un usuario específico por su ID
    """
    connection = get_connection()
    if connection is None:
        return None
    
    cursor = connection.cursor()
    
    query = """
    SELECT 
        u.ID_user,
        ua.name,
        ua.surname,
        ua.dni,
        r.role as rol,
        ua.exit_permit
    FROM User u
    JOIN UserAtributes ua ON u.ID_user = ua.ID_user
    JOIN Role r ON ua.ID_role = r.ID_role
    WHERE u.ID_user = %s
    """
    
    cursor.execute(query, (id_usuario,))
    usuario = cursor.fetchone()
    
    cursor.close()
    connection.close()
    
    if usuario:
        return {
            'id': usuario[0],
            'nombre': usuario[1],
            'apellido': usuario[2],
            'dni': usuario[3],
            'rol': usuario[4],
            'exit_permit': bool(usuario[5])
        }
    
    return None

def buscar_usuarios(termino_busqueda):
    """
    Busca usuarios por nombre, apellido o DNI
    """
    connection = get_connection()
    if connection is None:
        return []
    
    cursor = connection.cursor()
    
    query = """
    SELECT 
        u.ID_user,
        ua.name,
        ua.surname,
        ua.dni,
        r.role as rol,
        ua.exit_permit
    FROM User u
    JOIN UserAtributes ua ON u.ID_user = ua.ID_user
    JOIN Role r ON ua.ID_role = r.ID_role
    WHERE (ua.name LIKE %s OR 
          ua.surname LIKE %s OR 
          ua.dni LIKE %s) AND
          ua.nfc_code IS NOT NULL AND ua.nfc_code != ''
    ORDER BY ua.name, ua.surname
    """
    
    termino = f"%{termino_busqueda}%"
    cursor.execute(query, (termino, termino, termino))
    usuarios = cursor.fetchall()
    
    cursor.close()
    connection.close()
    
    usuarios_list = []
    for usuario in usuarios:
        usuarios_list.append({
            'id': usuario[0],
            'nombre': usuario[1],
            'apellido': usuario[2],
            'dni': usuario[3],
            'rol': usuario[4],
            'exit_permit': bool(usuario[5])
        })
    
    return usuarios_list

def filtrar_usuarios_por_rol(id_rol):
    """
    Filtra usuarios por rol específico
    """
    connection = get_connection()
    if connection is None:
        return []
    
    cursor = connection.cursor()
    
    query = """
    SELECT 
        u.ID_user,
        ua.name,
        ua.surname,
        ua.dni,
        r.role as rol,
        ua.exit_permit
    FROM User u
    JOIN UserAtributes ua ON u.ID_user = ua.ID_user
    JOIN Role r ON ua.ID_role = r.ID_role
    WHERE ua.ID_role = %s
    ORDER BY ua.name, ua.surname
    """
    
    cursor.execute(query, (id_rol,))
    usuarios = cursor.fetchall()
    
    cursor.close()
    connection.close()
    
    usuarios_list = []
    for usuario in usuarios:
        usuarios_list.append({
            'id': usuario[0],
            'nombre': usuario[1],
            'apellido': usuario[2],
            'dni': usuario[3],
            'rol': usuario[4],
            'exit_permit': bool(usuario[5])
        })
    
    return usuarios_list

def obtener_roles_disponibles():
    """
    Obtiene todos los roles disponibles
    """
    connection = get_connection()
    if connection is None:
        return []
    
    cursor = connection.cursor()
    
    query = "SELECT ID_role, role FROM Role ORDER BY role"
    cursor.execute(query)
    roles = cursor.fetchall()
    
    cursor.close()
    connection.close()
    
    roles_list = []
    for rol in roles:
        roles_list.append({
            'id': rol[0],
            'nombre': rol[1]
        })
    
    return roles_list

def eliminar_usuario(id_usuario):
    """
    Elimina un usuario (soft delete)
    """
    connection = get_connection()
    if connection is None:
        return False
    
    cursor = connection.cursor()
    
    try:
        query = "UPDATE User SET user_status = FALSE WHERE ID_user = %s"
        cursor.execute(query, (id_usuario,))
        connection.commit()
        cursor.close()
        connection.close()
        return True
    except Exception as e:
        cursor.close()
        connection.close()
        return False

def eliminar_usuario_completo(id_usuario):
    """
    Elimina completamente un usuario y todos sus datos relacionados (hard delete)
    """
    connection = get_connection()
    if connection is None:
        return False
    
    cursor = connection.cursor()
    
    try:
        # Iniciar transacción
        connection.start_transaction()
        
        # 1. Eliminar registros relacionados en userdoorpermit
        query_delete_permissions = """
        DELETE FROM userdoorpermit 
        WHERE ID_user = %s
        """
        cursor.execute(query_delete_permissions, (id_usuario,))
        
        # 2. Eliminar registros en activity que referencian al usuario
        query_delete_activity = """
        DELETE FROM activity 
        WHERE ID_useratributes IN (SELECT ID_useratributes FROM useratributes WHERE ID_user = %s)
        """
        cursor.execute(query_delete_activity, (id_usuario,))
        
        # 3. Eliminar registros en tracking que referencian al usuario
        query_delete_tracking = """
        DELETE FROM tracking 
        WHERE ID_useratributes IN (SELECT ID_useratributes FROM useratributes WHERE ID_user = %s)
        """
        cursor.execute(query_delete_tracking, (id_usuario,))
        
        # 4. Eliminar registros en useratributes
        query_delete_attributes = """
        DELETE FROM useratributes 
        WHERE ID_user = %s
        """
        cursor.execute(query_delete_attributes, (id_usuario,))
        
        # 5. Eliminar registros en permit
        query_delete_permit = """
        DELETE FROM permit 
        WHERE ID_user = %s
        """
        cursor.execute(query_delete_permit, (id_usuario,))
        
        # 6. Finalmente, eliminar el usuario de la tabla user
        query_delete_user = """
        DELETE FROM user 
        WHERE ID_user = %s
        """
        cursor.execute(query_delete_user, (id_usuario,))
        
        # Confirmar la transacción
        connection.commit()
        cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        # En caso de error, hacer rollback de la transacción
        if connection.is_connected():
            connection.rollback()
        print(f"Error en eliminar_usuario_completo: {str(e)}")
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()
        return False

def actualizar_rol_usuario(id_usuario, id_rol):
    """
    Actualiza el rol de un usuario
    """
    connection = get_connection()
    if connection is None:
        return False
    
    cursor = connection.cursor()
    
    try:
        # Verificar si el usuario existe
        cursor.execute("SELECT ID_user FROM User WHERE ID_user = %s", (id_usuario,))
        if not cursor.fetchone():
            return False
            
        # Verificar si el rol existe
        cursor.execute("SELECT ID_role FROM Role WHERE ID_role = %s", (id_rol,))
        if not cursor.fetchone():
            return False
            
        # Actualizar el rol del usuario
        query = """
        UPDATE UserAtributes 
        SET ID_role = %s 
        WHERE ID_user = %s
        """
        cursor.execute(query, (id_rol, id_usuario))
        
        connection.commit()
        cursor.close()
        connection.close()
        return True
    except Exception as e:
        print(f"Error al actualizar rol del usuario: {str(e)}")
        if connection.is_connected():
            cursor.close()
            connection.close()
        return False

def actualizar_usuario(id_usuario, datos):
    """
    Actualiza los datos de un usuario
    """
    connection = get_connection()
    if connection is None:
        return False
    
    cursor = connection.cursor()
    
    try:
        # Actualizar UserAtributes
        query = """
        UPDATE UserAtributes 
        SET name = %s, surname = %s, dni = %s, exit_permit = %s
        WHERE ID_user = %s
        """
        
        cursor.execute(query, (
            datos['nombre'],
            datos['apellido'],
            datos['dni'],
            datos['exit_permit'],
            id_usuario
        ))
        
        # Actualizar rol si es necesario
        if 'id_rol' in datos:
            query = "UPDATE UserAtributes SET ID_role = %s WHERE ID_user = %s"
            cursor.execute(query, (datos['id_rol'], id_usuario))
        
        connection.commit()
        cursor.close()
        connection.close()
        return True
    except Exception as e:
        cursor.close()
        connection.close()
        return False
