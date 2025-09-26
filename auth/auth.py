"""
Módulo de autenticación para registro y login de usuarios
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template
from bdd.conexionBDD import get_connection
from funciones.hashUtil import hash_dni_consistente
from funciones.encryption import encriptar_password, desencriptar_password
import re
import random
import string
import time
from datetime import datetime, timedelta
from functools import wraps
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Diccionario para almacenar temporalmente los códigos de verificación
# En producción, considera usar una base de datos o caché como Redis
codigos_verificacion = {}

def generar_codigo_verificacion():
    """Genera un código de verificación de 6 dígitos"""
    return ''.join(random.choices(string.digits, k=6))

def guardar_codigo_verificacion(email, codigo):
    """Guarda el código de verificación con su tiempo de expiración"""
    tiempo_expiracion = datetime.now() + timedelta(minutes=5)
    codigos_verificacion[email] = {
        'codigo': codigo,
        'expira': tiempo_expiracion.timestamp(),
        'intentos': 0,
        'bloqueado_hasta': None
    }

def verificar_codigo(email, codigo_ingresado):
    """Verifica si el código ingresado es válido"""
    if email not in codigos_verificacion:
        return False, "Código no encontrado o expirado"
    
    datos_codigo = codigos_verificacion[email]
    
    # Verificar si el código está bloqueado
    if datos_codigo.get('bloqueado_hasta') and datetime.now().timestamp() < datos_codigo['bloqueado_hasta']:
        tiempo_restante = int((datos_codigo['bloqueado_hasta'] - datetime.now().timestamp()) / 60) + 1
        return False, f"Demasiados intentos. Intente nuevamente en {tiempo_restante} minutos"
    
    # Verificar si el código expiró
    if datetime.now().timestamp() > datos_codigo['expira']:
        del codigos_verificacion[email]
        return False, "El código ha expirado. Por favor, solicite uno nuevo"
    
    # Verificar intentos fallidos
    if datos_codigo['intentos'] >= 3:
        # Bloquear por 5 minutos después de 3 intentos fallidos
        datos_codigo['bloqueado_hasta'] = datetime.now().timestamp() + 300  # 5 minutos
        return False, "Demasiados intentos fallidos. Intente nuevamente en 5 minutos"
    
    # Verificar el código
    if codigo_ingresado != datos_codigo['codigo']:
        datos_codigo['intentos'] += 1
        return False, "Código incorrecto"
    
    # Código válido
    return True, "Código válido"

def limpiar_codigo_verificacion(email):
    """Elimina el código de verificación después de usarlo"""
    if email in codigos_verificacion:
        del codigos_verificacion[email]

# SMTP configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "notfc.noreply@gmail.com"
SMTP_PASSWORD = "soop gyga qsta jfmp"

def enviar_correo_verificacion(destinatario, codigo):
    """Envía un correo con el código de verificación"""
    try:
        # Configurar el mensaje
        mensaje = MIMEMultipart()
        mensaje['From'] = SMTP_USER
        mensaje['To'] = destinatario
        mensaje['Subject'] = "Código de verificación - Recuperación de contraseña"
        
        # Cuerpo del correo
        cuerpo = f"""
        <html>
            <body>
                <h2>Recuperación de contraseña</h2>
                <p>Hola,</p>
                <p>Has solicitado restablecer tu contraseña. Utiliza el siguiente código de verificación:</p>
                <h3 style="background: #f4f4f4; padding: 10px; display: inline-block; border-radius: 5px;">
                    {codigo}
                </h3>
                <p>Este código expirará en 5 minutos.</p>
                <p>Si no has solicitado este cambio, por favor ignora este correo.</p>
                <p>Saludos,<br>El equipo de Soporte</p>
            </body>
        </html>
        """
        
        mensaje.attach(MIMEText(cuerpo, 'html'))
        
        # Conectar y enviar el correo
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as servidor:
            servidor.starttls()
            servidor.login(SMTP_USER, SMTP_PASSWORD)
            servidor.send_message(mensaje)
            
        return True
    except Exception as e:
        print(f"Error al enviar el correo: {e}")
        return False

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

def validar_email(email):
    """Valida el formato del email"""
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(patron, email) is not None

def validar_dni(dni):
    """Valida que el DNI tenga entre 7 y 8 dígitos"""
    return str(dni).isdigit() and 7 <= len(str(dni)) <= 8

def validar_contrasena(password):
    """Valida que la contraseña tenga al menos 6 caracteres"""
    return len(password) >= 6

def usuario_existe(username, email):
    """Verifica si el usuario o email ya existen"""
    conn = get_connection()
    if not conn:
        return True
    
    try:
        cursor = conn.cursor()
        query = "SELECT COUNT(*) FROM User WHERE username = %s OR mail = %s"
        cursor.execute(query, (username, email))
        resultado = cursor.fetchone()
        return resultado[0] > 0
    except Exception as e:
        print(f"Error verificando usuario: {e}")
        return True
    finally:
        if conn:
            conn.close()

def dni_existe(dni):
    """Verifica si el DNI ya está registrado"""
    conn = get_connection()
    if not conn:
        return True
    
    try:
        cursor = conn.cursor()
        query = "SELECT COUNT(*) FROM UserAtributes WHERE dni = %s"
        cursor.execute(query, (dni,))
        resultado = cursor.fetchone()
        return resultado[0] > 0
    except Exception as e:
        print(f"Error verificando DNI: {e}")
        return True
    finally:
        if conn:
            conn.close()

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Maneja el registro de nuevos usuarios"""
    if request.method == 'GET':
        return render_template('auth/register.html')
    
    # Procesar registro POST
    try:
        datos = request.get_json() if request.is_json else request.form
        
        nombre = datos.get('nombre', '').strip()
        apellido = datos.get('apellido', '').strip()
        dni = datos.get('dni', '').strip()
        email = datos.get('email', '').strip()
        username = datos.get('username', '').strip()
        password = datos.get('password', '')
        confirm_password = datos.get('confirm_password', '')
        
        # Validaciones
        errores = []
        
        if not all([nombre, apellido, dni, email, username, password]):
            errores.append("Todos los campos son obligatorios")
        
        if not validar_email(email):
            errores.append("El formato del email no es válido")
        
        if not validar_dni(dni):
            errores.append("El DNI debe tener entre 7 y 8 dígitos")
        
        if not validar_contrasena(password):
            errores.append("La contraseña debe tener al menos 6 caracteres")
        
        if password != confirm_password:
            errores.append("Las contraseñas no coinciden")
        
        if usuario_existe(username, email):
            errores.append("El usuario o email ya están registrados")
        
        if dni_existe(dni):
            errores.append("El DNI ya está registrado")
        
        if errores:
            if request.is_json:
                return jsonify({'success': False, 'errors': errores}), 400
            else:
                return render_template('auth/register.html', errors=errores, **datos)
        
        # Encriptar la contraseña (bidireccional)
        password_encrypted = encriptar_password(password)
        
        # Hash del DNI para NFC
        dni_hash = hash_dni_consistente(dni)
        
        conn = get_connection()
        if not conn:
            error = "Error de conexión a la base de datos"
            if request.is_json:
                return jsonify({'success': False, 'errors': [error]}), 500
            else:
                return render_template('auth/register.html', errors=[error], **datos)
        
        try:
            cursor = conn.cursor()
            
            # Insertar usuario
            query_user = """
                INSERT INTO User (mail, username, password) 
                VALUES (%s, %s, %s)
            """
            cursor.execute(query_user, (email, username, password_encrypted))
            id_user = cursor.lastrowid
            
            # Asignar rol Master al primer usuario (ID 1), Usuario a los demás
            if id_user == 1:
                cursor.execute("SELECT ID_role FROM Role WHERE role = 'master'")
            else:
                cursor.execute("SELECT ID_role FROM Role WHERE role = 'usuario'")
                
            rol_result = cursor.fetchone()
            if not rol_result:
                # Si no existe el rol, usar el primer rol disponible
                cursor.execute("SELECT ID_role FROM Role LIMIT 1")
                rol_result = cursor.fetchone()
            
            id_role = rol_result[0] if rol_result else 1
            
            # Insertar atributos del usuario
            query_atributes = """
                INSERT INTO UserAtributes 
                (ID_user, ID_role, name, surname, dni, nfc_code) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query_atributes, (
                id_user, id_role, nombre, apellido, dni, ''
            ))
            
            conn.commit()
            
            # Auto-loguear al usuario después del registro exitoso
            session['user_id'] = id_user
            session['username'] = username
            session['nombre'] = nombre
            session['apellido'] = apellido
            session['role'] = id_role
            
            mensaje = "Usuario registrado exitosamente"
            if request.is_json:
                return jsonify({'success': True, 'message': mensaje}), 201
            else:
                return redirect(url_for('index'))
                
        except Exception as e:
            conn.rollback()
            error = f"Error al registrar usuario: {str(e)}"
            if request.is_json:
                return jsonify({'success': False, 'errors': [error]}), 500
            else:
                return render_template('auth/register.html', errors=[error], **datos)
        finally:
            conn.close()
            
    except Exception as e:
        error = f"Error procesando solicitud: {str(e)}"
        if request.is_json:
            return jsonify({'success': False, 'errors': [error]}), 500
        else:
            return render_template('auth/register.html', errors=[error])

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Maneja el login de usuarios"""
    if request.method == 'GET':
        return render_template('auth/login.html')
    
    # Procesar login POST
    try:
        datos = request.get_json() if request.is_json else request.form
        
        username = datos.get('username', '').strip()
        password = datos.get('password', '')
        
        if not username or not password:
            error = "Usuario y contraseña son obligatorios"
            if request.is_json:
                return jsonify({'success': False, 'error': error}), 400
            else:
                return render_template('auth/login.html', error=error)
        
        conn = get_connection()
        if not conn:
            error = "Error de conexión a la base de datos"
            if request.is_json:
                return jsonify({'success': False, 'error': error}), 500
            else:
                return render_template('auth/login.html', error=error)
        
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Buscar usuario
            query = """
                SELECT u.ID_user, u.username, u.password, u.user_status,
                       ua.name, ua.surname, ua.ID_role
                FROM User u
                LEFT JOIN UserAtributes ua ON u.ID_user = ua.ID_user
                WHERE u.username = %s OR u.mail = %s
            """
            cursor.execute(query, (username, username))
            usuario = cursor.fetchone()
            
            if not usuario:
                error = "Usuario no encontrado"
                if request.is_json:
                    return jsonify({'success': False, 'error': error}), 404
                else:
                    return render_template('auth/login.html', error=error)
            
            if not usuario['user_status']:
                error = "Usuario desactivado"
                if request.is_json:
                    return jsonify({'success': False, 'error': error}), 403
                else:
                    return render_template('auth/login.html', error=error)
            
            # Verificar contraseña desencriptando
            stored_password = desencriptar_password(usuario['password'])
            if stored_password != password:
                error = "Contraseña incorrecta"
                if request.is_json:
                    return jsonify({'success': False, 'error': error}), 401
                else:
                    return render_template('auth/login.html', error=error)
            
            # Establecer sesión
            session['user_id'] = usuario['ID_user']
            session['username'] = usuario['username']
            session['nombre'] = usuario['name']
            session['apellido'] = usuario['surname']
            session['role'] = usuario['ID_role']
            
            # Registrar el inicio de sesión en el tracking
            from funciones.tracking import registrar_evento_tracking
            registrar_evento_tracking(
                user_id=usuario['ID_user'],
                tipo_evento='login',
                detalles=f"Inicio de sesión exitoso - Usuario: {usuario['username']}"
            )
            
            mensaje = "Login exitoso"
            if request.is_json:
                return jsonify({
                    'success': True, 
                    'message': mensaje,
                    'user': {
                        'id': usuario['ID_user'],
                        'username': usuario['username'],
                        'nombre': usuario['name'],
                        'apellido': usuario['surname']
                    }
                }), 200
            else:
                # Redirect admin users to the admin dashboard, others to user dashboard
                if usuario['ID_user'] == 1:  # Admin user
                    return redirect(url_for('index'))
                else:
                    return redirect(url_for('indexUser'))
                
        except Exception as e:
            error = f"Error al iniciar sesión: {str(e)}"
            if request.is_json:
                return jsonify({'success': False, 'error': error}), 500
            else:
                return render_template('auth/login.html', error=error)
        finally:
            conn.close()
            
    except Exception as e:
        error = f"Error procesando solicitud: {str(e)}"
        if request.is_json:
            return jsonify({'success': False, 'error': error}), 500
        else:
            return render_template('auth/login.html', error=error)

