import os
import logging
import requests
from datetime import datetime, timezone
from collections import Counter

logger = logging.getLogger(__name__)

GITHUB_USERNAME = os.getenv('GITHUB_USERNAME', 'vishalkonduru')

# Language color map (subset of github-linguist)
LANG_COLORS = {
    'Python': '#3572A5',
    'JavaScript': '#f1e05a',
    'TypeScript': '#2b7489',
    'Shell': '#89e051',
    'HTML': '#e34c26',
    'CSS': '#563d7c',
    'Java': '#b07219',
    'Go': '#00ADD8',
    'Rust': '#dea584',
    'C++': '#f34b7d',
    'C': '#555555',
    'Ruby': '#701516',
    'PHP': '#4F5D95',
    'Swift': '#ffac45',
    'Kotlin': '#A97BFF',
    'Dockerfile': '#384d54',
    'YAML': '#cb171e',
    'N/A': '#8b949e',
}


def _headers():
    """Build request headers lazily so token changes at runtime are picked up."""
    token = os.getenv('GITHUB_TOKEN', '').strip()
    h = {'Accept': 'application/vnd.github.v3+json'}
    if token:
        h['Authorization'] = f'token {token}'
    return h


def _get(url, params=None):
    """Safe GET — returns parsed JSON or {'_error': ..., '_status': ...}."""
    try:
        r = requests.get(url, headers=_headers(), params=params, timeout=10)
        if r.status_code == 403 and 'rate limit' in r.text.lower():
            reset = r.headers.get('X-RateLimit-Reset', 'unknown')
            return {'_error': f'GitHub rate limit exceeded (resets at {reset})', '_status': 403}
        if r.status_code == 404:
            return {'_error': 'Not found (404)', '_status': 404}
        r.raise_for_status()
        return r.json()
    except requests.Timeout:
        logger.warning('GitHub API timeout: %s', url)
        return {'_error': 'Request timed out', '_status': 0}
    except requests.ConnectionError:
        return {'_error': 'Connection error — check network', '_status': 0}
    except Exception as e:
        logger.exception('Unexpected error fetching %s', url)
        return {'_error': str(e), '_status': 0}


def _is_error(data):
    return isinstance(data, dict) and '_error' in data


def fetch_github_profile():
    """Fetch GitHub user profile data."""
    data = _get(f'https://api.github.com/users/{GITHUB_USERNAME}')
    if _is_error(data):
        return {'error': data['_error']}
    return {
        'login': data.get('login'),
        'name': data.get('name') or data.get('login'),
        'avatar_url': data.get('avatar_url'),
        'public_repos': data.get('public_repos', 0),
        'followers': data.get('followers', 0),
        'following': data.get('following', 0),
        'bio': data.get('bio') or '',
        'html_url': data.get('html_url'),
        'location': data.get('location') or '',
        'company': data.get('company') or '',
        'blog': data.get('blog') or '',
        'created_at': data.get('created_at', ''),
    }


def fetch_recent_repos():
    """Fetch the most recently updated original (non-fork) repositories."""
    repos = _get(
        f'https://api.github.com/users/{GITHUB_USERNAME}/repos',
        params={'sort': 'updated', 'per_page': 20, 'type': 'owner'}
    )
    if _is_error(repos):
        return []
    return [
        {
            'name': r['name'],
            'description': r.get('description') or '',
            'url': r['html_url'],
            'language': r.get('language') or 'N/A',
            'lang_color': LANG_COLORS.get(r.get('language') or 'N/A', '#8b949e'),
            'stars': r.get('stargazers_count', 0),
            'forks': r.get('forks_count', 0),
            'open_issues': r.get('open_issues_count', 0),
            'updated_at': r.get('updated_at', ''),
            'is_fork': r.get('fork', False),
            'topics': r.get('topics', []),
            'visibility': r.get('visibility', 'public'),
        }
        for r in repos
        if not r.get('fork', False)
    ][:6]


def fetch_language_stats():
    """Aggregate language usage across all owned repos."""
    repos = _get(
        f'https://api.github.com/users/{GITHUB_USERNAME}/repos',
        params={'per_page': 100, 'type': 'owner'}
    )
    if _is_error(repos):
        return []
    lang_counter = Counter(r.get('language') for r in repos if r.get('language'))
    total = sum(lang_counter.values()) or 1
    return [
        {
            'name': lang,
            'count': count,
            'percent': round(count / total * 100, 1),
            'color': LANG_COLORS.get(lang, '#8b949e'),
        }
        for lang, count in lang_counter.most_common(8)
    ]


def fetch_commit_activity():
    """Fetch recent PushEvents and extract individual commits."""
    events = _get(
        f'https://api.github.com/users/{GITHUB_USERNAME}/events',
        params={'per_page': 30}
    )
    if _is_error(events):
        return []
    commits = []
    for event in events:
        if event.get('type') == 'PushEvent':
            for c in event.get('payload', {}).get('commits', [])[:2]:
                commits.append({
                    'repo': event['repo']['name'].split('/')[-1],
                    'repo_full': event['repo']['name'],
                    'message': c.get('message', '')[:80].split('\n')[0],
                    'sha': c.get('sha', '')[:7],
                    'date': event.get('created_at', ''),
                })
    return commits[:10]


def fetch_event_summary():
    """Summarize last 100 events by type."""
    events = _get(
        f'https://api.github.com/users/{GITHUB_USERNAME}/events',
        params={'per_page': 100}
    )
    if _is_error(events):
        return {}
    type_map = {
        'PushEvent': 'Pushes',
        'PullRequestEvent': 'Pull Requests',
        'IssuesEvent': 'Issues',
        'CreateEvent': 'Branches/Tags',
        'WatchEvent': 'Stars Given',
        'ForkEvent': 'Forks',
    }
    counts = Counter(
        type_map[e['type']]
        for e in events
        if e.get('type') in type_map
    )
    return dict(counts.most_common())


def get_rate_limit_info():
    """Return remaining GitHub API calls for the current token/IP."""
    data = _get('https://api.github.com/rate_limit')
    if _is_error(data):
        return {}
    core = data.get('resources', {}).get('core', {})
    return {
        'limit': core.get('limit', 0),
        'remaining': core.get('remaining', 0),
        'reset': core.get('reset', 0),
        'used': core.get('used', 0),
    }


START_TIME = datetime.now(timezone.utc)


def get_uptime():
    """Return service uptime as a human-readable string."""
    delta = datetime.now(timezone.utc) - START_TIME
    hours, rem = divmod(int(delta.total_seconds()), 3600)
    minutes, seconds = divmod(rem, 60)
    return f'{hours}h {minutes}m {seconds}s'


def get_all_data():
    """Aggregate all fetched data."""
    return {
        'profile': fetch_github_profile(),
        'repos': fetch_recent_repos(),
        'commits': fetch_commit_activity(),
        'language_stats': fetch_language_stats(),
        'event_summary': fetch_event_summary(),
        'uptime': get_uptime(),
        'fetched_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
    }
