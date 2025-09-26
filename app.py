from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
from funciones.getDNI import obtenerDNIPorID
from funciones.hashDNI import hashearDNI
import bdd.usuarios_temporales as usuarios_temp
import bdd.roles as roles_db
from bdd.usuarios import actualizar_rol_usuario, obtener_usuario_por_id, eliminar_usuario_completo
from auth.auth import auth_bp
from auth.decorators import login_required, nfc_required, require_api_key
import bdd.puertas as puertas
from bdd.puertas import obtener_todas_puertas
from flask_mysqldb import MySQL
import hashlib
import secrets
import logging
import time
import MySQLdb
from datetime import datetime, timedelta
from functools import wraps
import uuid
from flask import Flask, request, jsonify


# MSN: Import APScheduler module for permission cleanup
from APScheduler import init_scheduler, start_scheduler, scheduler


# MSN: Configuración del sistema de control de acceso
CONFIG = {
    'EXIT_PERMIT_DURATION_HOURS': 12,  # Duración del permiso de salida
    'DOOR_TIMEOUT_SECONDS': 30,        # Timeout si no se cierra la puerta
    'DEBOUNCE_SECONDS': 1,             # Tiempo de debounce
    'API_KEY': 'MBordon'   # CAMBIAR EN PRODUCCIÓN
}


# Global variables for NFC debugging
ultimo_uid = None
ultimo_resultado = None

app = Flask(__name__)
app.secret_key = 'MBordon'  # Cambiar en producción
CORS(app)

# MSN: Configuración MySQL para el sistema de control de acceso
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'NotFC'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

# Sincronizar permisos del rol master (ID=3) con todas las puertas existentes (idempotente)
try:
    roles_db.asegurar_permisos_master_en_todas_puertas()
    print("[INIT] Permisos master sincronizados con todas las puertas existentes")
except Exception as e:
    print(f"[INIT] No se pudieron sincronizar permisos master: {e}")



# Variables globales para el estado del NFC
nfc_state = {
    'usuario_id': None,
    'hash_code': None,
    'uid_detectado': None,
    'estado_actual': 'idle',  # idle, waiting, detected, writing, success, failed
    'mensaje': '',
    'timestamp': None,
    'esperando_tag': False,
    'proceso_completado': False
}

# MSN: Cache para debounce
scan_cache = {}

# MSN: Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('access_control.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# MSN: Inicialización del scheduler de limpieza de permisos
if __name__ == '__main__':
    try:
        # Solo inicializar el scheduler una vez
        if not hasattr(app, 'scheduler_initialized'):
            scheduler_instance = init_scheduler()
            if scheduler_instance and start_scheduler():
                app.scheduler_initialized = True
                print("MSN: APScheduler inicializado correctamente para limpieza de permisos")
            else:
                print("MSN: No se pudo iniciar el scheduler de limpieza de permisos")
        else:
            print("MSN: El scheduler ya fue inicializado previamente")
    except Exception as e:
        print(f"MSN: Error al inicializar el scheduler de limpieza de permisos: {str(e)}")

# MSN: Registrar el manejador de apagado
import atexit
@atexit.register
def shutdown_scheduler():
    try:
        if scheduler and scheduler.running:
            scheduler.shutdown(wait=False)
            print("MSN: Scheduler detenido correctamente")
    except Exception as e:
        print(f"MSN: Error al detener el scheduler: {str(e)}")

@app.route('/index-user')
@login_required
@nfc_required
def indexUser():
    try:
        from bdd.miPerfil.miPerfil import obtener_informacion_usuario_actual
        from bdd.actividades_recientes import obtener_actividades_recientes
        from bdd.roles import obtener_flag_asignar_permisos_por_usuario
        from flask import session, redirect, url_for
        
        user_id = session.get('user_id')
        
        # Redirect admin users to the main index page
        if user_id == 1:
            return redirect(url_for('index'))
            
        usuario_info = obtener_informacion_usuario_actual(user_id) if user_id else None
        is_admin = (user_id == 1)
        # Detectar si el usuario tiene rol master (ID_role = 3)
        is_master = False
        try:
            if user_id:
                cur = mysql.connection.cursor()
                cur.execute("SELECT ID_role FROM UserAtributes WHERE ID_user = %s", (user_id,))
                row = cur.fetchone()
                cur.close()
                # row puede ser tupla como (3,) dependiendo del cursor
                if row is not None:
                    role_id = row[0] if isinstance(row, (tuple, list)) else row.get('ID_role')
                    is_master = (int(role_id) == 3)
        except Exception as e:
            print(f"[WARN] No se pudo determinar is_master: {e}")
        can_assign_permissions = False
        
        if user_id and not is_admin:
            try:
                can_assign_permissions = obtener_flag_asignar_permisos_por_usuario(user_id)
            except Exception as e:
                print(f"[WARN] No se pudo obtener can_assign_permissions: {e}")
        
        # Obtener las últimas 3 actividades del usuario
        actividades_recientes = obtener_actividades_recientes(limite=3, user_id=user_id) if user_id else []
        
        return render_template('shared/index-users.html', 
                            usuario=usuario_info,
                            is_admin=is_admin,
                            is_master=is_master,
                            user_id=user_id,
                            can_assign_permissions=can_assign_permissions,
                            actividades_recientes=actividades_recientes)
    except Exception as e:
        print(f"Error en indexUser: {e}")
        return render_template('shared/index-users.html', 
                            usuario=None, 
                            is_admin=False, 
                            user_id=None, 
                            can_assign_permissions=False,
                            actividades_recientes=[])

@app.route('/')
@login_required
@nfc_required
def index():
    try:
        from bdd.miPerfil.miPerfil import obtener_informacion_usuario_actual
        from bdd.actividades_recientes import obtener_actividades_recientes
        from flask import session
        # Permisos especiales para asignar permisos a usuarios
        from bdd.roles import obtener_flag_asignar_permisos_por_usuario
        
        user_id = session.get('user_id')
        print(f"[DEBUG] Index route - User ID from session: {user_id}, Type: {type(user_id)}")  # Debug log
        
        # Force admin for testing (temporary)
        # user_id = 1
        # print("[DEBUG] FORCING ADMIN MODE FOR TESTING")
        
        usuario_info = obtener_informacion_usuario_actual(user_id) if user_id else None
        is_admin = (user_id == 1)  # Check if user is admin (ID 1)
        
        print(f"[DEBUG] Is admin: {is_admin}")  # Debug log
        print(f"[DEBUG] User info: {usuario_info}")
        
        can_assign_permissions = False
        if user_id and not is_admin:
            try:
                can_assign_permissions = obtener_flag_asignar_permisos_por_usuario(user_id)
            except Exception as e:
                print(f"[WARN] No se pudo obtener can_assign_permissions: {e}")
        
        # Obtener las últimas 3 actividades del usuario
        actividades_recientes = obtener_actividades_recientes(limite=3, user_id=user_id) if user_id else []
        print(f"[DEBUG] Actividades recientes obtenidas: {actividades_recientes}")
        print(f"[DEBUG] Número de actividades: {len(actividades_recientes) if actividades_recientes else 0}")
        
        # Debug: Print template context
        template_context = {
            'usuario': usuario_info,
            'is_admin': is_admin,
            'user_id': user_id,
            'can_assign_permissions': can_assign_permissions,
            'actividades_recientes': actividades_recientes
        }
        print(f"[DEBUG] Template context: {template_context}")
        
        response = render_template('shared/index.html', **template_context)
        print(f"[DEBUG] Template rendered with user_id: {user_id}")  # Debug log
        return response
    except Exception as e:
        import traceback
        print(f"[ERROR] Error en index: {e}")
        traceback.print_exc()  # This will print the full traceback
        return render_template('shared/index.html', 
                            usuario=None, 
                            is_admin=False, 
                            user_id=None, 
                            can_assign_permissions=False,
                            actividades_recientes=[])

@app.route('/api/doors/search')
@login_required
@nfc_required
def api_search_doors():
    """Busca puertas por nombre (LIKE) y devuelve JSON [{id, nombre}]."""
    try:
        from bdd.puertas import buscar_puertas
        term = request.args.get('q', '', type=str)
        limit = request.args.get('limit', 10, type=int)
        results = buscar_puertas(term, limit)
        return jsonify({"success": True, "doors": results})
    except Exception as e:
        print(f"Error en api_search_doors: {e}")
        return jsonify({"success": False, "doors": [], "message": str(e)}), 500

@app.route('/usuarios')
@login_required
@nfc_required
def usuarios():
    """
    Muestra la página de gestión de usuarios con datos reales de la base de datos
    """
    try:
        # Importar la función para obtener usuarios
        from bdd.usuarios import obtener_todos_los_usuarios, obtener_roles_disponibles
        
        # Obtener todos los usuarios de la base de datos
        usuarios = obtener_todos_los_usuarios()
        
        # Obtener roles disponibles para el filtro
        roles = obtener_roles_disponibles()
        
        return render_template('admin/usuarios.html', usuarios=usuarios, roles=roles)
        
    except Exception as e:
        print(f"Error al obtener usuarios: {e}")
        return render_template('admin/usuarios.html', usuarios=[], roles=[])

@app.route('/usuariosTemporales')
@login_required
@nfc_required
def usuarios_temporarios():
    usuarios = usuarios_temp.get_usuarios_temporales()
    return render_template('admin/usuarios-temporarios.html', usuarios=usuarios)

@app.route('/eliminarUsuarioTemporal/<int:id_useratributes>', methods=['DELETE'])
@login_required
@nfc_required
def eliminar_usuario_temporal(id_useratributes):
    """
    Elimina un usuario temporal de la base de datos.
    Realiza un hard delete eliminando completamente el registro de User y UserAtributes.
    """
    try:
        # Verificar si el usuario existe
        if not usuarios_temp.verificar_usuario_existe(id_useratributes):
            return jsonify({"success": False, "message": "Usuario no encontrado"}), 404
            
        # Eliminar el usuario
        result = usuarios_temp.eliminar_usuario_temporal(id_useratributes)
        
        if result:
            return jsonify({
                "success": True, 
                "message": "Usuario eliminado exitosamente de la base de datos"
            }), 200
        else:
            return jsonify({
                "success": False, 
                "message": "No se pudo eliminar el usuario de la base de datos"
            }), 400
            
    except Exception as e:
        print(f"Error en eliminar_usuario_temporal: {e}")
        return jsonify({
            "success": False, 
            "message": f"Error interno del servidor: {str(e)}"
        }), 500

