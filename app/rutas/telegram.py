from flask import Blueprint, request, jsonify
from app.Handlers.TelegramHandler import TelegramHandler
from app.Handlers.AIHandler import AIHandler
from app.Handlers.WhisperHandler import WhisperHandler
from app.Handlers.HumeHandler import HumeHandler
from app.Handlers.ElevenLabsHandler import ElevenLabsHandler
from app.Helpers.UsuarioHelper import UsuarioHelper

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
        if 'text' in message:
            msg_type = 'text'
        elif 'voice' in message:
            msg_type = 'voice'
        else:
            msg_type = None

        tg = TelegramHandler()
        telegram_username = message.get('from', {}).get('username')

        # Verificar que el usuario esté registrado
        helper = UsuarioHelper()
        if not telegram_username or not helper.username_exists(telegram_username):
            tg.send_message(chat_id, "No estás registrado. Necesitas una cuenta para usar Lexi Azteca. puedes obtenerla aqui https://lexi-azteca.com/login")
            return jsonify({"status": "ok"}), 200

        if msg_type == 'text':
            text = message['text'].strip().lower()
            user_context = helper.get_by_username(telegram_username)
            ai = AIHandler()
            respuesta = ai.generate_response(text, user_context)
            tg.send_message(chat_id, respuesta)

        elif msg_type == 'voice':
            file_id = message['voice']['file_id']
            respuesta = None

            try:
                # 1. Descargar audio
                audio_bytes = tg.get_voice_bytes(file_id)

                # 2. Transcribir con Whisper
                whisper = WhisperHandler()
                texto_transcrito = whisper.transcribe(audio_bytes)
                print(f"TRANSCRIPCIÓN: {texto_transcrito}")

                # 3. Analizar emociones con Hume (opcional, no bloquea el flujo)
                emociones = {}
                try:
                    hume = HumeHandler()
                    emociones = hume.analyze_audio(audio_bytes)
                    print(f"EMOCIONES: {emociones}")
                except Exception as hume_error:
                    print(f"HUME ERROR (continuando sin emociones): {hume_error}")

                # 4. Obtener contexto del usuario
                user_context = helper.get_by_username(telegram_username) or {}

                # Agregar emociones al contexto si las hay
                if emociones:
                    user_context['emociones_detectadas'] = ", ".join(f"{k}: {v}" for k, v in emociones.items())

                # 5. Generar respuesta con DeepSeek
                ai = AIHandler()
                respuesta = ai.generate_response(texto_transcrito, user_context)

                # 6. Convertir respuesta a voz con ElevenLabs
                eleven = ElevenLabsHandler()
                audio_respuesta = eleven.text_to_speech(respuesta)

                # 7. Enviar audio de vuelta
                tg.send_voice(chat_id, audio_respuesta)

            except Exception as voice_error:
                print(f"VOICE PIPELINE ERROR: {voice_error}")
                # Fallback: responder en texto
                fallback = respuesta if respuesta else "Lo siento, no pude procesar tu mensaje de voz. Intenta escribirlo."
                tg.send_message(chat_id, fallback)

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
