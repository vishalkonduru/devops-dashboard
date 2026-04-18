import os
import requests
from datetime import datetime, timezone
from collections import Counter

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')
GITHUB_USERNAME = os.getenv('GITHUB_USERNAME', 'vishalkonduru')

HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}' if GITHUB_TOKEN else '',
    'Accept': 'application/vnd.github.v3+json',
}

GRAPHQL_HEADERS = {
    'Authorization': f'bearer {GITHUB_TOKEN}' if GITHUB_TOKEN else '',
    'Content-Type': 'application/json',
}

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


def _get(url, params=None):
    """Safe GET with error handling."""
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {'_error': str(e)}


def fetch_github_profile():
    """Fetch GitHub user profile data."""
    data = _get(f'https://api.github.com/users/{GITHUB_USERNAME}')
    if '_error' in data:
        return {'error': data['_error']}
    return {
        'login': data.get('login'),
        'name': data.get('name', data.get('login')),
        'avatar_url': data.get('avatar_url'),
        'public_repos': data.get('public_repos', 0),
        'followers': data.get('followers', 0),
        'following': data.get('following', 0),
        'bio': data.get('bio', ''),
        'html_url': data.get('html_url'),
        'location': data.get('location', ''),
        'company': data.get('company', ''),
        'blog': data.get('blog', ''),
        'created_at': data.get('created_at', ''),
    }


def fetch_recent_repos():
    """Fetch the most recently updated repositories."""
    repos = _get(
        f'https://api.github.com/users/{GITHUB_USERNAME}/repos',
        params={'sort': 'updated', 'per_page': 8, 'type': 'owner'}
    )
    if isinstance(repos, dict) and '_error' in repos:
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
        if not r.get('fork', False)  # only original repos
    ][:6]


def fetch_language_stats():
    """Aggregate language usage across all repos."""
    repos = _get(
        f'https://api.github.com/users/{GITHUB_USERNAME}/repos',
        params={'per_page': 100, 'type': 'owner'}
    )
    if isinstance(repos, dict) and '_error' in repos:
        return []

    lang_counter = Counter()
    for r in repos:
        lang = r.get('language')
        if lang:
            lang_counter[lang] += 1

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
    """Fetch recent PushEvents."""
    events = _get(
        f'https://api.github.com/users/{GITHUB_USERNAME}/events',
        params={'per_page': 30}
    )
    if isinstance(events, dict) and '_error' in events:
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
    """Summarize recent activity by event type."""
    events = _get(
        f'https://api.github.com/users/{GITHUB_USERNAME}/events',
        params={'per_page': 100}
    )
    if isinstance(events, dict) and '_error' in events:
        return {}

    type_map = {
        'PushEvent': 'Pushes',
        'PullRequestEvent': 'Pull Requests',
        'IssuesEvent': 'Issues',
        'CreateEvent': 'Branches/Tags',
        'WatchEvent': 'Stars Given',
        'ForkEvent': 'Forks',
    }
    counts = Counter()
    for e in events:
        label = type_map.get(e.get('type', ''), None)
        if label:
            counts[label] += 1
    return dict(counts.most_common())


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