@app.route('/api/miPerfil/foto', methods=['POST'])
@login_required
@nfc_required
def api_actualizar_foto_perfil():
    """
    Sube o elimina la foto de perfil del usuario autenticado.
    - Si llega form-data con campo 'remove' = '1', elimina (pone NULL en DB).
    - Si llega archivo 'foto', lo guarda en static/img/users/ y actualiza DB con ruta relativa.
    Responde JSON { success, message, photo_url }
    """
    try:
        from flask import session
        from bdd.miPerfil.miPerfil import actualizar_foto_usuario

        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"success": False, "message": "Usuario no autenticado"}), 401

        # Asegurar carpeta destino
        base_static = os.path.join(os.path.dirname(__file__), 'static')
        users_dir = os.path.join(base_static, 'img', 'users')
        os.makedirs(users_dir, exist_ok=True)

        remove_flag = request.form.get('remove')
        if remove_flag == '1':
            ok = actualizar_foto_usuario(user_id, None)
            if ok:
                return jsonify({"success": True, "message": "Foto eliminada", "photo_url": None}), 200
            return jsonify({"success": False, "message": "No se pudo eliminar la foto"}), 400

        if 'foto' not in request.files:
            return jsonify({"success": False, "message": "No se envió archivo"}), 400

        file = request.files['foto']
        if file.filename == '':
            return jsonify({"success": False, "message": "Archivo inválido"}), 400

        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        # Guardar con nombre estable por usuario
        safe_name = f"user_{user_id}{ext.lower() if ext else '.jpg'}"
        save_path = os.path.join(users_dir, safe_name)
        file.save(save_path)

        # Ruta relativa para servir via url_for('static', filename=...)
        relative_path = os.path.join('img', 'users', safe_name).replace('\\', '/')
        ok = actualizar_foto_usuario(user_id, relative_path)
        if ok:
            # Registrar el cambio de foto de perfil en el tracking
            from funciones.tracking import registrar_evento_tracking
            registrar_evento_tracking(
                user_id=user_id,
                tipo_evento='cambio_foto_perfil',
                detalles=f"Foto de perfil actualizada: {relative_path}"
            )
            return jsonify({"success": True, "message": "Foto actualizada", "photo_url": url_for('static', filename=relative_path)}), 200
        return jsonify({"success": False, "message": "No se pudo actualizar la foto"}), 400

    except Exception as e:
        print(f"Error al actualizar foto de perfil: {e}")
        return jsonify({
            "success": False,
            "message": f"Error interno del servidor: {str(e)}"
        }), 500

