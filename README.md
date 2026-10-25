# Simple URL Shortener

A self-hosted URL shortener built with Python, Flask, SQLite, and Waitress. It can create short links that never expire or automatically expire after a preset time or an exact date and time.

## Features

- Shorten long URLs with randomly generated codes
- Optional expiration: 30 minutes, 1 hour, 6 hours, 1 day, 7 days, or any custom date & time (up to 10 years in the future)
- Expired links return `410 Gone`
- Visit counts are tracked
- Works behind a reverse proxy (trusts `X-Forwarded-Proto` for correct HTTPS short URLs)
- SQLite storage with automatic schema migration

## Requirements

- Python 3.8+
- Dependencies listed in [`requirements.txt`](requirements.txt)

Install them with:

```bash
pip install -r requirements.txt
```

## Running locally

Start the development server:

```bash
python app.py
```

Then open [http://localhost:5000](http://localhost:5000), paste a URL, and choose when it should expire (or leave it as *Never*).

## Using the CLI

With the server running, you can shorten links from the terminal:

```bash
python shorten.py https://example.com
```

Add an expiration with a duration:

```bash
python shorten.py https://example.com -e 30m
python shorten.py https://example.com -e 12h
python shorten.py https://example.com -e 2d
```

Or pick an exact date/time:

```bash
python shorten.py https://example.com -e "2026-12-31 18:00"
python shorten.py https://example.com -e 2030-01-01T12:00:00Z
```

## API

### `POST /shorten`

Send JSON (or form data):

```json
{"url": "https://example.com/very/long/link", "expires_in": 3600}
```

Or an exact expiration time:

```json
{"url": "https://example.com/very/long/link", "expires_at": "2026-12-31T18:00:00Z"}
```

- `url` (required) — the long URL to shorten. If it has no scheme, `http://` is added.
- `expires_in` (optional) — seconds from now. Must be greater than 0 and at most 10 years.
- `expires_at` (optional) — Unix timestamp or ISO 8601 date/time. Must be in the future and at most 10 years away.

Response:

```json
{
  "short_url": "http://localhost:5000/Ab12Cd",
  "code": "Ab12Cd",
  "expires_at": "2026-10-25T11:23:45.123456+00:00"
}
```

If `expires_at` is `null`, the link never expires.

### `GET /<code>`

Redirects to the original URL with a `302` redirect. Returns `410 Gone` if the link has expired, or `404 Not Found` if the code does not exist.

## Production

The included [`url-shortener.service`](url-shortener.service) is configured to run with [Waitress](https://docs.pylonsproject.org/projects/waitress/) behind a reverse proxy. Set `URL_SHORTENER_DB` to change the database location.
