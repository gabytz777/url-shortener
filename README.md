# Simple Flask URL Shortener ✅

A tiny self-hosted URL shortener implemented in Python + Flask with SQLite storage.

## Requirements
- Python 3.8+
- Install dependencies: pip install -r requirements.txt

## Run the server
1. Start the app:

   python app.py

2. Open your browser at http://localhost:5000 and paste a URL to shorten.

## CLI usage
- With the server running, run:

  python shorten.py https://example.com

This prints the shortened URL.

## Notes
- Data is stored in `urls.db` (SQLite) in the project folder.
- To change DB path, set `URL_SHORTENER_DB` environment variable.
- Improvements you might want: custom codes, expiry, user accounts, analytics, tests.
