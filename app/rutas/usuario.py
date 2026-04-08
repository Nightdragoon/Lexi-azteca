from flask import Blueprint, request, jsonify, current_app
from app.modelos.modelo_usuario import Usuarios

usuario_bp = Blueprint('usuario', __name__, url_prefix='/usuario')


@usuario_bp.route("/", methods=["POST"])
def create_usuario():
    """
    Crea un nuevo usuario
    ---
    tags:
      - usuario
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - user_name
          properties:
            user_id:
              type: string
              example: "a1b2c3d4-0001-4e5f-8a9b-000000000001"
            user_name:
              type: string
              example: "carlos_mx"
            onboarding:
              type: boolean
              example: true
            created_at:
              type: string
              example: "2026-01-10 08:00:00"
    responses:
      201:
        description: Usuario creado
      400:
        description: Datos inválidos
    """
    session = current_app.Session()
    try:
        Usuario = Usuarios
        data = request.get_json()
        nuevo = Usuario(**data)
        session.add(nuevo)
        session.commit()
        result = {col.key: getattr(nuevo, col.key) for col in Usuario.__table__.columns}
        return jsonify(result), 201
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()


@usuario_bp.route("/", methods=["GET"])
def get_usuarios():
    """
    Lista todos los usuarios
    ---
    tags:
      - usuario
    responses:
      200:
        description: Lista de usuarios
    """
    session = current_app.Session()
    try:
        Usuario = Usuarios
        usuarios = session.query(Usuario).all()
        result = [
            {col.key: getattr(u, col.key) for col in Usuario.__table__.columns}
            for u in usuarios
        ]
        return jsonify(result)
    finally:
        session.close()


@usuario_bp.route("/<user_id>", methods=["GET"])
def get_usuario(user_id):
    """
    Obtiene un usuario por ID
    ---
    tags:
      - usuario
    parameters:
      - in: path
        name: user_id
        type: string
        required: true
    responses:
      200:
        description: Usuario encontrado
      404:
        description: No encontrado
    """
    session = current_app.Session()
    try:
        Usuario = Usuarios
        u = session.query(Usuario).filter_by(user_id=user_id).first()
        if u is None:
            return jsonify({"error": "Usuario no encontrado"}), 404
        result = {col.key: getattr(u, col.key) for col in Usuario.__table__.columns}
        return jsonify(result)
    finally:
        session.close()


@usuario_bp.route("/<user_id>", methods=["PUT"])
def update_usuario(user_id):
    """
    Reemplaza un usuario completo por ID
    ---
    tags:
      - usuario
    parameters:
      - in: path
        name: user_id
        type: string
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
    responses:
      200:
        description: Usuario actualizado
      404:
        description: No encontrado
    """
    session = current_app.Session()
    try:
        Usuario = Usuarios
        u = session.query(Usuario).filter_by(user_id=user_id).first()
        if u is None:
            return jsonify({"error": "Usuario no encontrado"}), 404
        data = request.get_json()
        for col in Usuario.__table__.columns:
            if col.key != 'user_id' and col.key in data:
                setattr(u, col.key, data[col.key])
        session.commit()
        result = {col.key: getattr(u, col.key) for col in Usuario.__table__.columns}
        return jsonify(result)
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()


@usuario_bp.route("/<user_id>", methods=["DELETE"])
def delete_usuario(user_id):
    """
    Elimina un usuario por ID
    ---
    tags:
      - usuario
    parameters:
      - in: path
        name: user_id
        type: string
        required: true
    responses:
      200:
        description: Usuario eliminado
      404:
        description: No encontrado
    """
    session = current_app.Session()
    try:
        Usuario = Usuarios
        u = session.query(Usuario).filter_by(user_id=user_id).first()
        if u is None:
            return jsonify({"error": "Usuario no encontrado"}), 404
        session.delete(u)
        session.commit()
        return jsonify({"message": f"Usuario {user_id} eliminado"})
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()
