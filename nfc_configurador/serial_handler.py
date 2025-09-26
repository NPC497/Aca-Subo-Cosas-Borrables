import serial
import serial.tools.list_ports
import json
import threading
import time
from queue import Queue

# Variables globales
serial_port = None
serial_thread = None
is_connected = False
message_queue = Queue()

# NUEVA VARIABLE: Para guardar temporalmente el resultado del escaneo
scan_result_cache = None
scan_result_timestamp = 0

esp32_status = {
    'connected': False,
    'wifi_connected': False,
    'wifi_ssid': '',
    'ip_address': '',
    'server_ip': '',
    'server_port': '',
    'last_message': ''
}

# Configuración serial
BAUD_RATE = 115200

def find_esp32_ports():
    """Busca puertos que probablemente sean ESP32"""
    ports = []
    for port in serial.tools.list_ports.comports():
        # ESP32 generalmente aparece con estos VID/PID o descripciones
        if any(x in port.description.lower() for x in ['cp210', 'ch340', 'esp32', 'usb']):
            ports.append({
                'port': port.device,
                'description': port.description,
                'hwid': port.hwid
            })
    return ports

def serial_reader():
    """Thread para leer datos del puerto serial"""
    global serial_port, esp32_status
    
    while is_connected and serial_port:
        try:
            if serial_port.in_waiting:
                line = serial_port.readline().decode('utf-8').strip()
                if line:
                    try:
                        # Intentar parsear como JSON
                        data = json.loads(line)
                        process_esp32_message(data)
                    except json.JSONDecodeError:
                        # Si no es JSON, guardarlo como mensaje plano
                        print(f"Serial: {line}")
        except Exception as e:
            print(f"Error leyendo serial: {e}")
            break
        time.sleep(0.01)

def process_esp32_message(data):
    """Procesa mensajes JSON del ESP32 con manejo especial para scan_result"""
    global esp32_status, scan_result_cache, scan_result_timestamp
    
    msg_type = data.get('type', '')
    
    # Imprimir mensajes de debug y scan_result
    if msg_type in ['debug', 'scan_result', 'scan_start', 'error', 'warning']:
        print(f"[ESP32 {msg_type}]: {data}")
    
    # IMPORTANTE: Guardar scan_result en caché especial
    if msg_type == 'scan_result':
        scan_result_cache = data
        scan_result_timestamp = time.time()
        print(f"✓ Resultado de escaneo guardado en caché: {len(data.get('networks', []))} redes")
    
    if msg_type == 'status':
        esp32_status['wifi_connected'] = data.get('wifi_connected', False)
        esp32_status['wifi_ssid'] = data.get('ssid', '')
        esp32_status['ip_address'] = data.get('ip', '')
        esp32_status['server_ip'] = data.get('serverIP', '')
        esp32_status['server_port'] = data.get('serverPort', '')
        
    elif msg_type == 'wifi_connected':
        esp32_status['wifi_connected'] = True
        esp32_status['wifi_ssid'] = data.get('ssid', '')
        esp32_status['ip_address'] = data.get('ip', '')
        
    elif msg_type == 'wifi_error':
        esp32_status['wifi_connected'] = False
        
    elif msg_type == 'message_updated':
        esp32_status['last_message'] = data.get('message', '')
    
    # Guardar mensaje para que el frontend lo consulte
    # PERO no guardar scan_result en la cola normal
    if msg_type != 'scan_result':
        message_queue.put(data)

def send_to_esp32(command):
    """Envía comando al ESP32"""
    global serial_port
    
    if not serial_port or not is_connected:
        return False
    
    try:
        json_str = json.dumps(command) + '\n'
        serial_port.write(json_str.encode('utf-8'))
        return True
    except Exception as e:
        print(f"Error enviando comando: {e}")
        return False

