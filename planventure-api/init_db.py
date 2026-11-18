from sqlalchemy import inspect, text
from app import create_app, db
from models import User

def add_missing_columns():
    """Add columns introduced after a database was first created (create_all skips existing tables)."""
    columns = {column['name'] for column in inspect(db.engine).get_columns('trips')}
    if 'title' not in columns:
        with db.engine.begin() as connection:
            connection.execute(text('ALTER TABLE trips ADD COLUMN title VARCHAR(200)'))
        print("Added trips.title column")

def init_db():
    app = create_app()
    with app.app_context():
        # Create all database tables
        db.create_all()
        add_missing_columns()
        print("Database tables created successfully!")

if __name__ == '__main__':
    init_db()
