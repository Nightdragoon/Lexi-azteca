from flask import Blueprint, request, jsonify, current_app
from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

usuario_bp = Blueprint('usuario', __name__, url_prefix='/usuario')

DATABASE_URL = os.getenv('DATABASE_URL')

engine = create_engine(DATABASE_URL)

Base = automap_base()
Base.prepare(engine, reflect=True)


@usuario_bp.route("/login", methods=["POST"])
def login():
    """
    Login de usuario
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
            - user_phone
            - password
          properties:
            user_phone:
              type: string
              example: "525619283816"
            password:
              type: string
              example: "password123"
    responses:
      200:
        description: Login exitoso
      401:
        description: Usuario o contraseña incorrectos
    """
    session = current_app.Session()
    try:
        data = request.get_json()
        user_phone = data.get('user_phone')
        password = data.get('password')

        if not user_phone or not password:
            return jsonify({"error": "user_phone y password son requeridos"}), 400

        Usuario = Base.classes.usuarios
        u = session.query(Usuario).filter_by(user_phone=user_phone, password=password).first()

        if u is None:
            return jsonify({"error": "Usuario o contraseña incorrectos"}), 401

        result = {col.key: getattr(u, col.key) for col in Usuario.__table__.columns if col.key != 'password'}
        return jsonify({"message": "Login exitoso", "usuario": result}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()


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
            - user_phone
            - password
          properties:
            user_name:
              type: string
              example: "carlos_mx"
            user_phone:
              type: string
              example: "525619283816"
            onboarding:
              type: boolean
              example: false
            password:
              type: string
              example: "password123"
    responses:
      201:
        description: Usuario creado
      400:
        description: Datos inválidos
    """
    session = current_app.Session()
    try:
        Usuario = Base.classes.usuarios
        data = request.get_json()
        data.pop('user_id', None)
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
        Usuario = Base.classes.usuarios
        usuarios = session.query(Usuario).all()
        result = [
            {col.key: getattr(u, col.key) for col in Usuario.__table__.columns}
            for u in usuarios
        ]
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()


@usuario_bp.route("/<int:user_id>", methods=["GET"])
def get_usuario(user_id):
    """
    Obtiene un usuario por ID
    ---
    tags:
      - usuario
    parameters:
      - in: path
        name: user_id
        type: integer
        required: true
    responses:
      200:
        description: Usuario encontrado
      404:
        description: No encontrado
    """
    session = current_app.Session()
    try:
        Usuario = Base.classes.usuarios
        u = session.query(Usuario).filter_by(user_id=user_id).first()
        if u is None:
            return jsonify({"error": "Usuario no encontrado"}), 404
        result = {col.key: getattr(u, col.key) for col in Usuario.__table__.columns}
        return jsonify(result)
    finally:
        session.close()


@usuario_bp.route("/<int:user_id>", methods=["PUT"])
def update_usuario(user_id):
    """
    Actualiza un usuario por ID
    ---
    tags:
      - usuario
    parameters:
      - in: path
        name: user_id
        type: integer
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            user_name:
              type: string
              example: "carlos_mx"
            user_phone:
              type: string
              example: "525619283816"
            onboarding:
              type: boolean
              example: true
            password:
              type: string
              example: "nueva_password"
    responses:
      200:
        description: Usuario actualizado
      404:
        description: No encontrado
    """
    session = current_app.Session()
    try:
        Usuario = Base.classes.usuarios
        u = session.query(Usuario).filter_by(user_id=user_id).first()
        if u is None:
            return jsonify({"error": "Usuario no encontrado"}), 404
        data = request.get_json()
        data.pop('user_id', None)
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


@usuario_bp.route("/<int:user_id>", methods=["DELETE"])
def delete_usuario(user_id):
    """
    Elimina un usuario por ID
    ---
    tags:
      - usuario
    parameters:
      - in: path
        name: user_id
        type: integer
        required: true
    responses:
      200:
        description: Usuario eliminado
      404:
        description: No encontrado
    """
    session = current_app.Session()
    try:
        Usuario = Base.classes.usuarios
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
