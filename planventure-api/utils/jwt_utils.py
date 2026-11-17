from flask_jwt_extended import create_access_token, decode_token
from flask_jwt_extended.exceptions import JWTExtendedException
from jwt.exceptions import PyJWTError


def generate_access_token(user_id, additional_claims=None):
    """Create a signed access token whose subject is the user's id."""
    return create_access_token(identity=str(user_id), additional_claims=additional_claims)


def verify_access_token(token):
    """Return the user id for a valid, unexpired access token, otherwise None."""
    try:
        claims = decode_token(token)
    except (JWTExtendedException, PyJWTError):
        return None
    if claims.get('type') != 'access':
        return None
    try:
        return int(claims['sub'])
    except (KeyError, TypeError, ValueError):
        return None


def get_user_from_token(token):
    """Return the User for a valid access token, or None if invalid or the user is gone."""
    from extensions import db
    from models import User

    user_id = verify_access_token(token)
    return db.session.get(User, user_id) if user_id is not None else None
