from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # farmer, labour, employer
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Farmer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    full_name = db.Column(db.String(120), nullable=False)
    village = db.Column(db.String(120))
    phone = db.Column(db.String(15))
    land_size = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Labour(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    full_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(15))
    work_type = db.Column(db.String(50))
    location = db.Column(db.String(80))
    experience = db.Column(db.Integer)
    rating = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employer_name = db.Column(db.String(120), nullable=False)
    district = db.Column(db.String(80), nullable=False)
    wage = db.Column(db.Float)
    experience_required = db.Column(db.String(50))
    min_rating = db.Column(db.Integer, default=1)
    status = db.Column(db.String(20), default="open")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Prediction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    crop_year = db.Column(db.Integer)
    area = db.Column(db.Float)
    rainfall = db.Column(db.Float)
    fertilizer = db.Column(db.Float)
    pesticide = db.Column(db.Float)
    predicted_yield = db.Column(db.String(500))
    ai_analysis = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_message = db.Column(db.Text, nullable=False)
    ai_response = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(20), default="english")
    was_voice = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
