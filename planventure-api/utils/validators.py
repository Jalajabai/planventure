import re

from utils.security import MAX_PASSWORD_BYTES

MAX_EMAIL_LENGTH = 255
MIN_PASSWORD_LENGTH = 8

_LOCAL_ATOM = r"[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+"
_DOMAIN_LABEL = r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?'
_EMAIL_RE = re.compile(
    rf'^{_LOCAL_ATOM}(?:\.{_LOCAL_ATOM})*@(?:{_DOMAIN_LABEL}\.)+[A-Za-z]{{2,63}}$'
)


def is_valid_email(email):
    if not isinstance(email, str) or len(email) > MAX_EMAIL_LENGTH:
        return False
    local_part = email.partition('@')[0]
    return len(local_part) <= 64 and _EMAIL_RE.fullmatch(email) is not None


def validate_password(password):
    """Return an error message for an unacceptable password, or None if it is fine."""
    if not isinstance(password, str):
        return 'Password is required'
    if len(password) < MIN_PASSWORD_LENGTH:
        return f'Password must be at least {MIN_PASSWORD_LENGTH} characters'
    if len(password.encode('utf-8')) > MAX_PASSWORD_BYTES:
        return f'Password must be at most {MAX_PASSWORD_BYTES} bytes'
    return None
