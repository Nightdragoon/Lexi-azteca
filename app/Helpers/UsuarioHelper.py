from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

engine = create_engine(os.getenv('DATABASE_URL'))

Base = automap_base()
Base.prepare(engine, reflect=True)

Session = sessionmaker(bind=engine)


class UsuarioHelper:

    def phone_exists(self, phone: str) -> bool:
        session = Session()
        try:
            Usuario = Base.classes.usuarios
            u = session.query(Usuario).filter_by(user_phone=phone).first()
            return u is not None
        finally:
            session.close()

    def get_by_phone(self, phone: str) -> dict | None:
        session = Session()
        try:
            Usuario = Base.classes.usuarios
            u = session.query(Usuario).filter_by(user_phone=phone).first()
            if u is None:
                return None
            return {col.key: getattr(u, col.key) for col in Usuario.__table__.columns if col.key != 'password'}
        finally:
            session.close()

    def username_exists(self, user_name: str) -> bool:
        session = Session()
        try:
            Usuario = Base.classes.usuarios
            u = session.query(Usuario).filter_by(user_name=user_name).first()
            return u is not None
        finally:
            session.close()

    def get_by_username(self, user_name: str) -> dict | None:
        session = Session()
        try:
            Usuario = Base.classes.usuarios
            u = session.query(Usuario).filter_by(user_name=user_name).first()
            if u is None:
                return None
            return {col.key: getattr(u, col.key) for col in Usuario.__table__.columns if col.key != 'password'}
        finally:
            session.close()
