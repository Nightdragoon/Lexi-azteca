import os
from flask import Flask, Blueprint, jsonify
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from flasgger import Swagger
from app.modelos.Misiones_model import Misiones

Base = automap_base()


# ── Blueprint de prueba ──────────────────────────────────────────────────────

prueba_bp = Blueprint('prueba', __name__, url_prefix='/prueba')

@prueba_bp.route('/')
def hello_world():
    """
    Endpoint de prueba
    ---
    tags:
      - prueba
    responses:
      200:
        description: Saludo de prueba
        schema:
          type: string
          example: Hello World!
    """
    return 'Hello World!'


# ── Blueprint de misiones ────────────────────────────────────────────────────

misiones_bp = Blueprint('misiones', __name__, url_prefix='/misiones')

@misiones_bp.route('/')
def get_misiones():
    """
    Lista todas las misiones
    ---
    tags:
      - misiones
    responses:
      200:
        descripcion: Lista de misiones
    """
    session = misiones_bp.Session()
    try:
        misiones = session.query(Misiones).all()
        result = [
            {
                'user_id':           m.id,
                'mision_type':  m.mision_type,
                'status':       m.status,
                'resolution':   m.resolution,
            }
            for m in misiones
        ]
        return jsonify(result)
    finally:
        session.close()


# ── App factory ──────────────────────────────────────────────────────────────

def create_app():
    app = Flask(__name__)

    Swagger(app, template={
        "info": {
            "title": "Lexi Azteca API",
            "description": "Documentación de la API",
            "version": "1.0.0"
        }
    })

    db_url = os.getenv('DATABASE_URL', 'sqlite:///lexi.db')
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)

    Base.metadata.create_all(engine)

    app.engine  = engine
    app.Session = Session

    app.register_blueprint(prueba_bp)
    app.register_blueprint(misiones_bp)

    return app


# ── Main ─────────────────────────────────────────────────────────────────────

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5432))
    app.run(host='0.0.0.0', port=port, debug=True)
