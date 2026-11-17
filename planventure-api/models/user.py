from datetime import datetime, timezone

from sqlalchemy.orm import validates

from extensions import db
from utils.security import hash_password, verify_password


def utcnow():
    return datetime.now(timezone.utc)


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=utcnow
    )
    updated_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    trips = db.relationship(
        'Trip', back_populates='user', cascade='all, delete-orphan', order_by='Trip.start_date'
    )

    @validates('email')
    def normalize_email(self, key, value):
        return value.strip().lower()

    def set_password(self, password):
        self.password_hash = hash_password(password)

    def check_password(self, password):
        return verify_password(password, self.password_hash)

    def to_dict(self):
        # password_hash is intentionally never serialized
        return {
            'id': self.id,
            'email': self.email,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

    def __repr__(self):
        return f'<User {self.email}>'
