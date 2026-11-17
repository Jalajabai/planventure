import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
VENV_DIR = BASE_DIR / 'venv'
VENV_PYTHON = VENV_DIR / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')


def run_with_project_venv():
    """Re-run this script with the project's venv Python if started from another interpreter."""
    if VENV_PYTHON.exists() and Path(sys.prefix).resolve() != VENV_DIR.resolve():
        raise SystemExit(subprocess.call([str(VENV_PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]]))


def init_db():
    from sqlalchemy import inspect
    from sqlalchemy.exc import ArgumentError

    # Imported here because an invalid DATABASE_URL fails when app.py is imported
    try:
        from app import app, db
    except ArgumentError as error:
        raise SystemExit(
            f"Invalid DATABASE_URL ({error}).\n"
            "Set it in .env, e.g. DATABASE_URL=sqlite:///planventure.db"
        )

    with app.app_context():
        db.create_all()
        url = db.engine.url
        tables = inspect(db.engine).get_table_names()
        print(f"Database ready: {url.database or url.render_as_string(hide_password=True)}")
        print("Tables:", ", ".join(sorted(tables)) or "(none)")


if __name__ == '__main__':
    run_with_project_venv()
    init_db()
