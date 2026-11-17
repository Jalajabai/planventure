from flask import jsonify
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
jwt = JWTManager()


@jwt.unauthorized_loader
def missing_token(reason):
    return jsonify({"error": reason}), 401


@jwt.invalid_token_loader
def invalid_token(reason):
    return jsonify({"error": reason}), 401


@jwt.expired_token_loader
def expired_token(jwt_header, jwt_payload):
    return jsonify({"error": "Token has expired"}), 401
