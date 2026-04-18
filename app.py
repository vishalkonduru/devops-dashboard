import os
from datetime import datetime, timezone
from flask import Flask, render_template, jsonify
from flask_caching import Cache
from fetcher import get_all_data, fetch_language_stats, fetch_event_summary, get_uptime

APP_START = datetime.now(timezone.utc)

app = Flask(__name__)

# Cache config
REDIS_URL = os.getenv('REDIS_URL', '')
if REDIS_URL:
    app.config['CACHE_TYPE'] = 'RedisCache'
    app.config['CACHE_REDIS_URL'] = REDIS_URL
else:
    app.config['CACHE_TYPE'] = 'SimpleCache'

app.config['CACHE_DEFAULT_TIMEOUT'] = 300
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


@app.route('/api/stats')
def api_stats():
    """Lightweight stats endpoint (not cached — always fresh)."""
    delta = datetime.now(timezone.utc) - APP_START
    return jsonify({
        'uptime_seconds': int(delta.total_seconds()),
        'uptime_human': get_uptime(),
        'language_stats': fetch_language_stats(),
        'event_summary': fetch_event_summary(),
        'cache_type': app.config.get('CACHE_TYPE'),
        'timestamp': datetime.utcnow().isoformat() + 'Z',
    })


@app.route('/health')
def health():
    delta = datetime.now(timezone.utc) - APP_START
    return jsonify({
        'status': 'ok',
        'service': 'devops-dashboard',
        'version': '2.0.0',
        'uptime_seconds': int(delta.total_seconds()),
    }), 200


@app.route('/refresh')
def refresh():
    cache.clear()
    return jsonify({'status': 'cache cleared', 'timestamp': datetime.utcnow().isoformat()}), 200


if __name__ == '__main__':
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=5000, debug=debug)
