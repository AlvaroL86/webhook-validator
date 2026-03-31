# WhatsApp Webhook Validator

Validador de webhooks para integración de **WhatsApp API Meta + n8n**.

Este servicio recibe y valida webhooks de Meta, procesando mensajes de WhatsApp.

## 🚀 Características

- ✅ Validación de webhooks de Meta
- ✅ Procesamiento de mensajes de WhatsApp
- ✅ Seguimiento de estados de entrega
- ✅ Integración con PostgreSQL
- ✅ Notificaciones por Slack (opcional)
- ✅ Listo para Render Deploy

## 📋 Requisitos

- Python 3.9+
- Cuenta en Meta Developer
- Número de teléfono de WhatsApp Business verificado
- (Opcional) PostgreSQL para almacenar mensajes

## 🔧 Instalación Local

### 1. Clonar el repositorio
```bash
git clone https://github.com/tu-usuario/webhook-validator.git
cd webhook-validator
```

### 2. Crear entorno virtual
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno
```bash
cp .env.example .env
# Edita .env y agrega tus credenciales
```

### 5. Ejecutar localmente
```bash
python app.py
```

La aplicación estará disponible en: `http://localhost:5000`

## 🌐 Deployment en Render

### Paso 1: Conectar repositorio GitHub
1. Ve a [render.com](https://render.com)
2. Click en "New" → "Web Service"
3. Selecciona tu repositorio `webhook-validator`
4. Configura:
   - **Name**: `whatsapp-webhook`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`

### Paso 2: Configurar variables de entorno
En Render Dashboard → Settings → Environment:

```
VERIFY_TOKEN=MiTokenSecreto123!@#
FLASK_ENV=production
PORT=5000
```

### Paso 3: Deploy
- Click en "Create Web Service"
- Render automáticamente hará deploy en: `https://whatsapp-webhook.onrender.com`

## 📝 Endpoints

### GET `/webhook/whatsapp`
Valida el webhook (handshake de Meta).

**Parámetros:**
```
hub.verify_token=MiTokenSecreto123!@#
hub.challenge=abc123...
```

**Respuesta:**
```json
{
  "challenge": "abc123..."
}
```

### POST `/webhook/whatsapp`
Recibe eventos de WhatsApp (mensajes, estados).

**Headers requeridos:**
```
X-Hub-Signature-256: sha256=<firma>
Content-Type: application/json
```

**Body (ejemplo):**
```json
{
  "object": "whatsapp_business_account",
  "entry": [
    {
      "changes": [
        {
          "value": {
            "messages": [
              {
                "from": "5491234567890",
                "id": "wamid.123...",
                "timestamp": "1234567890",
                "type": "text",
                "text": {
                  "body": "Hola!"
                }
              }
            ],
            "contacts": [
              {
                "profile": {
                  "name": "Juan"
                },
                "wa_id": "5491234567890"
              }
            ]
          }
        }
      ]
    }
  ]
}
```

### GET `/health`
Verifica que el servicio está corriendo.

**Respuesta:**
```json
{
  "status": "healthy"
}
```

### GET `/`
Información del servicio.

**Respuesta:**
```json
{
  "service": "WhatsApp Webhook Validator",
  "version": "1.0.0",
  "status": "running",
  "webhook_url": "/webhook/whatsapp"
}
```

## 🔐 Seguridad

### Validación de Firma
Meta envía webhooks con firma `X-Hub-Signature-256`. La app valida que coincida con tu `VERIFY_TOKEN`.

```python
# El servidor verifica:
signature = request.headers.get('X-Hub-Signature-256')
expected = hmac.new(VERIFY_TOKEN.encode(), payload, hashlib.sha256).hexdigest()
```

### Variables de Entorno
- Nunca commits `.env` (usa `.env.example`)
- Genera un token fuerte para `VERIFY_TOKEN`
- Renueva credenciales cada 30 días

## 📊 Configurar en Meta Dashboard

1. Ve a [developers.facebook.com](https://developers.facebook.com)
2. Selecciona tu app → WhatsApp → Configuration
3. En "Webhook URL":
   - **URL**: `https://whatsapp-webhook.onrender.com/webhook/whatsapp`
   - **Verify Token**: `MiTokenSecreto123!@#` (debe coincidir)
4. Selecciona eventos:
   - ☑ `messages`
   - ☑ `message_status`
   - ☑ `message_template_status_update`
5. Click "Verify and Save"

Meta hará GET para validar. Si ves ✓, estás listo.

## 🧪 Testing

### Test en Postman/curl
```bash
# Validar webhook
curl "http://localhost:5000/webhook/whatsapp?hub.verify_token=MiTokenSecreto123!@#&hub.challenge=test123"

# Check health
curl http://localhost:5000/health
```

### Test con n8n
1. En n8n, crea una workflow que haga HTTP POST a tu webhook
2. Verifica que aparece en los logs
3. Usa el Execution Log de n8n para debuggear

## 🐛 Troubleshooting

| **Problema** | **Solución** |
| --- | --- |
| `requirements.txt not found` | Asegúrate que el archivo está en la raíz del repo |
| `Verify Token Mismatch` | Verifica que `VERIFY_TOKEN` coincida en Meta y en `.env` |
| `Connection refused` | Revisa que Port esté correctamente configurado (5000) |
| `Invalid signature` | La firma de Meta no es válida. Verifica `VERIFY_TOKEN` |

## 📚 Documentación Relacionada

- [Documento 1: Setup Completo](../1_Setup_Completo_WhatsApp_API_n8n.docx)
- [Documento 2: Automatizaciones Avanzadas](../2_Automatizaciones_Avanzadas_WhatsApp_n8n.docx)
- [Documento 3: Cheat Sheet](../3_Cheat_Sheet_WhatsApp_n8n.docx)
- [Documento 4: Plan Implementación](../4_Plan_Implementacion_WhatsApp_n8n.docx)

## 🤝 Soporte

Si tienes problemas:

1. Revisa los logs en Render: Dashboard → Logs
2. Revisa Meta Webhook Dashboard: ¿está "Active"?
3. Revisa tu VERIFY_TOKEN en `.env`
4. Contacta con soporte Meta si el error es de su lado

## 📄 Licencia

MIT - Libre para usar y modificar.

---

**Creado**: Marzo 2026  
**Versión**: 1.0.0
