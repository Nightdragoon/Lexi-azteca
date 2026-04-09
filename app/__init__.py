import os
from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker
from flasgger import Swagger
from app.rutas.Ia import ia_bp
from app.rutas.prueba import prueba_bp
from app.rutas.usuario import usuario_bp
from app.rutas.whatsapp import wa_bp
from app.rutas.ranking import rk_bp
from app.rutas.missiones import ms_bl
from app.rutas.simulador import sim_bl
from app.rutas.historial import historial_bl
from app.rutas.banco import banco_bl
from app.rutas.productos import productos_bl
from app.rutas.telegram import tg_bp
from flask_cors import CORS
from app.scheduler import init_scheduler
from app.seed import seed_usuarios

Base = automap_base()

SWAGGER_TEMPLATE = {
    "swagger": "2.0",
    "info": {
        "title": "Lexi Azteca API",
        "description": "API del backend de Lexi Azteca. Usa esta UI para probar endpoints sin necesidad de Postman.",
        "version": "1.0.0",
        "contact": {
            "name": "Equipo Lexi Azteca"
        }
    },
    "host": "api.lexi-azteca.com",
    "schemes": ["https"],
    "consumes": ["application/json"],
    "produces": ["application/json"],
    "tags": [
        {"name": "usuario",  "description": "Registro, login y gestión de usuarios"},
        {"name": "ranking",  "description": "Ranking semanal por XP"},
        {"name": "misiones", "description": "Misiones del usuario"},
        {"name": "wallet",   "description": "Wallet y transacciones financieras"},
        {"name": "ia",       "description": "Conversación con IA"},
        {"name": "whatsapp", "description": "Integración WhatsApp"},
        {"name": "telegram", "description": "Integración Telegram"},
        {"name": "prueba",   "description": "Endpoints de prueba"},
    ],
}

SWAGGER_CONFIG = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec_1",
            "route": "/apispec_1.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/",
}


def create_app():
    app = Flask(__name__)
    CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)
    Swagger(app, template=SWAGGER_TEMPLATE, config=SWAGGER_CONFIG)

    db_url = os.getenv('DATABASE_URL')
    engine = create_engine(
        db_url,
        pool_size=5,
        max_overflow=0,
        pool_pre_ping=True,
        execution_options={"prepared_statement_cache_size": 0},
    )
    Session = sessionmaker(bind=engine)

    Base.metadata.create_all(engine)

    app.engine = engine
    app.Session = Session

    app.register_blueprint(prueba_bp)
    app.register_blueprint(ia_bp)
    app.register_blueprint(usuario_bp)
    app.register_blueprint(wa_bp)
    app.register_blueprint(rk_bp)
    app.register_blueprint(ms_bl)
    app.register_blueprint(sim_bl)
    app.register_blueprint(historial_bl)
    app.register_blueprint(banco_bl)
    app.register_blueprint(productos_bl)
    app.register_blueprint(tg_bp)
    seed_usuarios(engine)
    init_scheduler(Session)

    return app
