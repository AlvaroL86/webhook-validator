from flask import Flask, request, jsonify
from flask_cors import CORS
import hmac
import hashlib
import os
import requests
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

app = Flask(__name__)
CORS(app)

VERIFY_TOKEN = os.getenv('VERIFY_TOKEN', 'MiTokenSecreto123!@#')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN', '')
PHONE_NUMBER_ID = os.getenv('PHONE_NUMBER_ID', '111014585224427')
WABA_ID = os.getenv('WABA_ID', '105695539097204')
WEBHOOK_PATH = '/webhook/whatsapp'
META_API_URL = 'https://graph.instagram.com/v18.0'

messages_storage = []

def verify_webhook_signature(payload_body, signature):
    expected_signature = hmac.new(
        VERIFY_TOKEN.encode(),
        payload_body,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected_signature)

@app.route('/', methods=['GET'])
def index():
    """Servir dashboard HTML"""
    return '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WhatsApp Business Manager</title>
    <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto'; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }
        #root { max-width: 1400px; margin: 0 auto; }
        .container { background: white; border-radius: 12px; box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3); overflow: hidden; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; display: flex; justify-content: space-between; align-items: center; }
        .header h1 { font-size: 28px; font-weight: 600; }
        .header-badge { background: rgba(255, 255, 255, 0.2); padding: 8px 16px; border-radius: 20px; }
        .tabs { display: flex; border-bottom: 1px solid #e0e0e0; background: #f8f9fa; }
        .tab { flex: 1; padding: 16px; text-align: center; cursor: pointer; border: none; background: none; font-size: 15px; font-weight: 500; color: #666; }
        .tab.active { color: #667eea; border-bottom: 3px solid #667eea; }
        .tab-content { padding: 30px; }
        .info-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
        .info-card { background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #667eea; }
        .info-label { font-size: 12px; color: #999; text-transform: uppercase; font-weight: 600; margin-bottom: 8px; }
        .info-value { font-size: 18px; font-weight: 600; color: #333; }
        .status-badge { display: inline-block; padding: 6px 12px; border-radius: 20px; font-size: 12px; background: #d4edda; color: #155724; margin-top: 8px; }
        .message-list { display: flex; flex-direction: column; gap: 12px; }
        .message-item { background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #667eea; }
        .message-header { display: flex; justify-content: space-between; margin-bottom: 10px; }
        .message-from { font-weight: 600; color: #333; }
        .message-time { font-size: 12px; color: #999; }
        .message-text { color: #666; margin: 10px 0; }
        .template-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }
        .template-card { background: #f8f9fa; padding: 20px; border-radius: 8px; border: 1px solid #e0e0e0; }
        .template-name { font-size: 16px; font-weight: 600; color: #333; margin-bottom: 10px; }
        .template-body { background: white; padding: 12px; border-radius: 4px; font-size: 13px; color: #666; margin-bottom: 15px; border-left: 3px solid #667eea; }
        button { padding: 10px 16px; border: none; border-radius: 6px; cursor: pointer; background: #667eea; color: white; font-weight: 600; }
        button:hover { background: #5568d3; }
        .empty-state { text-align: center; padding: 60px 20px; color: #999; }
        .loading { text-align: center; padding: 40px; }
        .spinner { border: 3px solid #f3f3f3; border-top: 3px solid #667eea; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 0 auto 20px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div id="root"></div>
    <script type="text/babel">
        const { useState, useEffect } = React;
        
        function App() {
            const [activeTab, setActiveTab] = useState('account');
            const [messages, setMessages] = useState([]);
            const [templates, setTemplates] = useState([]);
            const [loading, setLoading] = useState(true);
            
            useEffect(() => {
                console.log('📊 Cargando datos...');
                
                fetch('/api/messages')
                    .then(r => r.json())
                    .then(data => {
                        console.log('✓ Mensajes:', data);
                        setMessages(Array.isArray(data) ? data : []);
                    })
                    .catch(e => console.error('✗ Error mensajes:', e));
                
                fetch('/api/templates')
                    .then(r => r.json())
                    .then(data => {
                        console.log('✓ Templates:', data);
                        setTemplates(Array.isArray(data) ? data : []);
                        setLoading(false);
                    })
                    .catch(e => {
                        console.error('✗ Error templates:', e);
                        setLoading(false);
                    });
            }, []);
            
            return (
                <div className="container">
                    <div className="header">
                        <h1>📱 WhatsApp Business Manager</h1>
                        <div className="header-badge">Status: <strong>Conectado ✓</strong></div>
                    </div>
                    
                    <div className="tabs">
                        <button className={`tab ${activeTab === 'conversations' ? 'active' : ''}`} onClick={() => setActiveTab('conversations')}>💬 Conversaciones</button>
                        <button className={`tab ${activeTab === 'templates' ? 'active' : ''}`} onClick={() => setActiveTab('templates')}>📋 Templates</button>
                        <button className={`tab ${activeTab === 'account' ? 'active' : ''}`} onClick={() => setActiveTab('account')}>⚙️ Cuenta</button>
                    </div>
                    
                    {activeTab === 'conversations' && (
                        <div className="tab-content">
                            <h2 style={{marginBottom: '20px'}}>Conversaciones Recientes</h2>
                            {messages.length > 0 ? (
                                <div className="message-list">
                                    {messages.map(m => (
                                        <div key={m.id} className="message-item">
                                            <div className="message-header">
                                                <div className="message-from">{m.from}</div>
                                                <div className="message-time">{m.timestamp}</div>
                                            </div>
                                            <div style={{fontSize: '12px', color: '#999'}}>{m.number}</div>
                                            <div className="message-text">{m.message}</div>
                                            <button>Responder</button>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="empty-state">
                                    <h3>Sin conversaciones</h3>
                                    <p>Los mensajes aparecerán aquí cuando recibas</p>
                                </div>
                            )}
                        </div>
                    )}
                    
                    {activeTab === 'templates' && (
                        <div className="tab-content">
                            <h2 style={{marginBottom: '20px'}}>Plantillas de Mensaje</h2>
                            {loading ? (
                                <div className="loading">
                                    <div className="spinner"></div>
                                    <p>Cargando...</p>
                                </div>
                            ) : templates.length > 0 ? (
                                <div className="template-list">
                                    {templates.map(t => (
                                        <div key={t.id} className="template-card">
                                            <div className="template-name">{t.name}</div>
                                            <span className="status-badge">✓ {t.status}</span>
                                            <div className="template-body">{t.components?.[0]?.text?.body || 'Sin contenido'}</div>
                                            <button>Editar</button>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="empty-state">
                                    <h3>Sin plantillas</h3>
                                    <p>Crea tu primera plantilla en Meta</p>
                                </div>
                            )}
                        </div>
                    )}
                    
                    {activeTab === 'account' && (
                        <div className="tab-content">
                            <h2 style={{marginBottom: '20px'}}>Información de Cuenta</h2>
                            <div className="info-grid">
                                <div className="info-card">
                                    <div className="info-label">Número</div>
                                    <div className="info-value">+34 976 04 30 30</div>
                                </div>
                                <div className="info-card">
                                    <div className="info-label">Phone Number ID</div>
                                    <div className="info-value">111014585224427</div>
                                </div>
                                <div className="info-card">
                                    <div className="info-label">WABA ID</div>
                                    <div className="info-value">105695539097204</div>
                                </div>
                                <div className="info-card">
                                    <div className="info-label">Nombre</div>
                                    <div className="info-value">Fidelity For Net</div>
                                </div>
                                <div className="info-card">
                                    <div className="info-label">Calidad</div>
                                    <div className="info-value"><span className="status-badge">✓ High</span></div>
                                </div>
                                <div className="info-card">
                                    <div className="info-label">Modo</div>
                                    <div className="info-value"><span className="status-badge">LIVE</span></div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            );
        }
        
        ReactDOM.render(<App />, document.getElementById('root'));
    </script>
</body>
</html>'''

@app.route(WEBHOOK_PATH, methods=['GET', 'POST'])
def webhook():
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

@app.route('/api/messages', methods=['GET'])
def get_messages():
    limit = request.args.get('limit', 50, type=int)
    return jsonify(messages_storage[:limit]), 200

@app.route('/api/templates', methods=['GET'])
def get_templates():
    try:
        print(f"📋 ACCESS_TOKEN: {ACCESS_TOKEN[:20]}..." if ACCESS_TOKEN else "❌ No token")
        
        if not ACCESS_TOKEN:
            return jsonify([]), 200
        
        headers = {'Authorization': f'Bearer {ACCESS_TOKEN}'}
        url = f'{META_API_URL}/{WABA_ID}/message_templates?fields=id,name,status,category,language,components'
        
        response = requests.get(url, headers=headers, timeout=10)
        print(f"📊 Response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            templates = data.get('data', [])
            print(f"✓ {len(templates)} templates found")
            return jsonify(templates), 200
        else:
            print(f"✗ Error: {response.text}")
            return jsonify([]), 200
    except Exception as e:
        print(f"✗ Exception: {str(e)}")
        return jsonify([]), 200

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