@app.route('/api/miPerfil/baja', methods=['POST'])
@login_required
@nfc_required
def api_baja_cuenta_usuario():
    """Desactiva la cuenta del usuario autenticado (user_status = 0)."""
    try:
        from flask import session
        from bdd.miPerfil.miPerfil import dar_de_baja_usuario
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"success": False, "message": "Usuario no autenticado"}), 401

        data = request.get_json(silent=True) or {}
        reason = data.get('reason')
        ok = dar_de_baja_usuario(user_id, reason)
        status = 200 if ok else 400
        return jsonify({"success": ok, "message": "Cuenta desactivada" if ok else "No se pudo desactivar la cuenta"}), status
    except Exception as e:
        print(f"Error en api_baja_cuenta_usuario: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

# API endpoint para cambiar contraseña del usuario
@app.route('/api/miPerfil/cambiar-password', methods=['POST'])
@login_required
@nfc_required
def api_cambiar_password_usuario():
    """
    Cambia la contraseña del usuario validando la actual
    Body JSON: { currentPassword: str, newPassword: str }
    """
    try:
        from bdd.miPerfil.miPerfil import actualizar_password_usuario
        data = request.get_json() or {}
        current_password = data.get('currentPassword', '')
        new_password = data.get('newPassword', '')
        from flask import session
        user_id = session.get('user_id')

        if not user_id:
            return jsonify({"success": False, "message": "Usuario no autenticado"}), 401
        if not current_password or not new_password:
            return jsonify({"success": False, "message": "Contraseñas requeridas"}), 400
        # Validación de complejidad: mínimo 8, una mayúscula, una minúscula, un número y un caracter especial
        has_min = len(new_password) >= 8
        has_upper = any(c.isupper() for c in new_password)
        has_lower = any(c.islower() for c in new_password)
        has_digit = any(c.isdigit() for c in new_password)
        special_chars = set('!@#$%^&*(),.?":{}|<>')
        has_special = any(c in special_chars for c in new_password)
        if not (has_min and has_upper and has_lower and has_digit and has_special):
            return jsonify({
                "success": False,
                "message": "La nueva contraseña debe tener mínimo 8 caracteres, una mayúscula, una minúscula, un número y un caracter especial"
            }), 400

        ok, msg = actualizar_password_usuario(user_id, current_password, new_password)
        status = 200 if ok else 400
        
        # Registrar el cambio de contraseña en el tracking
        from funciones.tracking import registrar_evento_tracking
        registrar_evento_tracking(
            user_id=user_id,
            tipo_evento='cambio_password',
            detalles="Contraseña actualizada"
        )
        
        return jsonify({"success": ok, "message": msg}), status
    except Exception as e:
        print(f"Error al cambiar contraseña: {e}")
        return jsonify({
            "success": False,
            "message": f"Error interno del servidor: {str(e)}"
        }), 500

@app.route('/puerta')
@login_required
@nfc_required
def puerta():
    puertas = obtener_todas_puertas()
    return render_template('admin/puerta.html', puertas=puertas)

@app.route('/permisos')
@login_required
@nfc_required
def permisos():
    """
    Muestra la página de gestión de permisos con datos reales de la base de datos
    """
    try:
        # Importar la función para obtener permisos
        import bdd.permisos as permisos_db
        from flask import session
        from bdd.roles import obtener_flag_asignar_permisos_por_usuario
        
        # Obtener todos los permisos de la base de datos
        permisos = permisos_db.obtener_todos_los_permisos()
        
        # Obtener puertas disponibles para el filtro
        puertas = permisos_db.obtener_puertas_disponibles()
        
        # Verificar si el usuario es administrador (ID 1)
        user_id = session.get('user_id')
        is_admin = (user_id == 1) if user_id else False
        can_assign_permissions = False
        if user_id and not is_admin:
            try:
                can_assign_permissions = obtener_flag_asignar_permisos_por_usuario(user_id)
            except Exception as e:
                print(f"[WARN] No se pudo obtener can_assign_permissions: {e}")
        
        return render_template('admin/permisos.html', 
                             permisos=permisos, 
                             puertas=puertas,
                             is_admin=is_admin,
                             user_id=user_id,
                             can_assign_permissions=can_assign_permissions)
        
    except Exception as e:
        print(f"Error al obtener permisos: {e}")
        return render_template('admin/permisos.html', permisos=[], puertas=[])

# API endpoints para permisos

@app.route('/api/buscar-usuario', methods=['POST'])
@login_required
@nfc_required
def api_buscar_usuario():
    """
    API endpoint para buscar un usuario por DNI
    """
    try:
        import bdd.permisos as permisos_db
        data = request.get_json()
        dni = data.get('dni')
        
        if not dni:
            return jsonify({'success': False, 'error': 'DNI requerido'})
        
        usuario = permisos_db.buscar_usuario_por_dni(dni)
        
        if usuario:
            return jsonify({
                'success': True, 
                'usuario': {
                    'id_user': usuario['id_user'],
                    'nombre': usuario['nombre'],
                    'apellido': usuario['apellido'],
                    'dni': usuario['dni']
                }
            })
        else:
            return jsonify({'success': False, 'error': 'Usuario no encontrado'})
            
    except Exception as e:
        print(f"Error al buscar usuario: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/buscar-usuarios-autocompletar', methods=['GET'])
@login_required
@nfc_required
def api_buscar_usuarios_autocompletar():
    """
    API endpoint para autocompletado de usuarios por DNI, nombre, apellido o email (usando LIKE)
    """
    try:
        import bdd.permisos as permisos_db
        search_term = request.args.get('search', '').strip()
        
        if not search_term or len(search_term) < 2:
            return jsonify({'success': True, 'usuarios': []})
        
        # Buscar usuarios que coincidan con el término de búsqueda en DNI, nombre, apellido o email
        usuarios = permisos_db.buscar_usuarios_por_campo(search_term)
        
        # Formatear los datos para el frontend
        usuarios_formateados = []
        for usuario in usuarios:
            usuarios_formateados.append({
                'id_user': usuario['id_user'],
                'nombre': usuario['nombre'],
                'apellido': usuario['apellido'],
                'dni': usuario['dni'],
                'nombre_completo': f"{usuario['nombre']} {usuario['apellido']}"
            })
        
        return jsonify({'success': True, 'usuarios': usuarios_formateados})
            
    except Exception as e:
        print(f"Error al buscar usuarios para autocompletar: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/crear-permiso', methods=['POST'])
@login_required
@nfc_required
def api_crear_permiso():
    """
    API endpoint para crear un nuevo permiso
    """
    try:
        import bdd.permisos as permisos_db
        data = request.get_json()
        print(f"Received request data: {data}")
        
        id_user = data.get('id_user')
        id_puerta = data.get('id_puerta')
        tiempo_minutos = data.get('tiempo_minutos')
        
        print(f"Extracted values - id_user: {id_user}, id_puerta: {id_puerta}, tiempo_minutos: {tiempo_minutos} (type: {type(tiempo_minutos)})")
        
        if not all([id_user, id_puerta, tiempo_minutos is not None]):
            missing = []
            if not id_user: missing.append('id_user')
            if not id_puerta: missing.append('id_puerta')
            if tiempo_minutos is None: missing.append('tiempo_minutos')
            print(f"Missing required fields: {', '.join(missing)}")
            return jsonify({'success': False, 'error': 'Faltan datos requeridos', 'missing': missing})
        
        # Obtener ID del admin actual (en producción vendría de la sesión)
        id_admin = permisos_db.obtener_id_admin_actual()
        print(f"Admin ID: {id_admin}")
        
        resultado = permisos_db.crear_permiso_completo(id_user, id_puerta, tiempo_minutos, id_admin)
        print(f"Result from crear_permiso_completo: {resultado}")
        
        if resultado:
            return jsonify({'success': True, 'message': 'Permiso creado exitosamente'})
        else:
            return jsonify({'success': False, 'error': 'Error al crear el permiso'})
            
    except Exception as e:
        print(f"Error al crear permiso: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/actividad')
@login_required
@nfc_required
def actividad():
    from flask import session
    from bdd.roles import obtener_flag_asignar_permisos_por_usuario
    user_id = session.get('user_id')
    is_admin = (user_id == 1)
    can_assign_permissions = False
    if user_id and not is_admin:
        try:
            can_assign_permissions = obtener_flag_asignar_permisos_por_usuario(user_id)
        except Exception as e:
            print(f"[WARN] No se pudo obtener can_assign_permissions: {e}")
    return render_template('admin/actividad.html', user_id=user_id, is_admin=is_admin, can_assign_permissions=can_assign_permissions)

@app.route('/admin/prueba')
@login_required
@nfc_required
def admin_prueba():
    return render_template('admin/prueba.html')

# API endpoints para actividades
@app.route('/api/actividades')
@login_required
@nfc_required
def api_actividades():
    """API endpoint para obtener actividades recientes"""
    try:
        import bdd.actividades_recientes as actividades
        from flask import session, request
        
        # Obtener parámetros de la solicitud
        limit = request.args.get('limit', default=10, type=int)
        tipo = request.args.get('tipo', default=None, type=str)
        
        # Obtener el ID del usuario de la sesión
        user_id = session.get('user_id')
        
        # Obtener actividades con los filtros aplicados
        actividades_list = actividades.obtener_actividades_recientes(
            limite=limit, 
            user_id=user_id,
            tipo=tipo
        )
        
        return jsonify({
            'success': True,
            'data': actividades_list
        })
    except Exception as e:
        print(f"Error en api_actividades: {e}")
        return jsonify({
            'success': False,
            'message': 'Error al obtener actividades',
            'error': str(e)
        }), 500

@app.route('/api/actividades/estadisticas')
@login_required
@nfc_required
def api_estadisticas_actividades():
    """API endpoint para obtener estadísticas de actividades"""
    try:
        import bdd.actividades_recientes as actividades
        from flask import session
        
        # Obtener el ID del usuario de la sesión
        user_id = session.get('user_id')
        
        # Obtener estadísticas
        estadisticas = actividades.obtener_estadisticas_actividades(user_id=user_id)
        
        # Formatear último acceso si existe
        ultimo_acceso = None
        if estadisticas.get('ultimo_acceso'):
            ultimo_acceso = {
                'puerta': estadisticas['ultimo_acceso'].get('puerta', 'Desconocida'),
                'hora': estadisticas['ultimo_acceso'].get('fecha_hora', '').strftime('%H:%M') if estadisticas['ultimo_acceso'].get('fecha_hora') else 'Nunca'
            }
        
        return jsonify({
            'success': True,
            'data': {
                'logins_este_mes': estadisticas.get('logins_este_mes', 0),
                'accesos_puertas_este_mes': estadisticas.get('accesos_puertas_este_mes', 0),
                'ultimo_acceso': ultimo_acceso
            }
        })
    except Exception as e:
        print(f"Error en api_estadisticas_actividades: {e}")
        return jsonify({
            'success': False,
            'message': 'Error al obtener estadísticas',
            'error': str(e)
        }), 500

@app.route('/api/actividades/filtrar')
@login_required
@nfc_required
def api_actividades_filtrar():
    """API endpoint para filtrar actividades"""
    try:
        import bdd.actividades_recientes as actividades
        
        usuario_id = request.args.get('usuario_id', type=int)
        puerta_id = request.args.get('puerta_id', type=int)
        tipo_actividad = request.args.get('tipo_actividad')
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')
        
        actividades_list = actividades.filtrar_actividades(
            usuario_id=usuario_id,
            puerta_id=puerta_id,
            tipo_actividad=tipo_actividad,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin
        )
        return jsonify(actividades_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/usuarios-filtros')
@login_required
@nfc_required
def api_usuarios_filtros():
    """API endpoint para obtener usuarios para filtros"""
    try:
        import bdd.actividades_recientes as actividades
        usuarios = actividades.obtener_usuarios_para_filtros()
        return jsonify(usuarios)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/puertas-filtros')
@login_required
@nfc_required
def api_puertas_filtros():
    """API endpoint para obtener puertas para filtros"""
    try:
        import bdd.actividades_recientes as actividades
        puertas = actividades.obtener_puertas_para_filtros()
        return jsonify(puertas)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/inicioSesion')
def inicioSesión():
    return render_template('auth/login.html')

@app.route('/registro')
def registro():
    return render_template('auth/register.html')

@app.route('/login')
def login_redirect():
    return redirect(url_for('auth.login'))

@app.route('/register')
def register_redirect():
    return redirect(url_for('auth.register'))

@app.route('/cambiarClave')
def cambiarClave():
    return render_template('auth/cambiar-clave.html')

@app.route('/miPerfil')
@login_required
@nfc_required
def miPerfil():
    """
    Muestra la página de perfil del usuario con datos dinámicos desde la base de datos
    """
    try:
        # Importar la función para obtener información del usuario
        from bdd.miPerfil.miPerfil import obtener_informacion_usuario_actual, obtener_informacion_cuenta
        from flask import session
        
        # Obtener el ID del usuario actual desde la sesión
        user_id = session.get('user_id')
        
        if not user_id:
            # Si no hay user_id en sesión, redirigir al login
            return redirect(url_for('auth.login'))
        
        # Obtener información del usuario desde la base de datos
        usuario_info = obtener_informacion_usuario_actual(user_id)
        cuenta_info = obtener_informacion_cuenta(user_id)
        
        return render_template('shared/miperfil.html', 
                             usuario=usuario_info,
                             cuenta=cuenta_info)
        
    except Exception as e:
        print(f"Error al cargar perfil: {e}")
        # En caso de error, mostrar valores por defecto
        usuario_info = {
            'nombre': 'Usuario',
            'apellido': 'No disponible',
            'email': 'no-disponible@email.com'
        }
        return render_template('shared/miperfil.html', 
                             usuario=usuario_info,
                             cuenta={
                                 'miembro_desde': 'N/D',
                                 'ultimo_acceso': 'N/D',
                                 'ingresos_realizados': 0,
                                 'estado': 'N/D'
                             })

@app.route('/actividadesRecientes')
@login_required
@nfc_required
def actividadesRecientes():
    return render_template('shared/actividades-recientes.html')

@app.route('/carga')
@login_required
@nfc_required
def carga():
    return render_template('shared/carga.html')

@app.route('/usuarioCarga')
@login_required
@nfc_required
def usuarioCarga():
    return render_template('shared/usuario-carga.html')

@app.route('/errores')
@login_required
@nfc_required
def errores():
    return render_template('shared/errores.html')

@app.route('/misPermisos')
@login_required
@nfc_required
def misPermisos():
    return render_template('shared/mis-permisos.html')

@app.route('/api/mis-permisos')
@login_required
@nfc_required
def api_mis_permisos():
    """
    API endpoint para obtener los permisos del usuario actual
    """
    try:
        from bdd.permisosUsuario import obtener_permisos_usuario, obtener_usuario_actual_por_username
        from flask import session
        
        # Obtener el username de la sesión
        username = session.get('username')
        if not username:
            return jsonify({'error': 'Usuario no autenticado'}), 401
        
        # Obtener el ID del usuario actual
        user_id = obtener_usuario_actual_por_username(username)
        if not user_id:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # Obtener los permisos del usuario
        permisos = obtener_permisos_usuario(user_id)
        
        return jsonify({'success': True, 'data': permisos}), 200
        
    except Exception as e:
        print(f"Error al obtener permisos: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/puertas-disponibles')
@login_required
@nfc_required
def api_puertas_disponibles():
    """
    API endpoint para obtener todas las puertas disponibles
    """
    try:
        from bdd.permisosUsuario import obtener_todas_las_puertas
        
        puertas = obtener_todas_las_puertas()
        return jsonify({'success': True, 'data': puertas}), 200
        
    except Exception as e:
        print(f"Error al obtener puertas: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/buscar-usuario/<identifier>')
@login_required
@nfc_required
def api_buscar_usuario_identificador(identifier):
    """
    API endpoint para buscar usuario por DNI o username
    """
    try:
        from bdd.permisosUsuario import obtener_usuario_por_dni_o_username
        
        usuario = obtener_usuario_por_dni_o_username(identifier)
        if usuario:
            return jsonify({'success': True, 'data': usuario}), 200
        else:
            return jsonify({'success': False, 'message': 'Usuario no encontrado'}), 404
            
    except Exception as e:
        print(f"Error al buscar usuario: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/grabarNFC')
@login_required
@nfc_required
def grabar_nfc():
    id_useratributes = request.args.get('id_useratributes', type=int)
    if not id_useratributes:
        return "Error: ID de usuario no proporcionado", 400
    return render_template('admin/grabar-nfc.html', id_useratributes=id_useratributes)

@app.route('/actualizarNFC', methods=['POST'])
@login_required
@nfc_required
def actualizar_nfc():
    """
    Actualiza el código NFC en la base de datos para un usuario específico.
    Recibe: {id_useratributes: int, nfc_code: string}
    """
    try:
        data = request.get_json()
        id_useratributes = data.get('id_useratributes')
        
        if not id_useratributes:
            return jsonify({"success": False, "message": "ID de usuario no proporcionado"}), 400
        
        # Obtener el DNI del usuario
        dni = obtenerDNIPorID(id_useratributes)
        if not dni:
            return jsonify({"success": False, "message": "Usuario no encontrado"}), 404
        
        # Hashear el DNI para obtener el código NFC
        nfc_code = hashearDNI(dni)
        
        # Actualizar en la base de datos
        import bdd.usuarios_temporales as usuarios_temp
        success = usuarios_temp.actualizar_nfc_code(id_useratributes, nfc_code)
        
        if success:
            return jsonify({
                "success": True, 
                "message": "Código NFC actualizado exitosamente",
                "nfc_code": nfc_code
            }), 200
        else:
            return jsonify({
                "success": False, 
                "message": "Error al actualizar código NFC en la base de datos"
            }), 400
            
    except Exception as e:
        print(f"Error en actualizar_nfc: {e}")
        return jsonify({
            "success": False, 
            "message": f"Error interno del servidor: {str(e)}"
        }), 500

# Rutas para gestión de roles
@app.route('/roles')
@login_required
@nfc_required
def roles():
    """
    Muestra la página de gestión de roles con datos reales de la base de datos
    """
    return render_template('admin/roles.html')

@app.route('/roles/lista', methods=['GET'])
@login_required
@nfc_required
def get_roles():
    """
    Obtiene todos los roles de la base de datos
    """
    try:
        roles = roles_db.obtener_todos_los_roles()
        return jsonify({"success": True, "data": roles}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/roles/nuevo', methods=['POST'])
@login_required
@nfc_required
def create_role():
    """
    Crea un nuevo rol en la base de datos con sus respectivos permisos de puertas
    """
    try:
        data = request.get_json()
        nombre = data.get('nombre')
        acceso_todas_puertas = data.get('acceso_todas_puertas', False)
        asignar_permisos_usuarios = data.get('asignar_permisos_usuarios', False)
        puertas = data.get('puertas', [])
        
        if not nombre:
            return jsonify({"success": False, "message": "El nombre del rol es requerido"}), 400
        
        # Validar que si no tiene acceso a todas las puertas, se hayan proporcionado puertas
        if not acceso_todas_puertas and not puertas:
            return jsonify({
                "success": False, 
                "message": "Debe seleccionar al menos una puerta o permitir acceso a todas las puertas."
            }), 400
        
        # Crear el rol y asignar las puertas
        success, role_id = roles_db.crear_rol(
            nombre=nombre,
            acceso_todas_puertas=acceso_todas_puertas,
            asignar_permisos_usuarios=asignar_permisos_usuarios,
            puertas=puertas if not acceso_todas_puertas else None
        )
        
        if success and role_id:
            return jsonify({
                "success": True, 
                "message": "Rol creado exitosamente",
                "roleId": role_id
            }), 201
        elif not success and role_id is None:
            return jsonify({
                "success": False, 
                "message": "El rol ya existe o hubo un error al crearlo"
            }), 400
        else:
            return jsonify({
                "success": False, 
                "message": "Error al crear el rol o asignar permisos"
            }), 500
            
    except Exception as e:
        print(f"Error en create_role: {str(e)}")
        return jsonify({
            "success": False, 
            "message": f"Error en el servidor: {str(e)}"
        }), 500

@app.route('/roles/<int:id>/actualizar', methods=['PUT'])
@login_required
@nfc_required
def update_role(id):
    """
    Actualiza un rol existente
    """
    try:
        data = request.get_json()
        nombre = data.get('nombre')
        acceso_todas_puertas = data.get('acceso_todas_puertas', False)
        asignar_permisos_usuarios = data.get('asignar_permisos_usuarios', False)
        puertas = data.get('puertas', [])
        
        if not nombre:
            return jsonify({"success": False, "message": "El nombre del rol es requerido"}), 400
        
        # Actualizar el rol
        success = roles_db.actualizar_rol(
            id_rol=id,
            nombre=nombre,
            acceso_todas_puertas=acceso_todas_puertas,
            asignar_permisos_usuarios=asignar_permisos_usuarios,
            puertas=puertas
        )
        
        if success:
            return jsonify({"success": True, "message": "Rol actualizado exitosamente"}), 200
        else:
            return jsonify({"success": False, "message": "No se pudo actualizar el rol"}), 400
            
    except Exception as e:
        print(f"Error al actualizar rol: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/roles/<int:id>', methods=['DELETE'])
@login_required
def delete_role(id):
    """
    Elimina un rol de la base de datos
    Si el rol tiene usuarios asignados, se puede forzar la eliminación con el parámetro force=true
    en cuyo caso los usuarios serán reasignados al rol de usuario por defecto (ID 2)
    """
    print(f"\n=== Iniciando solicitud DELETE para rol {id} ===")
    print(f"Headers: {request.headers}")
    print(f"Args: {request.args}")
    
    try:
        # Verificar si se está forzando la eliminación
        force_delete = request.args.get('force', 'false').lower() == 'true'
        print(f"Forzar eliminación: {force_delete}")
        
        # Llamar a la función de eliminación con el parámetro de forzar
        print("Llamando a roles_db.eliminar_rol...")
        success, message = roles_db.eliminar_rol(id, force_delete)
        print(f"Resultado de eliminar_rol: success={success}, message={message}")
        
        if success:
            print("Eliminación exitosa")
            return jsonify({"success": True, "message": message}), 200
        else:
            # Si hay usuarios asignados, devolver un código especial
            if message == "existen_usuarios":
                print("El rol tiene usuarios asignados")
                return jsonify({
                    "success": False, 
                    "message": "El rol tiene usuarios asignados",
                    "code": "USERS_ASSIGNED"
                }), 400
            else:
                print(f"Error al eliminar: {message}")
                return jsonify({"success": False, "message": message}), 400
                
    except Exception as e:
        print(f"Error en la ruta delete_role: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": f"Error en el servidor: {str(e)}"}), 500
    finally:
        print("=== Fin de la solicitud DELETE ===\n")

@app.route('/roles/<int:id>')
@login_required
@nfc_required
def get_role(id):
    """
    Obtiene un rol específico por su ID
    """
    try:
        rol = roles_db.obtener_rol_por_id(id)
        
        if rol:
            return jsonify({"success": True, "data": rol}), 200
        else:
            return jsonify({"success": False, "message": "Rol no encontrado"}), 404
            
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# Rutas para gestión de puertas
@app.route('/api/puertas', methods=['POST'])
@app.route('/api/puertas/crear', methods=['POST'])
@login_required
@nfc_required
def crear_puerta_api():
    """
    Endpoint para crear una nueva puerta
    """
    try:
        # Verificar si se envió un archivo
        imagen = None
        if 'imagen' in request.files:
            imagen_file = request.files['imagen']
            if imagen_file.filename != '':
                # Guardar solo el nombre del archivo, no la ruta completa
                filename = secure_filename(imagen_file.filename)
                filepath = os.path.join('static', 'img', 'doors', filename)
                imagen_file.save(filepath)
                imagen = filename  # Solo guardamos el nombre del archivo
            
        if not request.is_json and not request.form:
            return jsonify({'success': False, 'error': 'No se recibieron datos'}), 400
            
        data = request.form.to_dict() if not request.is_json else request.get_json()
        nombre = data.get('nombre')
        
        if not nombre:
            return jsonify({'success': False, 'error': 'El nombre de la puerta es requerido'}), 400
            
        # Llamar a la función crear_puerta con los parámetros correctos
        puerta_id = puertas.crear_puerta(
            nombre=nombre,
            imagen=imagen
        )
        
        if puerta_id:
            return jsonify({
                'success': True,
                'message': 'Puerta creada exitosamente',
                'puerta_id': puerta_id,
                'imagen': imagen
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No se pudo crear la puerta en la base de datos'
            }), 500
            
    except Exception as e:
        print(f"Error en crear_puerta_api: {e}")
        return jsonify({
            'success': False,
            'error': 'Error interno del servidor al crear la puerta',
            'details': str(e)
        }), 500

@app.route('/api/puertas', methods=['GET'])
@login_required
@nfc_required
def obtener_puertas():
    """
    Obtiene todas las puertas de la base de datos
    """
    try:
        puertas = obtener_todas_puertas()
        return jsonify({"success": True, "puertas": puertas}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/puertas/<int:id>', methods=['PUT'])
@login_required
@nfc_required
def actualizar_puerta(id):
    """
    Actualiza una puerta existente
    """
    try:
        # Verificar si la solicitud es multipart/form-data (para imágenes)
        if request.content_type.startswith('multipart/form-data'):
            nombre = request.form.get('nombre')
            estado = request.form.get('estado')
            
            # Manejar la imagen si se envió
            imagen_file = request.files.get('imagen')
            imagen_nombre = None
            
            if imagen_file and imagen_file.filename:
                # Generar un nombre de archivo seguro
                filename = secure_filename(imagen_file.filename)
                # Crear un nombre único para evitar colisiones
                unique_filename = f"{uuid.uuid4().hex}_{filename}"
                # Ruta donde se guardará la imagen
                upload_folder = os.path.join(app.root_path, 'static', 'img', 'puertas')
                # Asegurarse de que el directorio exista
                os.makedirs(upload_folder, exist_ok=True)
                # Guardar el archivo
                filepath = os.path.join(upload_folder, unique_filename)
                imagen_file.save(filepath)
                # Guardar solo la ruta relativa en la base de datos
                imagen_nombre = f"img/puertas/{unique_filename}"
        else:
            # Manejo para JSON (mantener compatibilidad)
            data = request.get_json()
            nombre = data.get('nombre')
            estado = data.get('estado')
            imagen_nombre = data.get('imagen')
        
        if not nombre:
            return jsonify({"success": False, "message": "El nombre de la puerta es requerido"}), 400
        
        # Actualizar la puerta en la base de datos
        success = puertas.actualizar_puerta(id, nombre, estado, imagen_nombre)
        
        if success:
            return jsonify({"success": True, "message": "Puerta actualizada exitosamente"}), 200
        else:
            return jsonify({"success": False, "message": "No se pudo actualizar la puerta"}), 400
            
    except Exception as e:
        print(f"Error al actualizar la puerta: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/puertas/<int:id>', methods=['DELETE'])
@login_required
@nfc_required
def eliminar_puerta(id):
    """
    Elimina una puerta de la base de datos
    """
    try:
        print(f"Solicitud para eliminar puerta con ID: {id}")
        
        # Verificar que la puerta existe antes de intentar eliminarla
        puerta = puertas.obtener_puerta_por_id(id)
        if not puerta:
            return jsonify({
                "success": False, 
                "message": f"No se encontró la puerta con ID {id}"
            }), 404
            
        # Verificar si hay registros relacionados que podrían causar problemas
        try:
            # Intentar eliminar la puerta
            success = puertas.eliminar_puerta(id)
            
            if success:
                print(f"Puerta con ID {id} eliminada exitosamente")
                return jsonify({
                    "success": True, 
                    "message": "Puerta eliminada exitosamente"
                }), 200
            else:
                print(f"No se pudo eliminar la puerta con ID {id}")
                return jsonify({
                    "success": False, 
                    "message": "No se pudo eliminar la puerta. La puerta podría no existir o ya haber sido eliminada."
                }), 400
                
        except mysql.connector.Error as e:
            if e.errno == 1451:  # Error de restricción de clave foránea
                print(f"No se puede eliminar la puerta ID {id} porque tiene registros relacionados")
                return jsonify({
                    "success": False,
                    "message": "No se puede eliminar la puerta porque tiene registros de actividad asociados. Por favor, contacte al administrador del sistema."
                }), 400
            else:
                raise  # Relanzar otros errores
            
    except Exception as e:
        print(f"Error al procesar la solicitud de eliminación: {str(e)}")
        return jsonify({
            "success": False, 
            "message": f"Error al procesar la solicitud: {str(e)}"
        }), 500

@app.route('/api/puertas/<int:id>')
@login_required
@nfc_required
def obtener_puerta(id):
    """
    Obtiene una puerta específica por su ID
    """
    try:
        puerta = puertas.obtener_puerta_por_id(id)
        
        if puerta:
            return jsonify({
                "success": True,
                "id": puerta['id'],
                "nombre": puerta['nombre'],
                "estado": puerta['estado'],
                "imagen": puerta['imagen']
            }), 200
        else:
            return jsonify({"success": False, "message": "Puerta no encontrada"}), 404
            
    except Exception as e:
        print(f"Error al obtener puerta: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/puertas/<int:id>/usuarios')
@login_required
@nfc_required
def obtener_usuarios_puerta(id):
    """
    Obtiene todos los usuarios que tienen acceso a una puerta específica
    """
    try:
        usuarios = puertas.obtener_usuarios_con_acceso_puerta(id)
        
        return jsonify({
            "success": True,
            "usuarios": usuarios,
            "total": len(usuarios)
        }), 200
            
    except Exception as e:
        print(f"Error al obtener usuarios de puerta {id}: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/usuarios/<int:user_id>/actualizar-rol', methods=['PUT'])
@login_required
@nfc_required
def api_actualizar_rol_usuario(user_id):
    """
    API endpoint para actualizar el rol de un usuario
    """
    try:
        data = request.get_json()
        id_rol = data.get('id_rol')
        
        if not id_rol:
            return jsonify({"success": False, "message": "El ID del rol es requerido"}), 400
            
        # Actualizar el rol del usuario
        if actualizar_rol_usuario(user_id, id_rol):
            return jsonify({
                "success": True, 
                "message": "Rol actualizado correctamente"
            }), 200
        else:
            return jsonify({
                "success": False, 
                "message": "No se pudo actualizar el rol del usuario. Verifique que el usuario y el rol existan."
            }), 400
            
    except Exception as e:
        print(f"Error al actualizar rol del usuario: {str(e)}")
        return jsonify({
            "success": False, 
            "message": f"Error al actualizar el rol: {str(e)}"
        }), 500

# API endpoint para actualizar información del usuario
@app.route('/api/miPerfil/actualizar', methods=['POST'])
@login_required
@nfc_required
def actualizar_perfil():
    """
    Actualiza la información personal del usuario
    """
    try:
        from bdd.miPerfil.miPerfil import actualizar_informacion_usuario
        
        data = request.get_json()
        from flask import session
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({
                "success": False, 
                "message": "Usuario no autenticado"
            }), 401
            
        nombre = data.get('nombre')
        apellido = data.get('apellido')
        email = data.get('email')
        
        if not all([nombre, apellido, email]):
            return jsonify({
                "success": False, 
                "message": "Todos los campos son requeridos"
            }), 400
        
        success = actualizar_informacion_usuario(user_id, nombre, apellido, email)
        
        if success:
            return jsonify({
                "success": True, 
                "message": "Información actualizada exitosamente"
            }), 200
        else:
            return jsonify({
                "success": False, 
                "message": "Error al actualizar la información"
            }), 400
            
    except Exception as e:
        print(f"Error al actualizar perfil: {e}")
        return jsonify({
            "success": False, 
            "message": f"Error interno del servidor: {str(e)}"
        }), 500

@app.route('/api/usuarios/<int:user_id>', methods=['PUT'])
@login_required
def api_actualizar_usuario(user_id):
    """
    Actualiza los datos de un usuario existente
    """
    try:
        data = request.get_json()
        
        # Validar datos requeridos
        required_fields = ['nombre', 'apellido', 'dni', 'rol']
        if not all(field in data for field in required_fields):
            return jsonify({
                'success': False,
                'message': 'Faltan campos requeridos'
            }), 400
        
        # Obtener el ID del rol a partir del nombre
        from bdd.roles import obtener_rol_por_nombre
        rol = obtener_rol_por_nombre(data['rol'].capitalize())
        
        if not rol:
            return jsonify({
                'success': False,
                'message': 'Rol no válido'
            }), 400
        
        # Actualizar el usuario
        from bdd.usuarios import actualizar_usuario
        
        # Preparar los datos en el formato que espera la función
        datos_actualizacion = {
            'nombre': data['nombre'],
            'apellido': data['apellido'],
            'dni': data['dni'],
            'exit_permit': False,  # Valor por defecto, puedes ajustarlo según sea necesario
            'id_rol': rol['id']
        }
        
        resultado = actualizar_usuario(user_id, datos_actualizacion)
        
        if resultado:
            return jsonify({
                'success': True,
                'message': 'Usuario actualizado correctamente',
                'data': {
                    'id': user_id,
                    'nombre': data['nombre'],
                    'apellido': data['apellido'],
                    'dni': data['dni'],
                    'rol': data['rol']
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No se pudo actualizar el usuario en la base de datos'
            }), 500
            
    except Exception as e:
        print(f"Error al actualizar usuario: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error al actualizar el usuario: {str(e)}'
        }), 500

@app.route('/eliminarUsuario/<int:user_id>', methods=['DELETE'])
@login_required
@nfc_required
def eliminar_usuario(user_id):
    """
    Elimina un usuario de la base de datos.
    Realiza un hard delete eliminando completamente el registro de User y UserAtributes.
    """
    try:
        from bdd.usuarios import obtener_usuario_por_id, eliminar_usuario_completo
        
        # Verificar si el usuario existe
        usuario = obtener_usuario_por_id(user_id)
        if not usuario:
            return jsonify({"success": False, "message": "Usuario no encontrado"}), 404
            
        # Eliminar el usuario
        result = eliminar_usuario_completo(user_id)
        
        if result:
            return jsonify({
                "success": True, 
                "message": "Usuario eliminado exitosamente"
            })
        else:
            return jsonify({
                "success": False, 
                "message": "Error al eliminar el usuario"
            }), 500
            
    except Exception as e:
        print(f"Error en eliminar_usuario: {str(e)}")
        return jsonify({
            "success": False, 
            "message": f"Error del servidor: {str(e)}"
        }), 500

# MSN
"""
MSN
"""
# NFC Configurator routes
@app.route('/configurador-nfc')
@login_required
@nfc_required
def configurador_nfc():
    """Página del configurador NFC WiFi"""
    return render_template('admin/configurador-nfc.html')

# NFC API routes
@app.route('/api/nfc/ports')
@login_required
@nfc_required
def api_nfc_ports():
    """Obtener puertos seriales disponibles"""
    try:
        from nfc_configurador.serial_handler import find_esp32_ports
        ports = find_esp32_ports()
        return jsonify(ports)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/nfc/connect', methods=['POST'])
@login_required
@nfc_required
def api_nfc_connect():
    """Conectar al ESP32 por puerto serial"""
    try:
        from nfc_configurador.serial_handler import connect_serial
        data = request.get_json()
        port = data.get('port')
        
        if not port:
            return jsonify({'success': False, 'error': 'Puerto requerido'})
        
        result = connect_serial(port)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/nfc/disconnect', methods=['POST'])
@login_required
@nfc_required
def api_nfc_disconnect():
    """Desconectar del ESP32"""
    try:
        from nfc_configurador.serial_handler import disconnect_serial
        result = disconnect_serial()
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/nfc/status')
@login_required
@nfc_required
def api_nfc_status():
    """Obtener estado del ESP32"""
    try:
        from nfc_configurador.serial_handler import get_status
        status = get_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/nfc/scan-wifi', methods=['POST'])
@login_required
@nfc_required
def api_nfc_scan_wifi():
    """Escanear redes WiFi disponibles"""
    try:
        from nfc_configurador.serial_handler import scan_wifi
        result = scan_wifi()
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/nfc/configure-wifi', methods=['POST'])
@login_required
@nfc_required
def api_nfc_configure_wifi():
    """Configurar WiFi en el ESP32"""
    try:
        from nfc_configurador.serial_handler import configure_wifi
        data = request.get_json()
        
        ssid = data.get('ssid')
        password = data.get('password')
        server_ip = data.get('serverIP', '192.168.1.12')
        server_port = data.get('serverPort', '5000')
        
        if not ssid or not password:
            return jsonify({'success': False, 'error': 'SSID y contraseña requeridos'})
        
        result = configure_wifi(ssid, password, server_ip, server_port)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/nfc/test-connection', methods=['POST'])
@login_required
@nfc_required
def api_nfc_test_connection():
    """Probar conexión del ESP32"""
    try:
        from nfc_configurador.serial_handler import test_connection
        result = test_connection()
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/nfc/clear-wifi', methods=['POST'])
@login_required
@nfc_required
def api_nfc_clear_wifi():
    """Borrar configuración WiFi del ESP32"""
    try:
        from nfc_configurador.serial_handler import clear_wifi
        result = clear_wifi()
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/nfc/messages')
@login_required
@nfc_required
def api_nfc_messages():
    """Obtener mensajes del ESP32"""
    try:
        from nfc_configurador.serial_handler import get_messages
        messages = get_messages()
        return jsonify(messages)
    except Exception as e:
        return jsonify([]), 500

def get_db_connection():
    """
    Obtiene una conexión a la base de datos con manejo de errores
    """
    try:
        # Verificar si la conexión existe y está activa
        if mysql.connection is None:
            # Intentar reconectar
            logger.warning("MySQL connection is None, attempting to reconnect...")
            # Crear conexión manual si la automática falla
            connection = MySQLdb.connect(
                host=app.config['MYSQL_HOST'],
                user=app.config['MYSQL_USER'],
                passwd=app.config['MYSQL_PASSWORD'],
                db=app.config['MYSQL_DB'],
                cursorclass=MySQLdb.cursors.DictCursor
            )
            return connection
        else:
            # Verificar que la conexión esté viva
            mysql.connection.ping(reconnect=True)
            return mysql.connection
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        # Intentar conexión directa como fallback
        try:
            connection = MySQLdb.connect(
                host=app.config['MYSQL_HOST'],
                user=app.config['MYSQL_USER'],
                passwd=app.config['MYSQL_PASSWORD'],
                db=app.config['MYSQL_DB'],
                cursorclass=MySQLdb.cursors.DictCursor
            )
            logger.info("Direct database connection established")
            return connection
        except Exception as e2:
            logger.critical(f"Failed to establish database connection: {str(e2)}")
            return None

def check_debounce(nfc_code, sensor_id):
    """Verifica si el scan está dentro del período de debounce"""
    key = f"{nfc_code}_{sensor_id}"
    current_time = time.time()
    
    if key in scan_cache:
        if current_time - scan_cache[key] < CONFIG['DEBOUNCE_SECONDS']:
            return True  # Está en debounce, ignorar
    
    scan_cache[key] = current_time
    # Limpiar cache antiguo
    for k in list(scan_cache.keys()):
        if current_time - scan_cache[k] > 60:  # Limpiar entradas > 1 minuto
            del scan_cache[k]
    
    return False

@app.route('/api/scan', methods=['POST'])
@require_api_key
def process_scan():
    """
    Procesa un escaneo NFC
    Payload esperado: {
        "nfc_code": "XXXX",
        "door_id": 1,
        "sensor": 1 (exterior) o 2 (interior)
    }
    """
    connection = None
    cur = None
    try:
        data = request.json
        nfc_code = data.get('nfc_code')
        door_id = data.get('door_id')
        sensor = data.get('sensor')  # 1=exterior, 2=interior
        
        if not all([nfc_code, door_id, sensor]):
            return jsonify({
                'status': False,
                'message': 'Missing required parameters'
            }), 400
        
        # Verificar debounce
        if check_debounce(nfc_code, sensor):
            return jsonify({
                'status': False,
                'message': 'Scan ignored (debounce)',
                'action': 'none'
            }), 429
        
        # Obtener conexión a la base de datos
        connection = get_db_connection()
        if connection is None:
            logger.error("Database connection unavailable")
            return jsonify({
                'status': False,
                'message': 'Database connection error',
                'action': 'deny'
            }), 503
        
        cur = connection.cursor()
        
        # Buscar usuario por NFC
        cur.execute("""
            SELECT ua.*, u.username, u.user_status, r.role
            FROM UserAtributes ua
            JOIN User u ON ua.ID_user = u.ID_user
            LEFT JOIN Role r ON ua.ID_role = r.ID_role
            WHERE ua.nfc_code = %s
        """, (nfc_code,))
        user = cur.fetchone()
        
        # Si no existe el usuario, registrar y denegar
        if not user:
            cur.execute("""
                INSERT INTO Activity (ID_useratributes, ID_door, activity_details)
                VALUES (NULL, %s, %s)
            """, (door_id, f"Unknown NFC: {nfc_code}"))
            connection.commit()
            
            logger.warning(f"Unknown NFC scanned: {nfc_code} at door {door_id}")
            
            return jsonify({
                'status': False,
                'message': 'Unknown NFC',
                'action': 'deny'
            }), 403
        
        # Verificar si el usuario está activo
        if not user['user_status']:
            return jsonify({
                'status': False,
                'message': 'User inactive',
                'action': 'deny'
            }), 403
        
        # Obtener estado actual de la puerta
        cur.execute("SELECT door_isOpen FROM Door WHERE ID_door = %s", (door_id,))
        door = cur.fetchone()
        door_is_open = door['door_isOpen'] if door else False
        
        # LÓGICA DE ENTRADA (sensor exterior = 1)
        if sensor == 1:
            # Verificar permisos de entrada
            cur.execute("""
                SELECT 1 FROM UserDoorPermit 
                WHERE ID_user = %s AND ID_door = %s
                UNION
                SELECT 1 FROM RoleDoorPermit 
                WHERE ID_role = %s AND ID_door = %s
            """, (user['ID_user'], door_id, user['ID_role'], door_id))
            
            has_permission = cur.fetchone() is not None
            
            if has_permission:
                # Tiene permiso, abrir puerta
                action = 'unlock'
                message = 'Access granted'
                
                # Registrar entrada
                cur.execute("""
                    INSERT INTO Activity (ID_useratributes, ID_door, activity_details)
                    VALUES (%s, %s, 'Entrada autorizada')
                """, (user['ID_useratributes'], door_id))
                
                # Registrar en tracking
                cur.execute("""
                    INSERT INTO Tracking (ID_useratributes, type, track_details)
                    VALUES (%s, 'ENTRY', %s)
                """, (user['ID_useratributes'], f'Door {door_id} - Authorized entry'))
                
            elif door_is_open:
                # No tiene permiso pero puerta abierta, crear exit_permit
                action = 'allow_pass'
                message = 'Passage allowed, exit permit created'
                
                # Actualizar exit_permit
                cur.execute("""
                    UPDATE UserAtributes 
                    SET exit_permit = TRUE 
                    WHERE ID_useratributes = %s
                """, (user['ID_useratributes'],))
                
                # Registrar actividad
                cur.execute("""
                    INSERT INTO Activity (ID_useratributes, ID_door, activity_details)
                    VALUES (%s, %s, 'Entrada sin permiso - Puerta abierta - Exit permit creado')
                """, (user['ID_useratributes'], door_id))
                
                # Registrar en tracking
                cur.execute("""
                    INSERT INTO Tracking (ID_useratributes, type, track_details)
                    VALUES (%s, 'ENTRY_NO_PERM', %s)
                """, (user['ID_useratributes'], f'Door {door_id} - Entry without permission, exit permit granted'))
                
            else:
                # No tiene permiso y puerta cerrada, denegar
                action = 'deny'
                message = 'Access denied'
                
                # Registrar intento fallido
                cur.execute("""
                    INSERT INTO Activity (ID_useratributes, ID_door, activity_details)
                    VALUES (%s, %s, 'Entrada denegada - Sin permisos')
                """, (user['ID_useratributes'], door_id))


        # LÓGICA DE SALIDA (sensor interior = 2)
        elif sensor == 2:
            # Verificar permisos de usuario/rol para la puerta
            cur.execute("""
                SELECT 1 FROM UserDoorPermit 
                WHERE ID_user = %s AND ID_door = %s
                UNION
                SELECT 1 FROM RoleDoorPermit 
                WHERE ID_role = %s AND ID_door = %s
            """, (user['ID_user'], door_id, user['ID_role'], door_id))
            
            has_permission = cur.fetchone() is not None

            if user['exit_permit'] or has_permission:
                # Tiene exit_permit o permisos -> permitir salida
                action = 'unlock'
                message = 'Exit authorized'

                # Si tenía exit_permit, lo removemos
                if user['exit_permit']:
                    cur.execute("""
                        UPDATE UserAtributes 
                        SET exit_permit = FALSE 
                        WHERE ID_useratributes = %s
                    """, (user['ID_useratributes'],))

                # Registrar salida
                cur.execute("""
                    INSERT INTO Activity (ID_useratributes, ID_door, activity_details)
                    VALUES (%s, %s, 'Salida autorizada')
                """, (user['ID_useratributes'], door_id))

                # Registrar en tracking
                cur.execute("""
                    INSERT INTO Tracking (ID_useratributes, type, track_details)
                    VALUES (%s, 'EXIT', %s)
                """, (user['ID_useratributes'], f'Door {door_id} - Authorized exit'))

            else:
                # No tiene permisos ni exit_permit, denegar
                action = 'deny'
                message = 'Exit denied - No exit permit or permission'

                # Registrar intento fallido
                cur.execute("""
                    INSERT INTO Activity (ID_useratributes, ID_door, activity_details)
                    VALUES (%s, %s, 'Salida denegada - Sin permisos ni exit permit')
                """, (user['ID_useratributes'], door_id))
        
        connection.commit()
        
        logger.info(f"Scan processed: User {user['username']}, Door {door_id}, Sensor {sensor}, Action: {action}")
        
        return jsonify({
            'status': True,
            'message': message,
            'action': action,
            'user': user['username'] if user else None,
            'timeout': CONFIG['DOOR_TIMEOUT_SECONDS'] if action == 'unlock' else None
        })
        
    except Exception as e:
        logger.error(f"Error processing scan: {str(e)}")
        if connection:
            connection.rollback()
        return jsonify({
            'status': False,
            'message': 'Internal server error',
            'action': 'deny'
        }), 500
    finally:
        if cur:
            cur.close()
        # Si usamos una conexión directa, cerrarla
        if connection and connection != mysql.connection:
            connection.close()

@app.route('/api/door/status', methods=['POST'])
@require_api_key
def update_door_status():
    """
    Actualiza el estado de la puerta basado en el sensor MC31
    Payload: {
        "door_id": 1,
        "is_open": true/false
    }
    """
    connection = None
    cur = None
    try:
        data = request.json
        door_id = data.get('door_id')
        is_open = data.get('is_open')
        
        if door_id is None or is_open is None:
            return jsonify({'status': False, 'message': 'Missing parameters'}), 400
        
        # Obtener conexión a la base de datos
        connection = get_db_connection()
        if connection is None:
            logger.error("Database connection unavailable")
            return jsonify({
                'status': False,
                'message': 'Database connection error'
            }), 503
        
        cur = connection.cursor()
        
        # Actualizar estado de la puerta
        cur.execute("""
            UPDATE Door 
            SET door_isOpen = %s 
            WHERE ID_door = %s
        """, (is_open, door_id))
        
        # Registrar en historial
        cur.execute("""
            INSERT INTO DoorStateHistory (ID_door, state)
            VALUES (%s, %s)
        """, (door_id, is_open))
        
        connection.commit()
        
        logger.info(f"Door {door_id} status updated: {'OPEN' if is_open else 'CLOSED'}")
        
        return jsonify({
            'status': True,
            'message': 'Door status updated',
            'door_id': door_id,
            'is_open': is_open
        })
        
    except Exception as e:
        logger.error(f"Error updating door status: {str(e)}")
        if connection:
            connection.rollback()
        return jsonify({'status': False, 'message': 'Internal server error'}), 500
    finally:
        if cur:
            cur.close()
        # Si usamos una conexión directa, cerrarla
        if connection and connection != mysql.connection:
            connection.close()

@app.route('/api/door/timeout', methods=['POST'])
@require_api_key
def handle_door_timeout():
    """
    Maneja el timeout de una puerta que no se cerró
    """
    connection = None
    cur = None
    try:
        data = request.json
        door_id = data.get('door_id')
        
        # Obtener conexión a la base de datos
        connection = get_db_connection()
        if connection is None:
            logger.error("Database connection unavailable")
            return jsonify({
                'status': False,
                'message': 'Database connection error'
            }), 503
        
        cur = connection.cursor()
        
        # Registrar timeout en tracking
        cur.execute("""
            INSERT INTO Tracking (ID_useratributes, type, track_details)
            VALUES (NULL, 'DOOR_TIMEOUT', %s)
        """, (f'Door {door_id} - Timeout after {CONFIG["DOOR_TIMEOUT_SECONDS"]} seconds',))
        
        # Actualizar estado de puerta a cerrada (asumiendo que el relé se desactivó)
        cur.execute("""
            UPDATE Door 
            SET door_isOpen = FALSE 
            WHERE ID_door = %s
        """, (door_id,))
        
        connection.commit()
        
        logger.warning(f"Door {door_id} timeout - Relay released")
        
        return jsonify({
            'status': True,
            'message': 'Timeout registered',
            'door_id': door_id
        })
        
    except Exception as e:
        logger.error(f"Error handling timeout: {str(e)}")
        if connection:
            connection.rollback()
        return jsonify({'status': False, 'message': 'Internal server error'}), 500
    finally:
        if cur:
            cur.close()
        # Si usamos una conexión directa, cerrarla
        if connection and connection != mysql.connection:
            connection.close()

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    # Verificar también la conexión a la base de datos
    db_status = 'healthy'
    connection = None
    try:
        connection = get_db_connection()
        if connection is None:
            db_status = 'unavailable'
        else:
            # Hacer una consulta simple para verificar
            cur = connection.cursor()
            cur.execute("SELECT 1")
            cur.close()
    except Exception as e:
        db_status = f'error: {str(e)}'
    finally:
        if connection and connection != mysql.connection:
            connection.close()
    
    return jsonify({
        'status': 'healthy',
        'database': db_status,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/admin/enroll', methods=['POST'])
@require_api_key
def enroll_user():
    """
    Endpoint para enrolar un nuevo usuario (admin only)
    """
    connection = None
    cur = None
    try:
        data = request.json
        
        # Validar datos requeridos
        required = ['username', 'mail', 'password', 'nfc_code', 'name', 'surname', 'dni', 'role_id']
        if not all(k in data for k in required):
            return jsonify({'status': False, 'message': 'Missing required fields'}), 400
        
        # Obtener conexión a la base de datos
        connection = get_db_connection()
        if connection is None:
            logger.error("Database connection unavailable")
            return jsonify({
                'status': False,
                'message': 'Database connection error'
            }), 503
        
        cur = connection.cursor()
        
        # Hash de la contraseña
        password_hash = hashlib.sha256(data['password'].encode()).hexdigest()
        
        # Crear usuario
        cur.execute("""
            INSERT INTO User (mail, username, password)
            VALUES (%s, %s, %s)
        """, (data['mail'], data['username'], password_hash))
        
        user_id = cur.lastrowid
        
        # Crear atributos de usuario
        cur.execute("""
            INSERT INTO UserAtributes (ID_user, ID_role, name, surname, dni, nfc_code)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (user_id, data['role_id'], data['name'], data['surname'], data['dni'], data['nfc_code']))
        
        connection.commit()
        
        logger.info(f"New user enrolled: {data['username']}")
        
        return jsonify({
            'status': True,
            'message': 'User enrolled successfully',
            'user_id': user_id
        })
        
    except Exception as e:
        logger.error(f"Error enrolling user: {str(e)}")
        if connection:
            connection.rollback()
        return jsonify({'status': False, 'message': str(e)}), 500
    finally:
        if cur:
            cur.close()
        # Si usamos una conexión directa, cerrarla
        if connection and connection != mysql.connection:
            connection.close()

# Escritor NFC
@app.route('/iniciarGrabacionNFC', methods=['POST'])
def iniciar_grabacion_nfc():
    """Iniciar el proceso de grabación NFC - llamado por el frontend"""
    global nfc_state
    
    try:
        data = request.get_json()
        id_useratributes = data.get('id_useratributes')
        
        print(f"\n=== INICIANDO PROCESO DE GRABACIÓN NFC ===")
        print(f"[iniciar_grabacion_nfc] ID UserAtributes recibido: {id_useratributes}")
        
        if not id_useratributes:
            print("ERROR: ID de usuario no proporcionado")
            return jsonify({'error': 'ID de usuario no proporcionado'}), 400
        
        # Obtener DNI del usuario
        dni = obtenerDNIPorID(id_useratributes)
        print(f"[iniciar_grabacion_nfc] DNI obtenido de la base de datos: '{dni}'")
        
        if not dni:
            print("ERROR: No se pudo obtener el DNI del usuario")
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # Generar hash determinístico
        hash_code = hashearDNI(dni)
        print(f"[iniciar_grabacion_nfc] Hash generado para DNI '{dni}': {hash_code}")
        
        if not hash_code:
            print("ERROR: No se pudo generar el hash del DNI")
            return jsonify({'error': 'Error al generar el código NFC'}), 500
        
        # Actualizar estado global
        nfc_state = {
            'usuario_id': id_useratributes,
            'hash_code': hash_code,
            'uid_detectado': None,
            'estado_actual': 'waiting',  # Estado inicial: esperando tarjeta
            'mensaje': 'Acerque la tarjeta NFC al lector',
            'timestamp': time.time(),
            'esperando_tag': True,
            'proceso_completado': False
        }
        
        print(f"[iniciar_grabacion_nfc] Estado NFC actualizado: {nfc_state}")
        
        return jsonify({
            'success': True,
            'message': 'Proceso iniciado correctamente',
            'hash_code': hash_code
        }), 200
        
    except Exception as e:
        print(f"ERROR CRÍTICO en iniciar_grabacion_nfc: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error interno: {str(e)}'}), 500

@app.route('/enviarNFC', methods=['GET'])
def enviar_nfc():
    """
    El ESP32 llama a esta ruta para obtener el código a escribir.
    NO recibe parámetros, usa el estado global.
    """
    global nfc_state
    
    try:
        # Verificar si hay un proceso activo
        if not nfc_state['esperando_tag'] or not nfc_state['hash_code']:
            print("INFO: No hay proceso de grabación activo")
            return "NO_DATA", 204  # No content
        
        hash_code = nfc_state['hash_code']
        print(f"\n=== ENVIANDO HASH AL ESP32 ===")
        print(f"[enviar_nfc] Hash a enviar: {hash_code}")
        print(f"[enviar_nfc] Longitud del hash: {len(hash_code)} caracteres")
        
        # Validar el hash antes de enviarlo
        if not isinstance(hash_code, str):
            print(f"ERROR: El hash_code no es una cadena: {type(hash_code)}")
            return "INVALID_HASH", 400
            
        if not hash_code.isalnum():
            print(f"ADVERTENCIA: El hash_code contiene caracteres no alfanuméricos: {hash_code}")
        
        # Asegurar que tenga exactamente 16 caracteres
        if len(hash_code) < 16:
            print(f"ADVERTENCIA: El hash_code tiene menos de 16 caracteres: {len(hash_code)}")
            # Rellenar con espacios o caracteres de relleno si es necesario
            hash_code = hash_code.ljust(16, '0')
            print(f"[enviar_nfc] Hash rellenado: '{hash_code}'")
        elif len(hash_code) > 16:
            print(f"ADVERTENCIA: El hash_code tiene más de 16 caracteres: {len(hash_code)}")
            hash_code = hash_code[:16]
            print(f"[enviar_nfc] Hash truncado: '{hash_code}'")
        
        print(f"[enviar_nfc] Hash final a enviar (16 chars): '{hash_code}'")
        print(f"[enviar_nfc] Longitud final: {len(hash_code)} caracteres")
        
        # Retornar solo el hash, sin JSON
        return hash_code, 200
        
    except Exception as e:
        print(f"ERROR CRÍTICO en enviar_nfc: {str(e)}")
        import traceback
        traceback.print_exc()
        return "ERROR", 500

@app.route('/recibirUID', methods=['POST'])
def recibir_uid():
    """
    Recibe el UID del tag NFC detectado por el ESP32
    """
    global nfc_state
    
    try:
        data = request.get_json()
        uid = data.get('uid')
        
        print(f"\n=== TAG NFC DETECTADO POR ESP32 ===")
        print(f"UID recibido: {uid}")
        
        # Solo procesar si estamos esperando un tag
        if nfc_state['esperando_tag'] and not nfc_state['proceso_completado']:
            # Actualizar estado a detectado
            nfc_state['uid_detectado'] = uid
            nfc_state['estado_actual'] = 'detected'
            nfc_state['mensaje'] = '¡Tarjeta detectada! Preparando escritura...'
            nfc_state['timestamp'] = time.time()
            
            print(f"Estado actualizado: detected")
            
            # Después de un breve momento, cambiar a writing
            # Esto se hace para que el frontend pueda mostrar la animación de detección
            import threading
            def cambiar_a_writing():
                time.sleep(1.5)  # Dar tiempo para mostrar la animación de detección
                if nfc_state['estado_actual'] == 'detected':
                    nfc_state['estado_actual'] = 'writing'
                    nfc_state['mensaje'] = 'Escribiendo datos en la tarjeta...'
                    print("Estado cambiado a: writing")
            
            threading.Thread(target=cambiar_a_writing).start()
            
        else:
            print("WARNING: Se detectó un tag pero no hay proceso activo")
        
        return jsonify({'status': 'ok'}), 200
        
    except Exception as e:
        print(f"ERROR en recibir_uid: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/recibirResultado', methods=['POST'])
def recibir_resultado():
    """
    Recibe el resultado de la escritura NFC del ESP32
    """
    global nfc_state
    
    try:
        data = request.get_json()
        uid = data.get('uid')
        resultado = data.get('resultado')
        
        print(f"\n=== RESULTADO ESCRITURA NFC RECIBIDO ===")
        print(f"UID: {uid}")
        print(f"Resultado: {'ÉXITO' if resultado == '1' else 'FALLO'}")
        print(f"Estado actual: {nfc_state['estado_actual']}")
        print(f"Proceso completado: {nfc_state['proceso_completado']}")
        
        # Solo procesar si estamos en proceso de escritura
        if nfc_state['estado_actual'] == 'writing' and not nfc_state['proceso_completado']:
            # Actualizar estado según resultado
            if resultado == '1':
                nfc_state['estado_actual'] = 'success'
                nfc_state['mensaje'] = '¡Grabación exitosa!'
                
                # Actualizar la base de datos
                if nfc_state['usuario_id'] and nfc_state['hash_code']:
                    print(f"\n=== ACTUALIZANDO BASE DE DATOS ===")
                    print(f"[recibir_resultado] Usuario ID: {nfc_state['usuario_id']}")
                    print(f"[recibir_resultado] DNI original: {nfc_state.get('dni_original', 'No disponible')}")
                    print(f"[recibir_resultado] Hash a guardar: {nfc_state['hash_code']}")
                    print(f"[recibir_resultado] Longitud del hash: {len(nfc_state['hash_code'])} caracteres")
                    
                    # Verificar que el hash tenga el formato correcto
                    if not nfc_state['hash_code'].isalnum():
                        print("ADVERTENCIA: El hash contiene caracteres no alfanuméricos")
                    
                    # Registrar el hash que se envió al ESP32
                    print(f"[recibir_resultado] Hash enviado al ESP32: {nfc_state['hash_code']}")
                    
                    # Llamar a la función para actualizar la base de datos
                    success = usuarios_temp.actualizar_nfc_code(
                        nfc_state['usuario_id'], 
                        nfc_state['hash_code']
                    )
                    
                    if success:
                        print("✓ Base de datos actualizada correctamente")
                        
                        # Verificar que el hash se guardó correctamente
                        try:
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            cursor.execute(
                                "SELECT nfc_code FROM UserAtributes WHERE ID_useratributes = %s", 
                                (nfc_state['usuario_id'],)
                            )
                            resultado = cursor.fetchone()
                            if resultado:
                                hash_guardado = resultado['nfc_code']
                                print(f"[recibir_resultado] Hash guardado en BD: {hash_guardado}")
                                print(f"[recibir_resultado] Longitud del hash guardado: {len(hash_guardado) if hash_guardado else 0} caracteres")
                                
                                # Verificar si el hash guardado coincide con el esperado
                                if hash_guardado == nfc_state['hash_code']:
                                    print("✓ Verificación exitosa: El hash guardado coincide con el esperado")
                                else:
                                    print("✗ ERROR: El hash guardado NO coincide con el esperado")
                                    print(f"  - Esperado: {nfc_state['hash_code']}")
                                    print(f"  - Guardado: {hash_guardado}")
                            cursor.close()
                            conn.close()
                        except Exception as db_error:
                            print(f"ERROR al verificar el hash en la base de datos: {db_error}")
                    else:
                        print("✗ Error actualizando base de datos")
                        nfc_state['estado_actual'] = 'failed'
                        nfc_state['mensaje'] = 'Error al guardar en base de datos'
            else:
                nfc_state['estado_actual'] = 'failed'
                nfc_state['mensaje'] = 'Error al grabar la tarjeta'
                print("ERROR: Falló la escritura en la tarjeta NFC")
            
            nfc_state['proceso_completado'] = True
            nfc_state['timestamp'] = time.time()
            
        else:
            print("WARNING: Se recibió resultado pero no estábamos escribiendo o el proceso ya estaba completado")
        
        return jsonify({'status': 'ok'}), 200
        
    except Exception as e:
        print(f"ERROR CRÍTICO en recibir_resultado: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/estadoNFC', methods=['GET'])
def estado_nfc():
    """
    Endpoint para que el frontend consulte el estado actual del proceso NFC
    """
    global nfc_state
    
    try:
        response = {
            'estado': nfc_state['estado_actual'],
            'mensaje': nfc_state['mensaje'],
            'uid': nfc_state['uid_detectado'],
            'usuario_id': nfc_state['usuario_id'],
            'progreso': 0  # Porcentaje de progreso para la barra
        }
        
        # Calcular progreso según el estado
        estado_progreso = {
            'idle': 0,
            'waiting': 0,
            'detected': 30,
            'writing': 60,
            'success': 100,
            'failed': 100
        }
        
        response['progreso'] = estado_progreso.get(nfc_state['estado_actual'], 0)
        
        # Limpiar el estado después de un tiempo si ya terminó el proceso
        if nfc_state['proceso_completado'] and nfc_state['timestamp']:
            tiempo_transcurrido = time.time() - nfc_state['timestamp']
            if tiempo_transcurrido > 10:  # 10 segundos después del resultado
                print("INFO: Limpiando estado NFC por timeout")
                nfc_state = {
                    'usuario_id': None,
                    'hash_code': None,
                    'uid_detectado': None,
                    'estado_actual': 'idle',
                    'mensaje': '',
                    'timestamp': None,
                    'esperando_tag': False,
                    'proceso_completado': False
                }
        
        return jsonify(response), 200
        
    except Exception as e:
        print(f"ERROR en estado_nfc: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/resetNFC', methods=['POST'])
def reset_nfc():
    """
    Resetea el estado del sistema NFC
    """
    global nfc_state
    
    print("\n=== RESET DEL SISTEMA NFC SOLICITADO ===")
    
    nfc_state = {
        'usuario_id': None,
        'hash_code': None,
        'uid_detectado': None,
        'estado_actual': 'idle',
        'mensaje': '',
        'timestamp': None,
        'esperando_tag': False,
        'proceso_completado': False
    }
    
    print("Estado NFC reseteado completamente")
    return jsonify({'status': 'reset'}), 200

# API endpoint para eliminar una puerta
@app.route('/api/puertas/<int:door_id>', methods=['DELETE'])
@login_required
@nfc_required
def api_eliminar_puerta(door_id):
    """Elimina una puerta por su ID"""
    try:
        from bdd.puertas import eliminar_puerta
        
        # Verificar si el usuario tiene permisos de administrador
        if not session.get('is_admin'):
            return jsonify({'success': False, 'error': 'No autorizado'}), 403
            
        # Intentar eliminar la puerta
        if eliminar_puerta(door_id):
            return jsonify({'success': True, 'message': 'Puerta eliminada correctamente'})
        else:
            return jsonify({'success': False, 'error': 'No se pudo eliminar la puerta'}), 400
            
    except Exception as e:
        print(f"Error al eliminar puerta: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/permisos/<id_permiso>', methods=['DELETE'])
@login_required
@nfc_required
def api_eliminar_permiso(id_permiso):
    """
    Endpoint para eliminar un permiso de usuario
    """
    try:
        from bdd.permisos import eliminar_permiso_usuario
        
        # Verificar si el usuario tiene permisos para eliminar
        from flask import session
        from bdd.roles import obtener_flag_asignar_permisos_por_usuario
        
        user_id = session.get('user_id')
        is_admin = (user_id == 1)  # El usuario con ID 1 es el administrador
        can_assign_permissions = False
        
        if user_id and not is_admin:
            try:
                can_assign_permissions = obtener_flag_asignar_permisos_por_usuario(user_id)
            except Exception as e:
                print(f"[WARN] No se pudo verificar permisos: {e}")
        
        if not (is_admin or can_assign_permissions):
            return jsonify({
                'success': False,
                'message': 'No tiene permisos para eliminar permisos.'
            }), 403
        
        # Intentar eliminar el permiso
        if eliminar_permiso_usuario(id_permiso):
            return jsonify({
                'success': True,
                'message': 'Permiso eliminado correctamente.'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No se pudo eliminar el permiso. Verifique el ID proporcionado.'
            }), 404
            
    except Exception as e:
        print(f"Error al eliminar permiso: {e}")
        return jsonify({
            'success': False,
            'message': f'Error al procesar la solicitud: {str(e)}'
        }), 500

# Registrar el blueprint de autenticación
app.register_blueprint(auth_bp)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)  # Desactivar reloader para evitar duplicación
