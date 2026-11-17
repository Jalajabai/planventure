from functools import lru_cache

from flask import Blueprint, jsonify, request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from extensions import db
from models import User
from utils.auth import get_current_user, login_required
from utils.jwt_utils import generate_access_token
from utils.responses import error_response
from utils.security import hash_password, verify_password
from utils.validators import is_valid_email, validate_password

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@lru_cache(maxsize=1)
def _dummy_password_hash():
    return hash_password('timing-equalizer')


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return error_response('Request body must be a JSON object', 400)

    email = data.get('email')
    if not isinstance(email, str) or not is_valid_email(email.strip()):
        return error_response('A valid email address is required', 400)
    email = email.strip().lower()

    password = data.get('password')
    password_error = validate_password(password)
    if password_error:
        return error_response(password_error, 400)

    if db.session.execute(select(User).filter_by(email=email)).scalar_one_or_none():
        return error_response('Email already registered', 409)

    user = User(email=email)
    user.set_password(password)
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        # Another request registered the same email after the check above
        db.session.rollback()
        return error_response('Email already registered', 409)

    return jsonify({
        'message': 'User registered successfully',
        'user': user.to_dict(),
        'access_token': generate_access_token(user.id),
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return error_response('Request body must be a JSON object', 400)

    email = data.get('email')
    password = data.get('password')
    if not isinstance(email, str) or not email.strip() or not isinstance(password, str) or not password:
        return error_response('Email and password are required', 400)

    user = db.session.execute(
        select(User).filter_by(email=email.strip().lower())
    ).scalar_one_or_none()

    # Always run a hash check so response time doesn't reveal whether the email exists
    password_ok = verify_password(password, user.password_hash if user else _dummy_password_hash())
    if user is None or not password_ok:
        return error_response('Invalid email or password', 401)

    return jsonify({
        'message': 'Login successful',
        'user': user.to_dict(),
        'access_token': generate_access_token(user.id),
    }), 200


@auth_bp.route('/me', methods=['GET'])
@login_required
def me():
    return jsonify({'user': get_current_user().to_dict()})
