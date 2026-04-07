from app import db
from datetime import datetime

class Misiones(db.Model):
    __tablename__='Misiones'
    user_id = db.Column(db.Integer, primary_key=True)
    mision_type = db.Column(db.String(100), nullable = False)
    status = db.Column(db.String(100), nullable = False)
    resolution = db.Column(db.String(100), nullable = False)