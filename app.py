from flask import Flask, request, redirect, jsonify, render_template
from werkzeug.middleware.proxy_fix import ProxyFix
import shortener

app = Flask(__name__)
# the tunnel ends TLS and forwards the original scheme; without this every
# short link it builds is http://
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1)


shortener.init_db()


def _request_data():
    data = request.get_json(silent=True)
    if isinstance(data, dict):
        return data
    return request.form


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/shorten', methods=['POST'])
def shorten():
    data = _request_data()
    url = (data.get('url') or '').strip()

    if not url:
        return jsonify({"error": "no url provided"}), 400

    try:
        expires_at = shortener.parse_expiry(
            expires_in=data.get('expires_in'),
            expires_at=data.get('expires_at'),
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    code = shortener.add_url(url, expires_at=expires_at)
    short_url = request.host_url.rstrip('/') + '/' + code
    return jsonify({
        "short_url": short_url,
        "code": code,
        "expires_at": shortener.format_expiry(expires_at),
    })


@app.route('/<code>')
def redirect_to(code):
    record = shortener.get_record(code)
    if record is None:
        return "Not found", 404
    if shortener.is_expired(record["expires_at"]):
        return "This link has expired", 410
    shortener.increment_visits(code)
    return redirect(record["url"], code=302)


if __name__ == "__main__":
    app.run(debug=True)
