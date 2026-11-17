import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS
from extensions import db, jwt
import models  # noqa: F401  (registers models with SQLAlchemy)
from routes.auth import auth_bp
from routes.trips import trips_bp

load_dotenv(Path(__file__).with_name('.env'))

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL', 'sqlite:///planventure.db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Falls back to SECRET_KEY when unset
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(
    minutes=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES_MINUTES', '60'))
)

db.init_app(app)
jwt.init_app(app)
app.register_blueprint(auth_bp)
app.register_blueprint(trips_bp)
CORS(app, origins=[
    origin.strip() for origin in os.getenv('CORS_ORIGINS', '*').split(',')
    if origin.strip()
])


@app.route('/')
def home():
    return jsonify({"message": "Welcome to PlanVenture API"})

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    app.run()
