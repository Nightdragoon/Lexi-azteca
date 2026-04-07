from flask import Blueprint, request, jsonify, current_app
from pydantic import ValidationError
from app.Handlers.AIHandler import AIHandler
from app.Dtos.RequestIaDto import RequestIaDto

ia_bp = Blueprint('ia', __name__, url_prefix='/ia')


@ia_bp.route("/hello_world", methods=["GET"])
def hello_world():
    """
    Endpoint de prueba IA
    ---
    tags:
      - ia
    responses:
      200:
        description: Saludo de prueba
        schema:
          type: object
          properties:
            message:
              type: string
              example: Hello, World!
    """
    return jsonify({"message": "Hello, World!"})


@ia_bp.route("/conversation", methods=["POST"])
def conversation():
    """
    Endpoint de conversación IA
    ---
    tags:
      - ia
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - prompt
            - number
          properties:
            prompt:
              type: string
              example: "¿Cuál es mi saldo?"
            number:
              type: string
              example: "5512345678"
    responses:
      200:
        description: Respuesta exitosa
      400:
        description: Datos inválidos
    """
    try:
        data = RequestIaDto(**request.get_json())
        if data.prompt != None and data.prompt != " ":
            ai_handler = AIHandler()
            response = ai_handler.generate_response(f"{data.prompt} Número de telefono : {data.number}")
            return jsonify({"response": response})

        return jsonify({"ok": "bien"})

    except ValidationError as e:
        return {"error": e.errors()}, 400


@ia_bp.route("/conversation", methods=["GET"])
def get_conversations():
    """
    Lista todas las conversaciones
    ---
    tags:
      - ia
    responses:
      200:
        description: Lista de conversaciones
    """
    session = current_app.Session()
    try:
        Conversacion = current_app.Base.classes.conversacion
        conversaciones = session.query(Conversacion).all()
        result = [
            {col.key: getattr(c, col.key) for col in Conversacion.__table__.columns}
            for c in conversaciones
        ]
        return jsonify(result)
    finally:
        session.close()


@ia_bp.route("/conversation/<int:id>", methods=["GET"])
def get_conversation(id):
    """
    Obtiene una conversación por ID
    ---
    tags:
      - ia
    parameters:
      - in: path
        name: id
        type: integer
        required: true
    responses:
      200:
        description: Conversación encontrada
      404:
        description: No encontrada
    """
    session = current_app.Session()
    try:
        Conversacion = current_app.Base.classes.conversacion
        c = session.query(Conversacion).filter_by(id=id).first()
        if c is None:
            return jsonify({"error": "Conversación no encontrada"}), 404
        result = {col.key: getattr(c, col.key) for col in Conversacion.__table__.columns}
        return jsonify(result)
    finally:
        session.close()


@ia_bp.route("/conversation/<int:id>", methods=["PUT"])
def update_conversation(id):
    """
    Reemplaza una conversación completa por ID
    ---
    tags:
      - ia
    parameters:
      - in: path
        name: id
        type: integer
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
    responses:
      200:
        description: Conversación actualizada
      404:
        description: No encontrada
    """
    session = current_app.Session()
    try:
        Conversacion = current_app.Base.classes.conversacion
        c = session.query(Conversacion).filter_by(id=id).first()
        if c is None:
            return jsonify({"error": "Conversación no encontrada"}), 404
        data = request.get_json()
        for col in Conversacion.__table__.columns:
            if col.key != 'id' and col.key in data:
                setattr(c, col.key, data[col.key])
        session.commit()
        result = {col.key: getattr(c, col.key) for col in Conversacion.__table__.columns}
        return jsonify(result)
    finally:
        session.close()


@ia_bp.route("/conversation/<int:id>", methods=["PATCH"])
def patch_conversation(id):
    """
    Actualiza parcialmente una conversación por ID
    ---
    tags:
      - ia
    parameters:
      - in: path
        name: id
        type: integer
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
    responses:
      200:
        description: Conversación parcialmente actualizada
      404:
        description: No encontrada
    """
    session = current_app.Session()
    try:
        Conversacion = current_app.Base.classes.conversacion
        c = session.query(Conversacion).filter_by(id=id).first()
        if c is None:
            return jsonify({"error": "Conversación no encontrada"}), 404
        data = request.get_json()
        for key, value in data.items():
            if key != 'id' and hasattr(c, key):
                setattr(c, key, value)
        session.commit()
        result = {col.key: getattr(c, col.key) for col in Conversacion.__table__.columns}
        return jsonify(result)
    finally:
        session.close()


@ia_bp.route("/conversation/<int:id>", methods=["DELETE"])
def delete_conversation(id):
    """
    Elimina una conversación por ID
    ---
    tags:
      - ia
    parameters:
      - in: path
        name: id
        type: integer
        required: true
    responses:
      200:
        description: Conversación eliminada
      404:
        description: No encontrada
    """
    session = current_app.Session()
    try:
        Conversacion = current_app.Base.classes.conversacion
        c = session.query(Conversacion).filter_by(id=id).first()
        if c is None:
            return jsonify({"error": "Conversación no encontrada"}), 404
        session.delete(c)
        session.commit()
        return jsonify({"message": f"Conversación {id} eliminada"})
    finally:
        session.close()
