from flask import Flask, Response
import requests

app = Flask(__name__)

@app.route('/fetch/<path:repo>/<branch>/<path:filename>')
def fetch_file(repo, branch, filename):
    url = f'https://raw.githubusercontent.com/{repo}/{branch}/{filename}'
    try:
        r = requests.get(url)
        r.raise_for_status()
        return Response(r.text, content_type='text/plain')
    except requests.exceptions.RequestException as e:
        return Response(f'Error fetching file: {e}', status=500)

@app.route('/')
def home():
    return 'Render backend is running!'