@auth_bp.route('/logout')
def logout():
    """Cierra la sesión del usuario"""
    # Registrar el cierre de sesión en el tracking
    if 'user_id' in session:
        from funciones.tracking import registrar_evento_tracking
        registrar_evento_tracking(
            user_id=session['user_id'],
            tipo_evento='logout',
            detalles=f"Cierre de sesión - Usuario: {session.get('username', '')}"
        )
    
    session.clear()
    return redirect(url_for('auth.login'))

@auth_bp.route('/check-session')
def check_session():
    """Verifica si hay una sesión activa"""
    if 'user_id' in session:
        return jsonify({
            'logged_in': True,
            'user': {
                'id': session['user_id'],
                'username': session['username'],
                'nombre': session['nombre'],
                'apellido': session['apellido']
            }
        })
    return jsonify({'logged_in': False})

@auth_bp.route('/cambiar-clave')
def cambiar_clave():
    """Muestra la página para cambiar contraseña"""
    return render_template('auth/cambiar-clave.html')

@auth_bp.route('/solicitar-codigo', methods=['POST'])
def solicitar_codigo():
    """Endpoint para solicitar un código de verificación"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        
        if not validar_email(email):
            return jsonify({
                'success': False,
                'message': 'Por favor ingrese un correo electrónico válido.'
            }), 400
        
        # Verificar si el correo existe en la base de datos
        conn = get_connection()
        if not conn:
            return jsonify({
                'success': False,
                'message': 'Error de conexión con la base de datos.'
            }), 500
            
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT ID_user FROM User WHERE mail = %s", (email,))
            if not cursor.fetchone():
                return jsonify({
                    'success': False,
                    'message': 'No existe una cuenta con este correo electrónico.'
                }), 404
                
            # Generar y guardar el código
            codigo = generar_codigo_verificacion()
            guardar_codigo_verificacion(email, codigo)
            
            # Enviar el correo con el código
            if not enviar_correo_verificacion(email, codigo):
                return jsonify({
                    'success': False,
                    'message': 'Error al enviar el correo de verificación. Por favor, intente nuevamente.'
                }), 500
            
            return jsonify({
                'success': True,
                'message': 'Se ha enviado un código de verificación a tu correo electrónico.'
            })
            
        finally:
            if conn:
                conn.close()
                
    except Exception as e:
        print(f"Error en solicitar_codigo: {e}")
        return jsonify({
            'success': False,
            'message': 'Ocurrió un error al procesar la solicitud.'
        }), 500

@auth_bp.route('/verificar-codigo', methods=['POST'])
def verificar_codigo_endpoint():
    """Endpoint para verificar el código de verificación"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        codigo = data.get('codigo', '').strip()
        
        if not email or not codigo:
            return jsonify({
                'success': False,
                'message': 'Email y código son requeridos.'
            }), 400
            
        valido, mensaje = verificar_codigo(email, codigo)
        
        if valido:
            # Guardamos el email en la sesión para el siguiente paso
            session['email_recuperacion'] = email
            session['codigo_verificado'] = True
            return jsonify({
                'success': True,
                'message': 'Código verificado correctamente.'
            })
        else:
            return jsonify({
                'success': False,
                'message': mensaje
            }), 400
            
    except Exception as e:
        print(f"Error en verificar_codigo: {e}")
        return jsonify({
            'success': False,
            'message': 'Ocurrió un error al verificar el código.'
        }), 500

