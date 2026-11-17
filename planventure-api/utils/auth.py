from functools import wraps

from flask import g, jsonify, request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from extensions import db
from models import User


def login_required(view):
    """Require a valid access token and load its user into g.current_user.

    Missing, invalid, expired or refresh tokens are rejected with a JSON 401 by the
    JWT error handlers in extensions.py; a token for a deleted user gets a 401 here.
    """
    @wraps(view)
    def wrapper(*args, **kwargs):
        if request.method == 'OPTIONS':
            # CORS preflight requests never carry credentials
            return view(*args, **kwargs)

        verify_jwt_in_request()
        try:
            user = db.session.get(User, int(get_jwt_identity()))
        except (TypeError, ValueError):
            user = None
        if user is None:
            return jsonify({'error': 'User not found'}), 401

        g.current_user = user
        return view(*args, **kwargs)

    return wrapper


def get_current_user():
    """Return the authenticated user inside a login_required view."""
    return g.get('current_user')
