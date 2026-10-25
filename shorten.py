import argparse
import re
import sys
import time
from datetime import datetime

import requests

DURATION_RE = re.compile(r"^(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?$", re.IGNORECASE)


def parse_expires(value):
    """Parse "30m", "1h30m", "2d" or an ISO 8601 date/time into a Unix timestamp."""
    text = value.strip()
    match = DURATION_RE.match(text)
    if match and any(match.groups()):
        days, hours, minutes = (int(part or 0) for part in match.groups())
        seconds = days * 86400 + hours * 3600 + minutes * 60
        if seconds <= 0:
            raise ValueError("duration must be greater than zero")
        return time.time() + seconds

    try:
        moment = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError(
            "use a duration like 30m, 12h, 2d or a date like 2026-12-31 18:00"
        )
    if moment.tzinfo is None:
        moment = moment.astimezone()
    return moment.timestamp()


def main():
    parser = argparse.ArgumentParser(description="Shorten a URL.")
    parser.add_argument("url", help="the long URL to shorten")
    parser.add_argument(
        "-e",
        "--expires",
        help="when the link should expire: 30m, 12h, 2d or '2026-12-31 18:00'",
    )
    args = parser.parse_args()

    payload = {"url": args.url}
    if args.expires:
        try:
            payload["expires_at"] = parse_expires(args.expires)
        except ValueError as exc:
            parser.error(str(exc))

    try:
        resp = requests.post("http://localhost:5000/shorten", json=payload)
    except requests.exceptions.ConnectionError:
        print("Could not connect to http://localhost:5000 — make sure the server is running")
        sys.exit(1)

    if resp.status_code == 200:
        data = resp.json()
        print("Short URL:", data["short_url"])
        if data.get("expires_at"):
            print("Expires:", data["expires_at"])
        else:
            print("Expires: never")
    else:
        print("Error:", resp.text)


if __name__ == "__main__":
    main()
