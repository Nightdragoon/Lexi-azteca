import os
from flask import Flask, Blueprint
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.rutas.Ia import ia_bp
from app.rutas.usuario import usuario_bp
from app.rutas.missiones import ms_bl
from app.rutas.telegram import tg_bp
from flasgger import Swagger
from flask_cors import CORS

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


# ── App factory ──────────────────────────────────────────────────────────────

def create_app():
    app = Flask(__name__)

    CORS(app)

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
    app.register_blueprint(ia_bp)
    app.register_blueprint(usuario_bp)
    app.register_blueprint(ms_bl)
    app.register_blueprint(tg_bp)

    return app


# ── Main ─────────────────────────────────────────────────────────────────────

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5432))
    app.run(host='0.0.0.0', port=port, debug=True)