def connect_serial(port_name):
    """Conecta al puerto serial especificado"""
    global serial_port, serial_thread, is_connected
    
    try:
        # Desconectar si ya está conectado
        if serial_port:
            disconnect_serial()
        
        # Conectar al nuevo puerto
        serial_port = serial.serial_for_url(port_name, baudrate=BAUD_RATE, timeout=1)
        is_connected = True
        esp32_status['connected'] = True
        
        # Iniciar thread de lectura
        serial_thread = threading.Thread(target=serial_reader, daemon=True)
        serial_thread.start()
        
        # Esperar un momento y pedir estado
        time.sleep(1)
        send_to_esp32({'command': 'getStatus'})
        
        return {'success': True, 'message': f'Conectado a {port_name}'}
        
    except Exception as e:
        return {'success': False, 'error': f'Error al conectar: {str(e)}'}

def disconnect_serial():
    """Desconecta del puerto serial"""
    global serial_port, is_connected
    
    is_connected = False
    esp32_status['connected'] = False
    
    if serial_port:
        try:
            serial_port.close()
        except:
            pass
        serial_port = None
    
    return True

def get_status():
    """Obtiene el estado actual del ESP32"""
    return esp32_status

def configure_wifi(ssid, password, server_ip='192.168.1.12', server_port='5000'):
    """Configura las credenciales WiFi del ESP32"""
    command = {
        'command': 'setWiFi',
        'ssid': ssid,
        'password': password,
        'serverIP': server_ip,
        'serverPort': server_port
    }
    
    success = send_to_esp32(command)
    return success

def scan_wifi():
    """Solicita escaneo de redes WiFi - VERSIÓN MEJORADA"""
    global scan_result_cache, scan_result_timestamp
    
    print("\n=== INICIANDO ESCANEO WIFI ===")
    
    # Limpiar caché anterior
    scan_result_cache = None
    scan_result_timestamp = 0
    
    # Enviar comando de escaneo
    success = send_to_esp32({'command': 'scanWiFi'})
    
    if not success:
        print("✗ Error enviando comando de escaneo")
        return False, 'Error solicitando escaneo'
    
    print("Comando de escaneo enviado. Esperando resultado...")
    
    # Esperar hasta 15 segundos por el resultado
    timeout = time.time() + 15
    check_interval = 0.5
    
    while time.time() < timeout:
        # Verificar si llegó el resultado del escaneo
        if scan_result_cache and scan_result_timestamp > 0:
            networks = scan_result_cache.get('networks', [])
            print(f"✓ Resultado recibido: {len(networks)} redes encontradas")
            
            if networks:
                print("Redes encontradas:")
                for i, net in enumerate(networks[:5], 1):  # Mostrar primeras 5
                    print(f"  {i}. {net.get('ssid', 'Sin SSID')} ({net.get('rssi', 'N/A')} dBm)")
            
            # Limpiar caché después de usar
            result = networks
            scan_result_cache = None
            scan_result_timestamp = 0
            
            return True, result
        
        time.sleep(check_interval)
    
    # Timeout - no se recibió resultado
    print("✗ Timeout esperando resultado del escaneo")
    return True, []

def clear_wifi():
    """Borra la configuración WiFi del ESP32"""
    success = send_to_esp32({'command': 'clearWiFi'})
    return success

def test_connection():
    """Prueba la conexión al servidor"""
    success = send_to_esp32({'command': 'testConnection'})
    return success

def set_message(message):
    """Establece el mensaje a grabar en NFC"""
    if len(message) > 16:
        return False, 'Mensaje muy largo (máx 16 caracteres)'
    
    success = send_to_esp32({'command': 'setMessage', 'message': message})
    return success, 'Mensaje configurado' if success else 'Error configurando mensaje'

def get_messages():
    """Obtiene mensajes pendientes del ESP32 (para polling)"""
    messages = []
    # Procesar solo mensajes normales, NO scan_result
    while not message_queue.empty():
        msg = message_queue.get()
        # Filtrar mensajes de debug y scan relacionados durante el polling normal
        if msg.get('type') not in ['debug', 'scan_start', 'scan_result']:
            messages.append(msg)
    return messages
