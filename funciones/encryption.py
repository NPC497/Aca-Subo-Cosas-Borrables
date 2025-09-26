"""
Módulo de encriptación bidireccional para contraseñas
Permite encriptar y desencriptar contraseñas para mostrarlas en el perfil
"""
from cryptography.fernet import Fernet
import base64
import os

# Clave de encriptación (en producción, usar variables de entorno)
SECRET_KEY = b'NotFC-Secret-Key-2024-For-Password-Encryption-32'

def generar_clave():
    """Genera una nueva clave de encriptación"""
    return Fernet.generate_key()

def crear_fernet():
    """Crea una instancia Fernet con la clave secreta"""
    # Asegurar que la clave tenga 32 bytes
    key = SECRET_KEY.ljust(32)[:32]
    key = base64.urlsafe_b64encode(key)
    return Fernet(key)

def encriptar_password(password):
    """
    Encripta una contraseña usando Fernet
    Args:
        password (str): Contraseña en texto plano
    Returns:
        str: Contraseña encriptada en base64
    """
    f = crear_fernet()
    password_bytes = password.encode('utf-8')
    encrypted = f.encrypt(password_bytes)
    return encrypted.decode('utf-8')

def desencriptar_password(encrypted_password):
    """
    Desencripta una contraseña usando Fernet
    Args:
        encrypted_password (str): Contraseña encriptada en base64
    Returns:
        str: Contraseña en texto plano
    """
    try:
        f = crear_fernet()
        encrypted_bytes = encrypted_password.encode('utf-8')
        decrypted = f.decrypt(encrypted_bytes)
        return decrypted.decode('utf-8')
    except Exception as e:
        print(f"Error al desencriptar: {e}")
        return None
