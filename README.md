# Planventure API 🚁

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/github-samples/planventure)

A Flask REST API for planning trips. Users register and log in to receive a
JWT, then create, read, update and delete their own trips, each with
destination, dates, coordinates and a day-by-day itinerary.

## Table of contents

- [Features](#features)
- [Tech stack](#tech-stack)
- [Project structure](#project-structure)
- [Getting started](#-getting-started)
- [Configuration](#configuration)
- [API reference](#-api-reference)
- [Data models](#data-models)
- [Authentication and security](#authentication-and-security)
- [Using the API from a React frontend](#using-the-api-from-a-react-frontend)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Known limitations](#known-limitations)
- [License](#-license)

## Features

- User registration and login with email validation and bcrypt password
  hashing.
- Stateless JWT access tokens with a configurable lifetime.
- Trip CRUD where every trip is private to its owner.
- Automatic day-by-day itinerary template when a trip is created.
- Input validation with consistent JSON error responses.
- CORS configured for React dev servers (Create React App and Vite).
- SQLite by default; any SQLAlchemy-supported database via `DATABASE_URL`.
- Automated tests (`unittest`) covering models, utilities and every route.

## Tech stack

| Area | Library |
| --- | --- |
| Web framework | Flask 2.3.3 |
| ORM | Flask-SQLAlchemy 3.1.1 (SQLAlchemy 2.x) |
| Authentication | Flask-JWT-Extended 4.7.1 |
| Password hashing | bcrypt 5.0.0 |
| CORS | Flask-CORS 4.0.0 |
| Configuration | python-dotenv 1.0.0 |

Developed and tested with Python 3.13.

## Project structure

```text
planventure-api/
├── app.py            # Entry point: config, extensions, blueprints, CORS
├── extensions.py     # Shared db (SQLAlchemy) and jwt (JWTManager) objects
├── init_db.py        # Creates the database tables
├── models/
│   ├── user.py       # User model (email, password_hash, timestamps)
│   └── trip.py       # Trip model (owner, dates, coordinates, itinerary)
├── routes/
│   ├── auth.py       # /auth/register, /auth/login, /auth/me
│   └── trips.py      # /api/trips CRUD
├── utils/
│   ├── auth.py       # login_required decorator, get_current_user()
│   ├── itinerary.py  # generate_default_itinerary()
│   ├── jwt_utils.py  # generate/verify access tokens
│   ├── responses.py  # error_response() helper
│   ├── security.py   # bcrypt hashing helpers
│   └── validators.py # email and password validation
├── test_*.py         # Test suite
├── requirements.txt
└── .sample.env       # Template for your .env file
```

## 🚀 Getting started

### Prerequisites

- Python 3.11 or newer (developed and tested with 3.13)
- Git - [Download & Install Git](https://git-scm.com/downloads)
- An API client such as [Bruno](https://github.com/usebruno/bruno) (or curl)
- A code editor - [VS Code](https://code.visualstudio.com/download) is
  recommended
- Optional: a GitHub account and
  [GitHub Copilot](https://gh.io/gfb-copilot) to build along with
  [PROMPTS.md](planventure-api/PROMPTS.md)

### Build along in a Codespace

Click the "Open in GitHub Codespaces" button above to start developing in a
GitHub Codespace.

### Local setup

1. Clone the repository and go to the API directory:

   ```sh
   cd planventure-api
   ```

2. Create and activate a virtual environment:

   ```sh
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```

   If PowerShell blocks `Activate.ps1` (execution policy), use
   `venv\Scripts\activate.bat` from Command Prompt, or skip activation and run
   commands with `venv\Scripts\python.exe` instead of `python`.

3. Install the dependencies:

   ```sh
   pip install -r requirements.txt
   ```

4. Create your `.env` file and fill it in (see
   [Configuration](#configuration)):

   ```sh
   cp .sample.env .env       # On Windows: copy .sample.env .env
   ```

   Generate strong secrets with:

   ```sh
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

5. Create the database tables (safe to re-run; existing tables are kept):

   ```sh
   python init_db.py
   ```

   `init_db.py` relaunches itself with the project's `venv` Python if you start
   it with a different interpreter, so `python3 init_db.py` also works.

6. Start the development server:

   ```sh
   flask run --debug
   ```

   The API is now available at <http://127.0.0.1:5000>. Check it with
   `GET /health`, which returns `{"status": "healthy"}`.

## Configuration

Settings come from environment variables, loaded from `planventure-api/.env`
(see [.sample.env](planventure-api/.sample.env)). Variables that are already
set in the environment take precedence over `.env`.

| Variable | Default | Description |
| --- | --- | --- |
| `SECRET_KEY` | none | Flask secret key. Set it to a long random value. |
| `JWT_SECRET_KEY` | `SECRET_KEY` | Key used to sign JWTs. Use a random value of 32+ characters. |
| `JWT_ACCESS_TOKEN_EXPIRES_MINUTES` | `60` | Access token lifetime in minutes. |
| `DATABASE_URL` | `sqlite:///planventure.db` | SQLAlchemy URL. Relative SQLite paths are created in the `instance/` folder. |
| `CORS_ORIGINS` | `http://localhost:3000,http://localhost:5173` | Comma-separated origins allowed to call the API from a browser. |

Notes:

- Replace every `your-...-here` placeholder from `.sample.env`. An invalid
  `DATABASE_URL` stops the app from starting, and a placeholder
  `CORS_ORIGINS` blocks all browser requests.
- For production, add your deployed frontend URL to `CORS_ORIGINS` and run the
  app with a production server instead of the Flask development server.

## 📚 API reference

Base URL for local development: `http://127.0.0.1:5000`

### Conventions

- Requests and responses use JSON (`Content-Type: application/json`).
- Protected routes need the header `Authorization: Bearer <access_token>`.
- Errors always look like `{"error": "<message>"}`.
- Trailing slashes are accepted on the trip routes (`/api/trips` and
  `/api/trips/`).
- Unknown fields in request bodies are ignored.
- Timestamps are ISO 8601 strings in UTC; dates are `YYYY-MM-DD`.

### Endpoint summary

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| GET | `/` | No | Welcome message |
| GET | `/health` | No | Health check |
| POST | `/auth/register` | No | Create an account, returns a token |
| POST | `/auth/login` | No | Log in, returns a token |
| GET | `/auth/me` | Yes | Current user |
| POST | `/api/trips` | Yes | Create a trip |
| GET | `/api/trips` | Yes | List your trips |
| GET | `/api/trips/<id>` | Yes | Get one trip |
| PUT / PATCH | `/api/trips/<id>` | Yes | Update a trip |
| DELETE | `/api/trips/<id>` | Yes | Delete a trip |

### General

`GET /` returns `{"message": "Welcome to PlanVenture API"}` and `GET /health`
returns `{"status": "healthy"}`.

### Authentication

#### `POST /auth/register`

Request:

```json
{ "email": "test@email.com", "password": "test1234" }
```

- `email` must be a valid address (at most 255 characters). It is trimmed and
  stored in lowercase, and must be unique.
- `password` must be at least 8 characters and at most 72 bytes.

Response `201 Created`:

```json
{
  "message": "User registered successfully",
  "user": {
    "id": 1,
    "email": "test@email.com",
    "created_at": "2027-01-01T10:00:00.000000",
    "updated_at": "2027-01-01T10:00:00.000000"
  },
  "access_token": "<jwt>"
}
```

| Status | Meaning |
| --- | --- |
| 400 | Body is not a JSON object, email is invalid, or password is invalid |
| 409 | Email already registered |

#### `POST /auth/login`

Request: same body as register.

Response `200 OK`: same shape as register with `"message": "Login
successful"`.

| Status | Meaning |
| --- | --- |
| 400 | Body is not a JSON object, or email or password is missing |
| 401 | Unknown email or wrong password (identical response for both) |

#### `GET /auth/me`

Returns `{"user": {...}}` for the token's owner.

| Status | Meaning |
| --- | --- |
| 401 | Missing, invalid or expired token, or the user no longer exists |

### Trips

All trip routes require a token and only ever access the logged-in user's
trips. A trip that belongs to someone else returns `404`, exactly like a trip
that does not exist.

#### Trip fields

| Field | Type | Required on create | Rules |
| --- | --- | --- | --- |
| `destination` | string | Yes | Non-empty, at most 255 characters, trimmed |
| `start_date` | string | Yes | `YYYY-MM-DD`, a real calendar date |
| `end_date` | string | Yes | `YYYY-MM-DD`, not before `start_date` |
| `latitude` | number or null | No | -90 to 90; send together with `longitude` |
| `longitude` | number or null | No | -180 to 180; send together with `latitude` |
| `itinerary` | array or object | No | Any JSON array or object; generated if omitted |

Response representation:

```json
{
  "id": 1,
  "user_id": 1,
  "destination": "Lisbon, Portugal",
  "start_date": "2027-05-01",
  "end_date": "2027-05-08",
  "latitude": 38.7223,
  "longitude": -9.1393,
  "itinerary": [],
  "created_at": "2027-01-01T10:00:00.000000",
  "updated_at": "2027-01-01T10:00:00.000000"
}
```

#### `POST /api/trips`

Request:

```json
{
  "destination": "Lisbon, Portugal",
  "start_date": "2027-05-01",
  "end_date": "2027-05-08",
  "latitude": 38.7223,
  "longitude": -9.1393,
  "itinerary": [
    { "day": 1, "title": "Arrival", "activities": ["Check in", "Alfama walk"] },
    { "day": 2, "title": "Belem", "activities": ["Belem Tower"] }
  ]
}
```

Response `201 Created`: `{"trip": {...}}`.

If `itinerary` is omitted, a template with one entry per day (both dates
included) is created:

```json
{ "day": 1, "date": "2027-05-01", "title": "Day 1", "activities": [], "notes": "" }
```

Send `"itinerary": []` to start with an empty itinerary. For trips longer than
365 days, or invalid ranges, no template is generated. `user_id` and `id` in
the request are ignored; the trip always belongs to the caller.

#### `GET /api/trips`

Response `200 OK`: `{"trips": [...]}` ordered by `start_date`. Returns an
empty list if you have no trips.

#### `GET /api/trips/<id>`

Response `200 OK`: `{"trip": {...}}`.

#### `PUT /api/trips/<id>` and `PATCH /api/trips/<id>`

Both methods behave the same: only the fields you send are changed. At least
one trip field is required.

```json
{ "destination": "Porto, Portugal", "end_date": "2027-05-10" }
```

- The result is validated against the stored values, so changing only
  `end_date` to a date before the stored `start_date` is rejected.
- Send `"latitude": null, "longitude": null` to clear the coordinates.
- Updates never regenerate the itinerary, so your edits are kept.

Response `200 OK`: `{"trip": {...}}`.

#### `DELETE /api/trips/<id>`

Response `204 No Content` with an empty body.

#### Trip error responses

| Status | Meaning |
| --- | --- |
| 400 | Invalid or missing fields, non-object body, or an empty update |
| 401 | Missing, invalid or expired token |
| 404 | Trip not found (or not yours) |

### Example session

Using curl in a Unix-style shell:

```sh
# 1. Register (or log in) and note the access_token in the response
curl -X POST http://127.0.0.1:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@email.com", "password": "test1234"}'

# 2. Create a trip
curl -X POST http://127.0.0.1:5000/api/trips \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"destination": "Kyoto, Japan", "start_date": "2027-10-10", "end_date": "2027-10-17"}'

# 3. List, update and delete
curl http://127.0.0.1:5000/api/trips -H "Authorization: Bearer $TOKEN"
curl -X PATCH http://127.0.0.1:5000/api/trips/1 \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"destination": "Osaka, Japan"}'
curl -X DELETE http://127.0.0.1:5000/api/trips/1 \
  -H "Authorization: Bearer $TOKEN"
```

In PowerShell, use `curl.exe` (not the `curl` alias) or an API client such as
Bruno, which avoids JSON quoting problems.

## Data models

### User (`users`)

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer | Primary key |
| `email` | string(255) | Required, unique, indexed, stored lowercase |
| `password_hash` | string(255) | Required; bcrypt hash, never returned by the API |
| `created_at` | datetime (UTC) | Set on insert |
| `updated_at` | datetime (UTC) | Refreshed on every update |

A user has many trips (`User.trips`); deleting a user through SQLAlchemy also
deletes their trips.

### Trip (`trips`)

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer | Primary key |
| `user_id` | integer | Required, foreign key to `users.id`, indexed |
| `destination` | string(255) | Required |
| `start_date` | date | Required |
| `end_date` | date | Required; database check `end_date >= start_date` |
| `latitude` | float | Optional; database check -90 to 90 |
| `longitude` | float | Optional; database check -180 to 180 |
| `itinerary` | JSON | Required; defaults to an empty list |
| `created_at` | datetime (UTC) | Set on insert |
| `updated_at` | datetime (UTC) | Refreshed on every update |

Tables are created with `python init_db.py` (`db.create_all()`).

## Authentication and security

- **Passwords** are hashed with bcrypt (cost 12) with a random salt embedded in
  the hash. Plain-text passwords are never stored or returned. bcrypt only
  uses the first 72 bytes, so longer passwords are rejected.
- **Tokens** are signed JWT access tokens whose subject is the user id. They
  expire after `JWT_ACCESS_TOKEN_EXPIRES_MINUTES`. Refresh tokens are not
  accepted as access tokens.
- **Login errors** are identical for unknown emails and wrong passwords, and a
  password check always runs, so neither the message nor the response time
  reveals whether an email is registered.
- **Authorization**: trips are filtered by the token's user on every query;
  other users' trips return `404`.
- **Protecting new routes**: put the `login_required` decorator from
  [utils/auth.py](planventure-api/utils/auth.py) under `@route`, then call
  `get_current_user()` inside the view:

  ```python
  from utils.auth import get_current_user, login_required

  @bp.route('/example')
  @login_required
  def example():
      return {'email': get_current_user().email}
  ```

- Keep `.env` out of version control (it is already in `.gitignore`) and use
  different secrets for each environment.

## Using the API from a React frontend

```js
const API = 'http://127.0.0.1:5000';

const { access_token } = await fetch(`${API}/auth/login`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password }),
}).then((r) => r.json());

const { trips } = await fetch(`${API}/api/trips`, {
  headers: { Authorization: `Bearer ${access_token}` },
}).then((r) => r.json());
```

CORS allows `http://localhost:3000` and `http://localhost:5173` by default, and
the methods and headers above. Authentication uses the `Authorization` header
rather than cookies, so `credentials: 'include'` is not needed.

## Testing

Run the whole suite from the `planventure-api` directory:

```sh
python -m unittest discover
```

Add `-v` for per-test output, or run one file, for example
`python -m unittest test_trips`. Tests use in-memory SQLite databases and do
not touch `instance/planventure.db`.

| File | Covers |
| --- | --- |
| `test_app.py` | Configuration, health routes, CORS, JWT error responses |
| `test_models.py` | User and Trip models, constraints, relationships |
| `test_security.py` | Password hashing helpers |
| `test_jwt_utils.py` | Token generation and validation |
| `test_auth.py` | Register, login, `/auth/me`, `login_required` |
| `test_trips.py` | Trip CRUD, validation and ownership rules |
| `test_itinerary.py` | Default itinerary generation |

## Troubleshooting

- **`ModuleNotFoundError: No module named 'sqlalchemy'`**: you ran a Python
  that is not the project's virtual environment. Activate `venv` or use
  `venv\Scripts\python.exe` (`venv/bin/python` on macOS and Linux).
- **`Could not parse SQLAlchemy URL`**: `DATABASE_URL` is still a placeholder.
  Set it to a valid URL such as `sqlite:///planventure.db`.
- **Changed `.env` but nothing changes**: environment variables already set in
  your terminal win over `.env`. VS Code with
  `python.terminal.useEnvFile` enabled copies `.env` into a terminal when it is
  opened, so after editing `.env` open a new terminal or clear the variable
  (PowerShell: `Remove-Item Env:DATABASE_URL`), then restart the server.
- **`404` on `/trips`**: trip routes live under `/api/trips`.
- **`401` on a protected route**: send `Authorization: Bearer <access_token>`;
  tokens expire (default 60 minutes), so log in again.
- **Browser blocks requests (CORS)**: add your frontend's exact origin
  (scheme, host and port) to `CORS_ORIGINS` and restart.
- **JWT key length warning**: use a `JWT_SECRET_KEY` of at least 32 characters.

## Known limitations

- No database migrations: `create_all()` only creates missing tables. After
  changing existing columns, use a migration tool or recreate the development
  database (delete `instance/planventure.db`).
- SQLite does not enforce foreign keys by default, so deleting a user with raw
  SQL leaves their trips behind. Deleting through SQLAlchemy removes them.
- No refresh tokens, logout or token revocation, and no rate limiting on login
  or registration.
- Email validation checks the format only; it does not verify the address.
- Pagination and filtering are not implemented for `GET /api/trips`.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE)
file for details.
