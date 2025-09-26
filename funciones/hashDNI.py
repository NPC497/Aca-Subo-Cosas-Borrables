import hashlib

def hashearDNI(dni):
    """
    Genera un hash determinístico del DNI.
    MEJORADO: Asegura que siempre genera el mismo hash para el mismo DNI
    y devuelve exactamente 16 caracteres para el NFC.
    """
    # Convertir DNI a string y limpiar espacios en blanco
    dni_str = str(dni).strip()
    
    # Validar que el DNI no esté vacío
    if not dni_str:
        print("ERROR: DNI vacío recibido en hashearDNI")
        return ""
    
    # Usar un salt fijo para que sea determinístico
    SALT = "NFC_SYSTEM_2024"
    
    # Combinar DNI con salt
    cadena_combinada = f"{dni_str}_{SALT}"
    
    # Generar hash SHA-256
    try:
        hash_obj = hashlib.sha256(cadena_combinada.encode('utf-8'))
        hash_hex = hash_obj.hexdigest()
        
        # Tomar los primeros 16 caracteres para el NFC (máximo permitido)
        hash_corto = hash_hex[:16].upper()
        
        print(f"[hashearDNI] DNI: '{dni_str}' -> Hash generado: {hash_corto}")
        return hash_corto
        
    except Exception as e:
        print(f"ERROR en hashearDNI para DNI '{dni_str}': {e}")
        return ""
