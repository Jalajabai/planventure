from sqlalchemy import inspect, text
from app import create_app, db
from models import User

# Columns added after the first release; create_all() never alters existing tables
NEW_TRIP_COLUMNS = {
    'title': 'VARCHAR(200)',
    'accommodations': 'JSON',
    'transportation': 'JSON',
}

def add_missing_columns():
    """Add any columns from NEW_TRIP_COLUMNS that an existing database doesn't have yet."""
    existing = {column['name'] for column in inspect(db.engine).get_columns('trips')}
    for name, column_type in NEW_TRIP_COLUMNS.items():
        if name not in existing:
            with db.engine.begin() as connection:
                connection.execute(text(f'ALTER TABLE trips ADD COLUMN {name} {column_type}'))
            print(f"Added trips.{name} column")

def init_db():
    app = create_app()
    with app.app_context():
        # Create all database tables
        db.create_all()
        add_missing_columns()
        print("Database tables created successfully!")

if __name__ == '__main__':
    init_db()
