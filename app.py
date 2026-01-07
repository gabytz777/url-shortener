from flask import Flask, request, redirect, jsonify, render_template
import shortener

app = Flask(__name__)


# Initialize DB (Flask 3 removed before_first_request); run once at import
shortener.init_db()


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/shorten', methods=['POST'])
def shorten():
    data = request.form or request.get_json()
    url = None
    if isinstance(data, dict):
        url = data.get('url')
    else:
        url = request.form.get('url')

    if not url:
        return jsonify({"error": "no url provided"}), 400

    code = shortener.add_url(url)
    short_url = request.host_url.rstrip('/') + '/' + code
    return jsonify({"short_url": short_url, "code": code})


@app.route('/<code>')
def redirect_to(code):
    url = shortener.get_url(code)
    if not url:
        return "Not found", 404
    shortener.increment_visits(code)
    return redirect(url, code=302)


if __name__ == "__main__":
    app.run(debug=True)
