import os
import time
import hashlib
import logging
from flask import Flask, render_template, jsonify, Response
from fetcher import get_dashboard_data

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder="static", static_url_path="/static")

# Build fingerprint — changes every deploy (or use git SHA if available)
BUILD_ID = os.getenv("RENDER_GIT_COMMIT", str(int(time.time())))[:8]


@app.after_request
def set_cache_headers(response):
    """Apply correct Cache-Control headers per content type."""
    ct = response.content_type

    # HTML pages: never cache — always revalidate
    if "text/html" in ct:
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"]  = "no-cache"
        response.headers["Expires"] = "0"

    # Versioned static assets: cache 1 year (immutable)
    elif any(x in ct for x in ("text/css", "javascript", "image/", "font/")):
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"

    # API / JSON: short cache
    elif "application/json" in ct:
        response.headers["Cache-Control"] = "public, max-age=60"

    return response


@app.route("/")
def index():
    try:
        data = get_dashboard_data()
        return render_template("index.html", build_id=BUILD_ID, **data)
    except Exception as e:
        logger.error(f"Dashboard render error: {e}")
        return render_template(
            "index.html",
            build_id=BUILD_ID,
            profile={}, stats={}, top_languages=[],
            recent_repos=[], recent_events=[], activity=[],
            fetched_at="N/A", redis_available=False,
            github_username="vishalkonduru",
            error=str(e)
        )


@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "devops-dashboard", "build": BUILD_ID}), 200


@app.route("/api/data")
def api_data():
    try:
        data = get_dashboard_data()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
