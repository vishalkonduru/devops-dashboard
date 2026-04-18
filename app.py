import os
from datetime import datetime, timezone
from flask import Flask, render_template, jsonify
from flask_caching import Cache
import config
from fetcher import get_all_data, fetch_language_stats, fetch_event_summary, get_uptime, get_rate_limit_info

APP_START = datetime.now(timezone.utc)

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

# Cache
if config.REDIS_URL:
    app.config['CACHE_TYPE'] = 'RedisCache'
    app.config['CACHE_REDIS_URL'] = config.REDIS_URL
else:
    app.config['CACHE_TYPE'] = 'SimpleCache'
app.config['CACHE_DEFAULT_TIMEOUT'] = config.CACHE_TIMEOUT
cache = Cache(app)


@app.route('/')
@cache.cached(timeout=config.CACHE_TIMEOUT)
def index():
    data = get_all_data()
    return render_template('index.html', data=data, version=config.APP_VERSION)


@app.route('/api/data')
@cache.cached(timeout=config.CACHE_TIMEOUT)
def api_data():
    return jsonify(get_all_data())


@app.route('/api/stats')
def api_stats():
    """Always-fresh stats: uptime, languages, events, rate limit."""
    delta = datetime.now(timezone.utc) - APP_START
    return jsonify({
        'uptime_seconds': int(delta.total_seconds()),
        'uptime_human': get_uptime(),
        'language_stats': fetch_language_stats(),
        'event_summary': fetch_event_summary(),
        'rate_limit': get_rate_limit_info(),
        'cache_type': app.config.get('CACHE_TYPE'),
        'version': config.APP_VERSION,
        'timestamp': datetime.utcnow().isoformat() + 'Z',
    })


@app.route('/health')
def health():
    delta = datetime.now(timezone.utc) - APP_START
    return jsonify({
        'status': 'ok',
        'service': config.APP_NAME,
        'version': config.APP_VERSION,
        'uptime_seconds': int(delta.total_seconds()),
    }), 200


@app.route('/refresh')
def refresh():
    cache.clear()
    return jsonify({'status': 'cache cleared', 'timestamp': datetime.utcnow().isoformat()}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=config.FLASK_DEBUG)
