from app import db
from datetime import datetime

class Usuarios(db.Model):
    __tablename__='Usuarios'


    #aqui insertar un UUID mejor
    user_id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(100), nullable = False)
    user_name = db.Column(db.String(100), nullable = False)
    # user_alias = db.Column(db.String(100), nullable = False)
    #revisar bools
    onboarding = db.Column(db.boolean, nullable = False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate = datetime.utcnow)
