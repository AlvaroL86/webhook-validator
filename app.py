from flask import Flask, request, jsonify
import hmac
import hashlib
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)

# Configuración
VERIFY_TOKEN = os.getenv('VERIFY_TOKEN', 'MiTokenSecreto123!@#')
WEBHOOK_PATH = '/webhook/whatsapp'

def verify_webhook_signature(payload_body, signature):
    """
    Valida la firma del webhook de Meta.
    Meta envía: X-Hub-Signature-256: sha256=<hash>
    """
    expected_signature = hmac.new(
        VERIFY_TOKEN.encode(),
        payload_body,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)

@app.route(WEBHOOK_PATH, methods=['GET', 'POST'])
def webhook():
    """
    Endpoint principal para recibir webhooks de Meta.
    
    GET: Valida el webhook (handshake inicial)
    POST: Procesa eventos de WhatsApp
    """
    
    # PASO 1: Validación GET (Challenge de Meta)
    if request.method == 'GET':
        verify_token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        if verify_token == VERIFY_TOKEN:
            print(f"✓ Webhook validado correctamente")
            return challenge, 200
        else:
            print(f"✗ Token de validación incorrecto")
            return 'Invalid verification token', 403
    
    # PASO 2: Procesar POST (Eventos de WhatsApp)
    if request.method == 'POST':
        # Obtener firma para validación
        signature = request.headers.get('X-Hub-Signature-256', '').replace('sha256=', '')
        payload_body = request.get_data()
        
        # Validar firma (seguridad)
        if not verify_webhook_signature(payload_body, signature):
            print("✗ Firma del webhook inválida")
            return jsonify({'error': 'Invalid signature'}), 401
        
        try:
            data = request.get_json()
            
            # Extraer eventos de Meta
            entry = data.get('entry', [{}])[0]
            changes = entry.get('changes', [{}])[0]
            value = changes.get('value', {})
            
            # Procesar mensajes
            messages = value.get('messages', [])
            contacts = value.get('contacts', [])
            statuses = value.get('statuses', [])
            
            if messages:
                for message in messages:
                    from_number = message.get('from')
                    message_id = message.get('id')
                    message_type = message.get('type')
                    timestamp = message.get('timestamp')
                    
                    # Extraer contenido según tipo
                    text_body = None
                    if message_type == 'text':
                        text_body = message.get('text', {}).get('body')
                    
                    contact_name = None
                    if contacts:
                        contact_name = contacts[0].get('profile', {}).get('name')
                    
                    print(f"""
                    📱 Nuevo mensaje recibido:
                    De: {contact_name} ({from_number})
                    Tipo: {message_type}
                    Mensaje: {text_body}
                    ID: {message_id}
                    Timestamp: {timestamp}
                    """)
                    
                    # Aquí puedes:
                    # 1. Guardar en BD (PostgreSQL)
                    # 2. Procesar con IA
                    # 3. Enviar respuesta automática
                    # 4. Integrar con n8n
            
            if statuses:
                for status in statuses:
                    message_id = status.get('id')
                    status_value = status.get('status')
                    print(f"📊 Estado de mensaje {message_id}: {status_value}")
            
            # Responder a Meta (importante)
            return jsonify({'status': 'ok'}), 200
            
        except Exception as e:
            print(f"✗ Error procesando webhook: {str(e)}")
            return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Endpoint de salud para monitoreo"""
    return jsonify({'status': 'healthy'}), 200

@app.route('/', methods=['GET'])
def index():
    """Raíz de la aplicación"""
    return jsonify({
        'service': 'WhatsApp Webhook Validator',
        'version': '1.0.0',
        'status': 'running',
        'webhook_url': WEBHOOK_PATH
    }), 200

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
