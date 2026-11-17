from sqlalchemy import CheckConstraint

from extensions import db
from models.user import utcnow


class Trip(db.Model):
    __tablename__ = 'trips'
    __table_args__ = (
        CheckConstraint('end_date >= start_date', name='ck_trips_dates_order'),
        CheckConstraint(
            'latitude IS NULL OR latitude BETWEEN -90 AND 90', name='ck_trips_latitude'
        ),
        CheckConstraint(
            'longitude IS NULL OR longitude BETWEEN -180 AND 180', name='ck_trips_longitude'
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True
    )
    destination = db.Column(db.String(255), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    itinerary = db.Column(db.JSON, nullable=False, default=list)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=utcnow
    )
    updated_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    user = db.relationship('User', back_populates='trips')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'destination': self.destination,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'latitude': self.latitude,
            'longitude': self.longitude,
            'itinerary': self.itinerary,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

    def __repr__(self):
        return f'<Trip {self.destination} ({self.start_date} - {self.end_date})>'
