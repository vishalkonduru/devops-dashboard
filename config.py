import os

# ── GitHub ──────────────────────────────────────────────────────────────────
GITHUB_USERNAME: str = os.getenv('GITHUB_USERNAME', 'vishalkonduru')
GITHUB_TOKEN: str = os.getenv('GITHUB_TOKEN', '').strip()

# ── Flask ────────────────────────────────────────────────────────────────────
FLASK_DEBUG: bool = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
SECRET_KEY: str = os.getenv('SECRET_KEY', 'dev-secret-change-in-prod')

# ── Cache ────────────────────────────────────────────────────────────────────
REDIS_URL: str = os.getenv('REDIS_URL', '')
CACHE_TIMEOUT: int = int(os.getenv('CACHE_TIMEOUT', '300'))  # seconds

# ── App metadata ─────────────────────────────────────────────────────────────
APP_VERSION: str = '2.1.0'
APP_NAME: str = 'devops-dashboard'
