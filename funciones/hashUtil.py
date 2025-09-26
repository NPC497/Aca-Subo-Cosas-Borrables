"""
Utilidad de hashing consistente para frontend y backend
Mantiene compatibilidad entre Python y JavaScript
"""

import hashlib
import hmac
import secrets

def hash_dni_consistente(dni, salt=None):
    """
    Genera un hash consistente para DNI que puede ser replicado en frontend
    
    Args:
        dni (str or int): Número de DNI
        salt (str, optional): Salt para el hash. Si no se proporciona, se genera uno
        
    Returns:
        dict: Contiene 'hash', 'salt', y 'short_hash'
    """
    if not dni:
        raise ValueError("DNI no puede estar vacío")
    
    dni_str = str(dni).strip()
    
    # Si no se proporciona salt, generar uno
    if salt is None:
        salt = secrets.token_hex(8)  # 16 caracteres hex
    
    # Crear hash usando HMAC-SHA256 para mayor seguridad
    message = f"{dni_str}:{salt}"
    hash_obj = hmac.new(
        salt.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    )
    
    # Obtener hash completo
    full_hash = hash_obj.hexdigest()
    
    # Crear hash corto (6 dígitos) para NFC
    # Tomar los primeros 6 caracteres del hash convertido a entero
    hash_int = int(full_hash[:12], 16)
    short_hash = str(hash_int % 1000000).zfill(6)
    
    return {
        'hash': full_hash,
        'salt': salt,
        'short_hash': short_hash,
        'dni': dni_str
    }

def verify_hash(dni, salt, expected_hash):
    """
    Verifica que un hash sea válido para un DNI dado
    
    Args:
        dni (str): Número de DNI
        salt (str): Salt usado en el hash
        expected_hash (str): Hash esperado
        
    Returns:
        bool: True si el hash es válido
    """
    try:
        result = hash_dni_consistente(dni, salt)
        return result['hash'] == expected_hash
    except:
        return False

# Función de compatibilidad con el método anterior
def hashearDNI_compat(dni):
    """
    Método de compatibilidad que mantiene el mismo formato que hashearDNI original
    pero usa el nuevo sistema de hashing
    """
    result = hash_dni_consistente(dni)
    return result['short_hash']

# JavaScript equivalent function (para referencia)
"""
// JavaScript equivalente para usar en frontend
function hashDNIConsistente(dni, salt = null) {
    if (!salt) {
        salt = Array.from({length: 16}, () => 
            Math.floor(Math.random() * 16).toString(16)
        ).join('');
    }
    
    const message = `${dni}:${salt}`;
    
    // Usar Web Crypto API
    const encoder = new TextEncoder();
    const key = encoder.encode(salt);
    const data = encoder.encode(message);
    
    return crypto.subtle.importKey(
        'raw',
        key,
        {name: 'HMAC', hash: 'SHA-256'},
        false,
        ['sign']
    ).then(key => {
        return crypto.subtle.sign('HMAC', key, data);
    }).then(signature => {
        const hashArray = Array.from(new Uint8Array(signature));
        const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
        
        const hashInt = parseInt(hashHex.substring(0, 12), 16);
        const shortHash = (hashInt % 1000000).toString().padStart(6, '0');
        
        return {
            hash: hashHex,
            salt: salt,
            shortHash: shortHash,
            dni: dni.toString()
        };
    });
}
"""
