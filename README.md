# Spotify Charts Snapshot

This project automates the process of logging in to Spotify Charts, capturing a bearer token, downloading weekly regional/global chart data, and importing that data into a local SQLite database.

The project is no longer actively maintained. The code is provided as a snapshot of a working system.

---

## Scripts

- `get_spotify_token.py`  
  Automates browser-based login using Playwright to capture a Spotify bearer token and save it to `.env`.

- `fetch_weekly_charts.py`  
  Uses the saved token to download weekly chart data for multiple countries and saves the result as JSON.

- `import_charts_db.py`  
  Imports one or more weekly JSON files into a local SQLite database (`spotify_charts.db`).

---

## Usage

Install dependencies:

```
pip install -r requirements.txt
```

Create a `.env` file using the provided template (this file is ignored by Git):

```
cp .env.example .env
```

Then run:

```
python get_spotify_token.py
python fetch_weekly_charts.py
python import_charts_to_sqlite.py --all
```

---

## GitHub Actions

A one-time GitHub Actions workflow (`.github/workflows/spotify-action.yml`) is included for manual execution. It uses repository secrets for login and downloads the most recent charts.

Required secrets:
- SPOTIFY_USERNAME
- SPOTIFY_PASSWORD

The workflow does not commit or push any files. Files are temporary unless explicitly uploaded as artifacts.

---

## License

MIT License
