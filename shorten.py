import sys
import requests

def main():
    if len(sys.argv) < 2:
        print("Usage: python shorten.py <long_url>")
        sys.exit(1)
    url = sys.argv[1]
    try:
        resp = requests.post("http://localhost:5000/shorten", json={"url": url})
    except requests.exceptions.ConnectionError:
        print("Could not connect to http://localhost:5000 — make sure the server is running")
        sys.exit(1)

    if resp.status_code == 200:
        data = resp.json()
        print("Short URL:", data["short_url"])
    else:
        print("Error:", resp.text)


if __name__ == "__main__":
    main()
