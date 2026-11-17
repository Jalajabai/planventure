# Planventure API 🚁

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/github-samples/planventure)

A Flask-based REST API backend for the Planventure application.

## Prerequisites
Before you begin, ensure you have the following:

- A GitHub account - [sign up for FREE](https://github.com)
- Access to GitHub Copilot - [sign up for FREE](https://gh.io/gfb-copilot)!
- A Code Editor - [VS Code](https://code.visualstudio.com/download) is recommended
- API Client (like [Bruno](https://github.com/usebruno/bruno))
- Git - [Download & Install Git](https://git-scm.com/downloads)

## 🚀 Getting Started

## Build along in a Codespace

1. Click the "Open in GitHub Codespaces" button above to start developing in a GitHub Codespace.

### Local Development Setup

If you prefer to develop locally, follow the steps below:

1.Fork and clone the repository and navigate to the [planventue-api](/planventure-api/) directory:
```sh
cd planventure-api
```

2. Create a virtual environment and activate it:
```sh
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```
If PowerShell blocks activation (execution policy), use `venv\Scripts\activate.bat` from Command Prompt, or run commands with `venv\Scripts\python.exe`. Running other scripts with a Python outside the virtual environment causes `ModuleNotFoundError`; `init_db.py` automatically relaunches itself with the project's `venv` if one exists.

3. Install the required dependencies:
```sh
pip install -r requirements.txt
```

4. Create an `.env` file based on [.sample.env](/planventure-api/.sample.env):
```sh
cp .sample.env .env
```

Set `SECRET_KEY` to a private random value. The app loads `.env` from the API
directory without overriding existing environment variables. If you already have
an `.env` file, replace the placeholder `DATABASE_URL` with
`sqlite:///planventure.db` or another valid SQLAlchemy connection URL.

Configuration:

- `DATABASE_URL`: defaults to `sqlite:///planventure.db`, stored in the API's
  `instance` directory. Run `python init_db.py` to create the tables.
- `SECRET_KEY`: Flask signing key; required before using sessions.
- `CORS_ORIGINS`: comma-separated allowed origins, or `*` (the default).
- `JWT_SECRET_KEY`: signing key for JWTs (falls back to `SECRET_KEY` if unset);
  use a random value of at least 32 characters.
- `JWT_ACCESS_TOKEN_EXPIRES_MINUTES`: access token lifetime, default `60`.

JWT helpers live in `utils/jwt_utils.py`: `generate_access_token(user_id)`,
`verify_access_token(token)` (returns the user id or `None`) and
`get_user_from_token(token)`.

5. Create the database tables:
```sh
python init_db.py
```
The script is safe to re-run; it only creates tables that don't exist yet.

6. Start the Flask development server:
```sh
flask run
```

Use `flask --debug run` to explicitly enable the development debugger.

Run the backend tests from the API directory:
```sh
python -m unittest discover
```

## 📚 API Endpoints
- GET / - Welcome message
- GET /health - Health check endpoint
- POST /auth/register - Register a user (`{"email", "password"}`); returns the user and an access token.
  Returns 400 for an invalid email or password (minimum 8 characters, at most 72 bytes) and 409 if the email is already registered.
- POST /auth/login - Log in (`{"email", "password"}`); returns the user and an access token.
  Returns 400 for a missing field and 401 for an unknown email or wrong password (the same response for both).
- GET /auth/me - Current user; requires an `Authorization: Bearer <access_token>` header (401 otherwise).

Protect your own routes with the `login_required` decorator from `utils/auth.py`
(place it below `@route`); inside the view, `get_current_user()` returns the `User`.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.