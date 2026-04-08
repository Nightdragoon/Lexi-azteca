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
from flask_cors import CORS

Base = automap_base()


def create_app():
    app = Flask(__name__)
    CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)
    Swagger(app, template={
        "info": {
            "title": "Lexi Azteca API",
            "description": "Documentación de la API",
            "version": "1.0.0"
        }
    })

    db_url = os.getenv('DATABASE_URL')
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)

    Base.metadata.create_all(engine)

    app.engine = engine
    app.Session = Session

    app.register_blueprint(prueba_bp)
    app.register_blueprint(ia_bp)
    app.register_blueprint(usuario_bp)
    app.register_blueprint(wa_bp)

    return app
