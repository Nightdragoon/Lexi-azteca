from flask import Blueprint, request, jsonify
from app.Handlers.TelegramHandler import TelegramHandler
from app.Handlers.AIHandler import AIHandler
from app.Helpers.UsuarioHelper import UsuarioHelper
import random

tg_bp = Blueprint('telegram', __name__, url_prefix='/telegram')


@tg_bp.route('/webhook', methods=['POST'])
def receive_webhook():
    """
    Recibe mensajes entrantes de Telegram
    ---
    tags:
      - telegram
    responses:
      200:
        description: Mensaje procesado
      400:
        description: Error al procesar el mensaje
    """
    data = request.get_json()
    print("TELEGRAM WEBHOOK RECIBIDO:", data)

    try:
        message = data.get('message')
        if not message:
            return jsonify({"status": "ok"}), 200

        chat_id = message['chat']['id']
        msg_type = 'text' if 'text' in message else None

        if msg_type == 'text':
            text = message['text'].strip().lower()
            tg = TelegramHandler()

            if text == 'quiero registrarme':
                # En Telegram no hay teléfono automático, se usa el chat_id como identificador
                helper = UsuarioHelper()
                phone = str(chat_id)
                if helper.phone_exists(phone):
                    tg.send_message(chat_id, "Tu cuenta ya está registrada en la base de datos")
                else:
                    codigo = random.randint(100000, 999999)
                    tg.send_message(chat_id, f"Tu código de registro es: {codigo}")
            else:
                helper = UsuarioHelper()
                user_context = helper.get_by_phone(str(chat_id))
                ai = AIHandler()
                respuesta = ai.generate_response(text, user_context)
                tg.send_message(chat_id, respuesta)

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        print("TELEGRAM WEBHOOK ERROR:", str(e))
        return jsonify({"error": str(e)}), 400


@tg_bp.route('/set-webhook', methods=['POST'])
def set_webhook():
    """
    Registra el webhook de Telegram
    ---
    tags:
      - telegram
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - url
          properties:
            url:
              type: string
              example: "https://tu-dominio.up.railway.app/telegram/webhook"
    responses:
      200:
        description: Webhook registrado
      400:
        description: URL no proporcionada
    """
    body = request.get_json()
    url = body.get('url')

    if not url:
        return jsonify({"error": "El campo 'url' es requerido"}), 400

    try:
        tg = TelegramHandler()
        result = tg.set_webhook(url)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@tg_bp.route('/delete-webhook', methods=['POST'])
def delete_webhook():
    """
    Elimina el webhook de Telegram
    ---
    tags:
      - telegram
    responses:
      200:
        description: Webhook eliminado
    """
    try:
        tg = TelegramHandler()
        result = tg.delete_webhook()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@tg_bp.route('/send-message', methods=['POST'])
def send_message():
    """
    Envía un mensaje de texto por Telegram
    ---
    tags:
      - telegram
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - chat_id
            - text
          properties:
            chat_id:
              type: integer
              example: 123456789
            text:
              type: string
              example: "Hola!"
    responses:
      200:
        description: Mensaje enviado
      400:
        description: Datos inválidos
    """
    body = request.get_json()
    chat_id = body.get('chat_id')
    text = body.get('text')

    if not chat_id or not text:
        return jsonify({"error": "Los campos 'chat_id' y 'text' son requeridos"}), 400

    try:
        tg = TelegramHandler()
        result = tg.send_message(chat_id, text)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@tg_bp.route('/update-token', methods=['POST'])
def update_token():
    """
    Actualiza el token del bot de Telegram
    ---
    tags:
      - telegram
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - token
          properties:
            token:
              type: string
              example: "123456:ABC-DEF..."
    responses:
      200:
        description: Token actualizado
      400:
        description: Token no proporcionado
    """
    body = request.get_json()
    token = body.get('token')

    if not token:
        return jsonify({"error": "El campo 'token' es requerido"}), 400

    tg = TelegramHandler()
    tg.update_token(token)
    return jsonify({"message": "Token actualizado correctamente"}), 200
