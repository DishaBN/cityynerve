# CityNER

A small Flask-based demo that evaluates city neighborhoods, collects user feedback, and displays simple scores and AQI data.

This README is formatted for GitHub and provides line-by-line installation, configuration, usage and testing instructions.

## Table of Contents

- Project overview
- Features
- Repository layout
- Requirements
- Installation (Windows)
- Configuration
- Running the application
- Testing / Automation script
- Templates and customization
- Security notes
- Troubleshooting
- Contributing
- License

## Project overview

CityNER serves per-city pages with a computed score based on static base values, user feedback stored in SQLite, and optional AQI data fetched from the WAQI API.

Users can sign up / log in, submit feedback per city, and admins can view recent feedback.

## Features

- Per-city score computation using multiple factors (traffic, pollution, cost, safety, water, healthcare, heat, response time, complaints).
- Feedback collection stored in a local SQLite database (`city.db`).
- AQI lookup via the WAQI API with a small caching layer.
- Simple authentication (signup/login) and a dashboard.
- Optional ML components if `numpy` and `scikit-learn` are installed.

## Repository layout

- `app.py` — Main Flask application, routing, DB initialization, scoring logic.
- `city.db` — SQLite database (created automatically on first run).
- `templates/` — Jinja2 templates (UI views).
- `scripts/test_feedback.py` — Simple integration script that exercises feedback submission.
- `.venv/` — (recommended) virtual environment folder — not committed.

## Requirements

- Python 3.8+ recommended.
- Required packages: `Flask`, `requests`.
- Optional (for ML experiments): `numpy`, `scikit-learn`.

If you prefer using `pipenv` or `poetry`, you can adapt the dependency steps below accordingly.

## Installation (Windows)

1. Create a virtual environment and activate it:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Upgrade pip and install required packages:

```powershell
pip install --upgrade pip
pip install Flask requests
```

3. (Optional) Install ML dependencies:

```powershell
pip install numpy scikit-learn
```

4. Ensure `app.py` and `templates/` are present in the project root.

## Configuration

- Open `app.py` and review the `WAQI_TOKEN` value. Replace it with your WAQI token for live AQI lookups. Leave blank to skip external API calls.
- `DB = "city.db"` controls the SQLite database filename. By default the file is created in the project root.
- The app currently uses a generated `app.secret_key` on start. For persistent sessions in development or production, set `app.secret_key` to a fixed secret.

Consider storing secrets in environment variables and reading them in `app.py` (I can add `.env` support on request).

## Running the application

Activate the virtual environment and run:

```powershell
python app.py
```

The server starts in debug mode by default and listens on `http://127.0.0.1:5000/`.

Routes of interest:

- `/` — Home / index listing cities.
- `/view/<city>` — View computed score and AQI for a city.
- `/feedback/<city>` — Submit feedback for a city.
- `/auth` — Sign up / login.
- `/dashboard` — User dashboard (requires login).
- `/admin` — Admin feedback viewer.

## Testing / Automation script

There is a small test script to exercise feedback submission and verify the admin listing.

To run it while the server is running:

```powershell
python scripts/test_feedback.py
```

The script performs a GET to the feedback page, POSTs test feedback, then fetches the admin page and checks for the submitted city entry.

## Templates and customization

UI templates are in the `templates/` folder. Common templates include: `index.html`, `view.html`, `feedback.html`, `admin.html`, `auth.html`, and `dashboard.html`.

Edit templates to customize UI. If you change form field names, update corresponding logic in `app.py`.

## Security notes

- This project is intended for local development and demonstrations only.
- Do not run the Flask development server with `debug=True` in production.
- Passwords are hashed with SHA-256 inside `app.py`. For production use a stronger algorithm (bcrypt/argon2) and a mature authentication framework.
- Sanitize and validate all user input if adapting the project for public use.

## Troubleshooting

- If AQI lookups fail, check your `WAQI_TOKEN` and network connectivity; the app will continue to function without AQI.
- If database operations fail, check file permissions for `city.db` and ensure the running user can write to the project folder.

## Contributing

Contributions are welcome. Suggested next improvements:

- Add `requirements.txt` or `pyproject.toml` for reproducible installs.
- Add `.env` support for configuration and secrets.
- Replace SHA-256 password hashing with `werkzeug.security` or `bcrypt`.
- Add unit tests and CI configuration.

If you'd like, I can create `requirements.txt`, a `.env` loader, or a `Dockerfile` next — tell me which and I'll add it.

## License

MIT
