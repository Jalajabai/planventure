import bcrypt

# bcrypt only uses the first 72 bytes; longer input would be silently truncated
MAX_PASSWORD_BYTES = 72
DEFAULT_ROUNDS = 12


def _encode_password(password):
    if not isinstance(password, str) or not password:
        raise ValueError('Password must be a non-empty string')
    encoded = password.encode('utf-8')
    if len(encoded) > MAX_PASSWORD_BYTES:
        raise ValueError(f'Password must be at most {MAX_PASSWORD_BYTES} bytes')
    return encoded


def generate_salt(rounds=DEFAULT_ROUNDS):
    """Return a new random bcrypt salt (includes the cost factor)."""
    return bcrypt.gensalt(rounds=rounds).decode('ascii')


def hash_password(password, salt=None):
    """Hash a password with bcrypt; the salt is embedded in the returned hash."""
    salt_bytes = salt.encode('ascii') if salt else bcrypt.gensalt(rounds=DEFAULT_ROUNDS)
    return bcrypt.hashpw(_encode_password(password), salt_bytes).decode('ascii')


def verify_password(password, password_hash):
    """Check a password against a stored hash; malformed input never matches."""
    try:
        return bcrypt.checkpw(_encode_password(password), password_hash.encode('ascii'))
    except (ValueError, AttributeError, UnicodeEncodeError):
        return False