@auth_bp.route('/cambiar-contrasena', methods=['POST'])
def cambiar_contrasena():
    """Endpoint para cambiar la contraseña después de verificar el código"""
    try:
        # Verificar que el código haya sido verificado previamente
        if 'email_recuperacion' not in session or not session.get('codigo_verificado'):
            return jsonify({
                'success': False,
                'message': 'Por favor verifica tu código primero.'
            }), 400
            
        data = request.get_json()
        nueva_contrasena = data.get('nueva_contrasena', '').strip()
        
        if not validar_contrasena(nueva_contrasena):
            return jsonify({
                'success': False,
                'message': 'La contraseña debe tener al menos 6 caracteres.'
            }), 400
            
        email = session['email_recuperacion']
        
        # Hashear la nueva contraseña
        contrasena_hash = encriptar_password(nueva_contrasena)
        
        # Actualizar la contraseña en la base de datos
        conn = get_connection()
        if not conn:
            return jsonify({
                'success': False,
                'message': 'Error de conexión con la base de datos.'
            }), 500
            
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE User SET password = %s WHERE mail = %s",
                (contrasena_hash, email)
            )
            conn.commit()
            
            # Limpiar la sesión y el código de verificación
            session.pop('email_recuperacion', None)
            session.pop('codigo_verificado', None)
            limpiar_codigo_verificacion(email)
            
            return jsonify({
                'success': True,
                'message': 'Contraseña actualizada correctamente.'
            })
            
        except Exception as e:
            conn.rollback()
            print(f"Error al actualizar la contraseña: {e}")
            return jsonify({
                'success': False,
                'message': 'Ocurrió un error al actualizar la contraseña.'
            }), 500
            
        finally:
            if conn:
                conn.close()
                
    except Exception as e:
        print(f"Error en cambiar_contrasena: {e}")
        return jsonify({
            'success': False,
            'message': 'Ocurrió un error al procesar la solicitud.'
        }), 500
