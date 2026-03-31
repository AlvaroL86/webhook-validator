#!/usr/bin/env python3
from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

WEBHOOK_VERIFY_TOKEN = os.getenv('WEBHOOK_VERIFY_TOKEN', 'fidelity_whatsapp_2024_secure')

@app.route('/webhook/whatsapp', methods=['GET', 'POST'])
def webhook_whatsapp():
    if request.method == 'GET':
        mode = request.args.get('hub.mode')
        challenge = request.args.get('hub.challenge')
        verify_token = request.args.get('hub.verify_token')
        
        if mode == 'subscribe' and verify_token == WEBHOOK_VERIFY_TOKEN:
            print(f'✅ Webhook validated!')
            return challenge, 200, {'Content-Type': 'text/plain'}
        else:
            print(f'❌ Validation failed')
            return 'Unauthorized', 403
    else:
        print(f'📨 Message received')
        return jsonify({'status': 'received'}), 200

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f'\n✅ Webhook Validator running on port {port}')
    print(f'🔐 Token: {WEBHOOK_VERIFY_TOKEN}')
    app.run(host='0.0.0.0', port=port, debug=False)
```

4. Click **"Commit new file"**

### **PASO 3: Crear requirements.txt**

1. Click **"Add file"** → **"Create new file"**
2. **Nombre**: `requirements.txt`
3. Pega:
```
Flask==2.3.3
python-dotenv==1.0.0
gunicorn==21.2.0
