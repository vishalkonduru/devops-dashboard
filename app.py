import os
import json
from flask import Flask, render_template, jsonify
from flask_caching import Cache
from fetcher import get_all_data

app = Flask(__name__)

# Cache config — use Redis if available, fallback to simple in-memory
REDIS_URL = os.getenv('REDIS_URL', '')
if REDIS_URL:
    app.config['CACHE_TYPE'] = 'RedisCache'
    app.config['CACHE_REDIS_URL'] = REDIS_URL
else:
    app.config['CACHE_TYPE'] = 'SimpleCache'

app.config['CACHE_DEFAULT_TIMEOUT'] = 300  # 5 min cache
cache = Cache(app)


@app.route('/')
@cache.cached(timeout=300)
def index():
    data = get_all_data()
    return render_template('index.html', data=data)


@app.route('/api/data')
@cache.cached(timeout=300)
def api_data():
    return jsonify(get_all_data())


@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'service': 'devops-dashboard'}), 200


@app.route('/refresh')
def refresh():
    cache.clear()
    return jsonify({'status': 'cache cleared'}), 200


if __name__ == '__main__':
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=5000, debug=debug)
