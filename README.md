Simple Flask URL Shortener 

This is a small self-hosted URL shortener made with Python + Flask, using SQLite to store links.

To run it, you’ll need Python 3.8+ installed. Install the dependencies with:

pip install -r requirements.txt

Then start the server with:

python app.py

After that, open http://localhost:5000
 in your browser and paste in a URL to shorten.

There’s also a CLI script if you prefer. With the server running, you can do:

python shorten.py https://example.com

and it’ll print the shortened link.
