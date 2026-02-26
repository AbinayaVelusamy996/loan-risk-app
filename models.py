from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)

    # keep lowercase for role check
    role = db.Column(db.String(20), default="user")

    # relationship
    predictions = db.relationship("Prediction", backref="user", lazy=True)


class Prediction(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # ✅ THIS IS VERY IMPORTANT
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    applicant_name = db.Column(db.String(100), nullable=False)
    no_of_dependents = db.Column(db.Integer, nullable=False)
    education = db.Column(db.String(50), nullable=False)
    self_employed = db.Column(db.String(50), nullable=False)

    income_annum = db.Column(db.Float, nullable=False)
    loan_amount = db.Column(db.Float, nullable=False)
    loan_term = db.Column(db.Float, nullable=False)
    cibil_score = db.Column(db.Float, nullable=False)

    residential_assets_value = db.Column(db.Float, nullable=False)
    commercial_assets_value = db.Column(db.Float, nullable=False)
    luxury_assets_value = db.Column(db.Float, nullable=False)
    bank_asset_value = db.Column(db.Float, nullable=False)

    loan_status = db.Column(db.String(50), nullable=False)
    risk_level = db.Column(db.String(50), nullable=False)
    probability = db.Column(db.Float, nullable=False)

    # timestamp stays SAME
    timestamp = db.Column(db.DateTime, server_default=db.func.current_timestamp())
