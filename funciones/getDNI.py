from bdd.conexionBDD import get_connection

def obtenerDNIPorID(id_useratributes):
    """
    Obtiene el DNI de una persona dado su ID_useratributes desde la base de datos.
    CORREGIDO: Ahora usa ID_useratributes en lugar de ID_user
    """
    conexion = get_connection()
    if conexion is None:
        return None

    try:
        cursor = conexion.cursor()
        # CORRECCIÓN: Usar ID_useratributes en lugar de ID_user
        consulta = "SELECT dni FROM UserAtributes WHERE ID_useratributes = %s"
        cursor.execute(consulta, (id_useratributes,))
        resultado = cursor.fetchone()
        if resultado:
            dni_str = resultado[0]
            try:
                # Retornar el DNI completo como string
                return dni_str
            except Exception as e:
                print(f"Error procesando DNI: {e}")
                return None
        else:
            print(f"No se encontró usuario con ID_useratributes: {id_useratributes}")
            return None
    except Exception as e:
        print(f"Error al obtener DNI: {e}")
        return None
    finally:
        cursor.close()
        conexion.close()
