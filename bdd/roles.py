import mysql.connector
from bdd.conexionBDD import get_connection as obtener_conexion

def obtener_todos_los_roles():
    """
    Obtiene todos los roles de la base de datos
    Retorna: lista de diccionarios con la información de cada rol
    """
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        
        # quitar WHEN r.ID_role = 3 THEN 1

        query = """
        SELECT 
            r.ID_role as id,
            r.role as nombre,
            CASE 
                WHEN r.ID_role = 3 THEN 1
                WHEN NOT EXISTS (
                    SELECT 1 
                    FROM Door d
                    WHERE NOT EXISTS (
                        SELECT 1 
                        FROM RoleDoorPermit rdp 
                        WHERE rdp.ID_role = r.ID_role 
                        AND rdp.ID_door = d.ID_door
                    )
                ) THEN 1
                ELSE 0 
            END as acceso_todas_puertas,
            r.asignar_permisos_usuarios as asignar_permisos_usuarios,
            0 as usuarios_asignados
        FROM Role r
        ORDER BY r.role
        """
        
        cursor.execute(query)
        roles = cursor.fetchall()
        
        # Contar usuarios asignados a cada rol
        for rol in roles:
            cursor.execute(
                "SELECT COUNT(*) as total FROM UserAtributes WHERE ID_role = %s",
                (rol['id'],)
            )
            resultado = cursor.fetchone()
            rol['usuarios_asignados'] = resultado['total']
        
        return roles
        
    except Exception as e:
        print(f"Error al obtener roles: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()

def asegurar_permisos_master_en_todas_puertas(id_rol_master=3):
    """
    Garantiza que el rol master (ID=3 por defecto) tenga permisos en todas las puertas
    insertando en RoleDoorPermit las relaciones faltantes.
    """
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        if conexion is None:
            return False
        cursor = conexion.cursor()

        # Insertar de forma idempotente los permisos faltantes para el rol master
        query = (
            """
            INSERT IGNORE INTO RoleDoorPermit (ID_role, ID_door)
            SELECT %s AS ID_role, d.ID_door
            FROM Door d
            LEFT JOIN RoleDoorPermit rdp
              ON rdp.ID_door = d.ID_door AND rdp.ID_role = %s
            WHERE rdp.ID_role IS NULL
            """
        )
        cursor.execute(query, (id_rol_master, id_rol_master))
        conexion.commit()
        return True
    except Exception as e:
        if conexion:
            try:
                conexion.rollback()
            except Exception:
                pass
        print(f"Error al asegurar permisos master: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()

def obtener_flag_asignar_permisos_por_usuario(id_usuario):
    """
    Devuelve True si el rol del usuario tiene asignado el flag
    Role.asignar_permisos_usuarios = 1. Caso contrario False.
    """
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        if conexion is None:
            return False
        cursor = conexion.cursor()
        query = (
            """
            SELECT r.asignar_permisos_usuarios
            FROM UserAtributes ua
            INNER JOIN Role r ON ua.ID_role = r.ID_role
            WHERE ua.ID_user = %s
            """
        )
        cursor.execute(query, (id_usuario,))
        row = cursor.fetchone()
        if row is None:
            return False
        # row can be tuple like (0,) or (1,)
        value = row[0]
        try:
            return bool(int(value))
        except Exception:
            return bool(value)
    except Exception as e:
        print(f"Error al obtener flag asignar_permisos_usuarios por usuario: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()

def crear_rol(nombre, acceso_todas_puertas=False, asignar_permisos_usuarios=False, puertas=None):
    """
    Crea un nuevo rol en la base de datos
    
    Args:
        nombre: Nombre del rol
        acceso_todas_puertas: Booleano que indica si el rol tiene acceso a todas las puertas
        asignar_permisos_usuarios: Booleano que indica si el rol puede asignar permisos a usuarios
        puertas: Lista de IDs de puertas a asignar (opcional, solo si acceso_todas_puertas es False)
        
    Retorna: 
        (success, role_id) donde success es booleano indicando si se creó exitosamente,
        y role_id es el ID del rol creado (o None si hubo error)
    """
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        
        # Insertar el nuevo rol
        query = "INSERT INTO Role (role, asignar_permisos_usuarios) VALUES (%s, %s)"
        cursor.execute(query, (nombre, asignar_permisos_usuarios))
        role_id = cursor.lastrowid
        
        # Si tiene acceso a todas las puertas, obtener todas las puertas existentes
        if acceso_todas_puertas:
            cursor.execute("SELECT ID_door FROM Door")
            puertas = [row[0] for row in cursor.fetchall()]
        
        # Asignar las puertas al rol
        if puertas and len(puertas) > 0:
            # Eliminar duplicados por si acaso
            puertas_unicas = list(set(puertas))
            
            # Insertar relaciones con las puertas
            placeholders = ', '.join(['(%s, %s)'] * len(puertas_unicas))
            values = []
            for puerta_id in puertas_unicas:
                values.extend([role_id, puerta_id])
                
            query = f"INSERT INTO RoleDoorPermit (ID_role, ID_door) VALUES {placeholders}"
            cursor.execute(query, values)
        
        conexion.commit()
        return True, role_id
        
    except mysql.connector.IntegrityError as e:
        # El rol ya existe o violación de clave foránea
        print(f"Error de integridad al crear rol: {e}")
        if conexion:
            conexion.rollback()
        return False, None
    except Exception as e:
        print(f"Error al crear rol: {e}")
        if conexion:
            conexion.rollback()
        return False, None
    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()

def actualizar_rol(id_rol, nombre, acceso_todas_puertas=False, asignar_permisos_usuarios=False, puertas=None):
    """
    Actualiza un rol existente con toda su información
    
    Args:
        id_rol: ID del rol a actualizar
        nombre: Nuevo nombre del rol
        acceso_todas_puertas: Si es True, asigna acceso a todas las puertas existentes
        asignar_permisos_usuarios: Booleano que indica si el rol puede asignar permisos a usuarios
        puertas: Lista de IDs de puertas a asignar (solo se usa si acceso_todas_puertas es False)
        
    Retorna: 
        True si se actualizó exitosamente, False si hubo error
    """
    if puertas is None:
        puertas = []
        
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        
        # Iniciar transacción
        conexion.start_transaction()
        
        # 1. Actualizar información básica del rol
        query = """
            UPDATE Role 
            SET role = %s, 
                asignar_permisos_usuarios = %s
            WHERE ID_role = %s
        """
        cursor.execute(query, (nombre, asignar_permisos_usuarios, id_rol))
        
        # 2. Eliminar todos los permisos existentes primero
        cursor.execute("DELETE FROM roledoorpermit WHERE ID_role = %s", (id_rol,))
        
        # 3. Manejar la asignación de puertas según el tipo de acceso
        if acceso_todas_puertas:
            # Obtener todas las puertas existentes
            cursor.execute("SELECT ID_door FROM Door")
            todas_las_puertas = [str(puerta['ID_door']) for puerta in cursor.fetchall()]
            puertas = todas_las_puertas
        
        # 4. Insertar los nuevos permisos si hay puertas para asignar
        if puertas:
            # Convertir puertas a enteros y eliminar duplicados
            puertas_unicas = list(set(int(puerta_id) for puerta_id in puertas if str(puerta_id).isdigit()))
            if puertas_unicas:
                placeholders = ', '.join(['(%s, %s)'] * len(puertas_unicas))
                values = []
                for puerta_id in puertas_unicas:
                    values.extend([id_rol, puerta_id])
                
                query = f"""
                    INSERT INTO roledoorpermit (ID_role, ID_door)
                    VALUES {placeholders}
                """
                cursor.execute(query, values)
    
        # Confirmar transacción
        conexion.commit()
        return True
        
    except mysql.connector.IntegrityError as e:
        if conexion:
            conexion.rollback()
        print(f"Error de integridad al actualizar rol: {e}")
        return False
    except Exception as e:
        if conexion:
            conexion.rollback()
        print(f"Error al actualizar rol: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conexion and conexion.is_connected():
            conexion.close()

def eliminar_rol(id_rol, forzar_eliminacion=False):
    """
    Elimina un rol de la base de datos
    
    Parámetros:
        id_rol: ID del rol a eliminar
        forzar_eliminacion: Si es True, asigna a los usuarios el rol por defecto (ID 2) y elimina el rol
        
    Retorna: 
        (success, mensaje) donde success es booleano indicando si se realizó la operación exitosamente,
        y mensaje contiene información sobre el resultado
    """
    print(f"\n=== Iniciando eliminación de rol ===")
    print(f"ID Rol: {id_rol}, Forzar eliminación: {forzar_eliminacion}")
    
    conexion = None
    cursor = None
    try:
        print("Obteniendo conexión a la base de datos...")
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        
        # Asegurarse de que el ID sea un entero
        try:
            id_rol = int(id_rol)
            print(f"ID convertido a entero: {id_rol}")
        except ValueError as e:
            print(f"Error: ID no es un número válido: {id_rol}")
            return False, "ID de rol no válido"
        
        # Verificar si el rol existe
        print(f"Verificando existencia del rol {id_rol}...")
        cursor.execute("SHOW TABLES LIKE 'Role'")
        print(f"Tabla Role existe: {cursor.fetchone() is not None}")
        
        cursor.execute("SELECT role FROM Role WHERE ID_role = %s", (id_rol,))
        rol = cursor.fetchone()
        print(f"Resultado de búsqueda del rol: {rol}")
        
        if not rol:
            return False, "El rol no existe"
            
        # Verificar si el rol es el de administrador (ID 1)
        if id_rol == 1:
            return False, "No se puede eliminar el rol de administrador"
            
        # Verificar si es el rol por defecto (ID 2)
        if id_rol == 2:
            return False, "No se puede eliminar el rol de usuario por defecto"
        
        # Verificar si hay usuarios asignados a este rol
        print("Verificando usuarios asignados al rol...")
        cursor.execute(
            "SELECT ID_user FROM UserAtributes WHERE ID_role = %s",
            (id_rol,)
        )
        usuarios = cursor.fetchall()
        print(f"Usuarios encontrados: {len(usuarios)}")
        
        if usuarios and not forzar_eliminacion:
            return False, "existen_usuarios"
        
        # Si hay usuarios y se forzó la eliminación, reasignar al rol por defecto (ID 2)
        if usuarios and forzar_eliminacion:
            print(f"Reasignando {len(usuarios)} usuarios al rol por defecto...")
            cursor.execute(
                "UPDATE UserAtributes SET ID_role = 2 WHERE ID_role = %s",
                (id_rol,)
            )
        
        # Eliminar permisos asociados
        print("Eliminando permisos asociados...")
        cursor.execute("DELETE FROM RoleDoorPermit WHERE ID_role = %s", (id_rol,))
        
        # Eliminar el rol
        print("Eliminando el rol...")
        cursor.execute("DELETE FROM Role WHERE ID_role = %s", (id_rol,))
        
        conexion.commit()
        print("Cambios confirmados en la base de datos")
        
        if usuarios and forzar_eliminacion:
            return True, f"Se eliminó el rol y se reasignaron {len(usuarios)} usuarios al rol por defecto"
        else:
            return True, "Rol eliminado exitosamente"
        
    except mysql.connector.Error as err:
        print(f"Error de MySQL: {err}")
        print(f"Número de error: {err.errno}")
        print(f"SQL State: {err.sqlstate}")
        if conexion:
            conexion.rollback()
            print("Rollback realizado")
        return False, f"Error al eliminar el rol: {err}"
    except Exception as e:
        print(f"Error inesperado: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        if conexion:
            conexion.rollback()
            print("Rollback realizado")
        return False, f"Error inesperado al eliminar el rol: {e}"
    finally:
        if cursor:
            cursor.close()
            print("Cursor cerrado")
        if conexion:
            conexion.close()
            print("Conexión cerrada")
        print("=== Fin de la eliminación de rol ===\n")

def obtener_rol_por_id(id_rol):
    """
    Obtiene un rol específico por su ID
    Retorna: diccionario con la información del rol o None si no existe
    """
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        
        query = "SELECT ID_role as id, role as nombre FROM Role WHERE ID_role = %s"
        cursor.execute(query, (id_rol,))
        rol = cursor.fetchone()
        
        return rol
        
    except Exception as e:
        print(f"Error al obtener rol por ID: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()

def obtener_roles_para_select():
    """
    Obtiene solo ID y nombre de todos los roles para select dropdowns
    Retorna: lista de diccionarios con id y nombre
    """
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        
        query = "SELECT ID_role as id, role as nombre FROM Role ORDER BY role"
        cursor.execute(query)
        roles = cursor.fetchall()
        
        return roles
        
    except Exception as e:
        print(f"Error al obtener roles para select: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()

def obtener_rol_por_nombre(nombre_rol):
    """
    Obtiene un rol por su nombre
    
    Args:
        nombre_rol: Nombre del rol a buscar
        
    Retorna:
        Diccionario con la información del rol o None si no se encuentra
    """
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        
        query = "SELECT ID_role as id, role as nombre FROM Role WHERE role = %s"
        cursor.execute(query, (nombre_rol,))
        rol = cursor.fetchone()
        
        return rol
        
    except Exception as e:
        print(f"Error al obtener rol por nombre: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()
