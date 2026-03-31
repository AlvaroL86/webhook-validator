from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import hmac
import hashlib
import os
import requests
from dotenv import load_dotenv
from datetime import datetime

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuración
VERIFY_TOKEN = os.getenv('VERIFY_TOKEN', 'MiTokenSecreto123!@#')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN', 'EAARm8LRk4zEBRCFkmFRcF0zHNYUNrTZCG5RrJmRkO0socidmdT3vIXgidvPKgrYqxKaZAdWC6UxagI4OIAs7ZA3cZBN6obN6K4FvMmquKafLgwAdOQXZBuPOglukFtD3JGFZB6EUFyNYkMsZANcQoDFTOGZAwr9RAdB2ZCSssEZCVHywk6FZCbDhM9OinRTZAUVe2AZDZD')
PHONE_NUMBER_ID = os.getenv('PHONE_NUMBER_ID', '111014585224427')
WABA_ID = os.getenv('WABA_ID', '105695539097204')
WEBHOOK_PATH = '/webhook/whatsapp'
META_API_URL = 'https://graph.instagram.com/v18.0'

# Almacenamiento en memoria para mensajes (en producción usar BD)
messages_storage = []
templates_storage = []

def verify_webhook_signature(payload_body, signature):
    """Valida la firma del webhook de Meta"""
    expected_signature = hmac.new(
        VERIFY_TOKEN.encode(),
        payload_body,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected_signature)

@app.route('/', methods=['GET'])
def index():
    """Servir dashboard HTML"""
    try:
        with open('dashboard.html', 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return jsonify({
            'service': 'WhatsApp Business Manager',
            'version': '1.0.0',
            'status': 'running'
        }), 200

@app.route(WEBHOOK_PATH, methods=['GET', 'POST'])
def webhook():
    """Endpoint para webhooks de Meta"""
    if request.method == 'GET':
        verify_token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        if verify_token == VERIFY_TOKEN:
            return challenge, 200
        else:
            return 'Invalid verification token', 403
    
    if request.method == 'POST':
        signature = request.headers.get('X-Hub-Signature-256', '').replace('sha256=', '')
        payload_body = request.get_data()
        
        if not verify_webhook_signature(payload_body, signature):
            return jsonify({'error': 'Invalid signature'}), 401
        
        try:
            data = request.get_json()
            entry = data.get('entry', [{}])[0]
            changes = entry.get('changes', [{}])[0]
            value = changes.get('value', {})
            
            messages = value.get('messages', [])
            contacts = value.get('contacts', [])
            
            if messages:
                for message in messages:
                    from_number = message.get('from')
                    message_id = message.get('id')
                    message_type = message.get('type')
                    timestamp = message.get('timestamp')
                    
                    text_body = None
                    if message_type == 'text':
                        text_body = message.get('text', {}).get('body')
                    
                    contact_name = 'Desconocido'
                    if contacts:
                        contact_name = contacts[0].get('profile', {}).get('name', 'Desconocido')
                    
                    message_obj = {
                        'id': message_id,
                        'from': contact_name,
                        'number': from_number,
                        'message': text_body or f'[{message_type}]',
                        'timestamp': datetime.fromtimestamp(int(timestamp)).strftime('%d/%m/%Y %H:%M:%S'),
                        'type': message_type
                    }
                    messages_storage.insert(0, message_obj)
                    
                    print(f"📱 Mensaje: {contact_name} - {text_body}")
            
            return jsonify({'status': 'ok'}), 200
        except Exception as e:
            print(f"Error: {str(e)}")
            return jsonify({'error': str(e)}), 500

# API ENDPOINTS
@app.route('/api/account', methods=['GET'])
def get_account_info():
    """Información de la cuenta"""
    try:
        headers = {'Authorization': f'Bearer {ACCESS_TOKEN}'}
        response = requests.get(
            f'{META_API_URL}/{PHONE_NUMBER_ID}?fields=display_phone_number,phone_number_id,quality_rating,messaging_product',
            headers=headers,
            timeout=10
        )
        return jsonify(response.json() if response.status_code == 200 else {}), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/templates', methods=['GET'])
def get_templates():
    """Obtener plantillas"""
    try:
        headers = {'Authorization': f'Bearer {ACCESS_TOKEN}'}
        response = requests.get(
            f'{META_API_URL}/{WABA_ID}/message_templates?fields=id,name,status,category,language,components',
            headers=headers,
            timeout=10
        )
        data = response.json() if response.status_code == 200 else {'data': []}
        return jsonify(data.get('data', [])), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/templates', methods=['POST'])
def create_template():
    """Crear nueva plantilla"""
    try:
        data = request.get_json()
        headers = {'Authorization': f'Bearer {ACCESS_TOKEN}'}
        
        payload = {
            'name': data.get('name'),
            'language': data.get('language', 'es'),
            'category': data.get('category', 'MARKETING'),
            'components': data.get('components', [])
        }
        
        response = requests.post(
            f'{META_API_URL}/{WABA_ID}/message_templates',
            json=payload,
            headers=headers,
            timeout=10
        )
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/templates/<template_id>', methods=['DELETE'])
def delete_template(template_id):
    """Eliminar plantilla"""
    try:
        headers = {'Authorization': f'Bearer {ACCESS_TOKEN}'}
        response = requests.delete(
            f'{META_API_URL}/{template_id}',
            headers=headers,
            timeout=10
        )
        return jsonify({'success': response.status_code == 200}), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/messages', methods=['GET'])
def get_messages():
    """Obtener mensajes"""
    limit = request.args.get('limit', 50, type=int)
    return jsonify(messages_storage[:limit]), 200

@app.route('/api/messages/send', methods=['POST'])
def send_message():
    """Enviar mensaje"""
    try:
        data = request.get_json()
        recipient_phone = data.get('phone')
        message_text = data.get('message')
        
        if not recipient_phone or not message_text:
            return jsonify({'error': 'Phone and message required'}), 400
        
        headers = {'Authorization': f'Bearer {ACCESS_TOKEN}'}
        payload = {
            'messaging_product': 'whatsapp',
            'to': recipient_phone,
            'type': 'text',
            'text': {'body': message_text}
        }
        
        response = requests.post(
            f'{META_API_URL}/{PHONE_NUMBER_ID}/messages',
            json=payload,
            headers=headers,
            timeout=10
        )
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Estadísticas"""
    return jsonify({
        'total_messages': len(messages_storage),
        'phone_number': '+34 976 04 30 30',
        'waba_id': WABA_ID,
        'phone_number_id': PHONE_NUMBER_ID,
        'display_name': 'Fidelity For Net',
        'quality_rating': 'High',
        'account_mode': 'LIVE',
        'message_limit': '10K Customers / 24hr'
    }), 200

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
