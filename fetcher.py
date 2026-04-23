import os
import logging
import requests
from datetime import datetime, timezone, timedelta
from collections import Counter

logger = logging.getLogger(__name__)

GITHUB_USERNAME = os.getenv('GITHUB_USERNAME', 'vishalkonduru')

IST = timezone(timedelta(hours=5, minutes=30))

LANG_COLORS = {
    'Python': '#3572A5', 'JavaScript': '#f1e05a', 'TypeScript': '#2b7489',
    'Shell': '#89e051', 'HTML': '#e34c26', 'CSS': '#563d7c',
    'Java': '#b07219', 'Go': '#00ADD8', 'Rust': '#dea584',
    'C++': '#f34b7d', 'C': '#555555', 'Ruby': '#701516',
    'PHP': '#4F5D95', 'Swift': '#ffac45', 'Kotlin': '#A97BFF',
    'Dockerfile': '#384d54', 'YAML': '#cb171e', 'N/A': '#8b949e',
}


def _headers():
    token = os.getenv('GITHUB_TOKEN', '').strip()
    h = {'Accept': 'application/vnd.github.v3+json'}
    if token:
        h['Authorization'] = f'token {token}'
    return h


def _get(url, params=None):
    try:
        r = requests.get(url, headers=_headers(), params=params, timeout=10)
        if r.status_code == 403 and 'rate limit' in r.text.lower():
            reset = r.headers.get('X-RateLimit-Reset', 'unknown')
            return {'_error': f'Rate limit exceeded (resets {reset})', '_status': 403}
        if r.status_code == 404:
            return {'_error': 'Not found (404)', '_status': 404}
        r.raise_for_status()
        return r.json()
    except requests.Timeout:
        return {'_error': 'Request timed out', '_status': 0}
    except requests.ConnectionError:
        return {'_error': 'Connection error', '_status': 0}
    except Exception as e:
        logger.exception('Error fetching %s', url)
        return {'_error': str(e), '_status': 0}


def _is_error(data):
    return isinstance(data, dict) and '_error' in data


def fetch_github_profile():
    data = _get(f'https://api.github.com/users/{GITHUB_USERNAME}')
    if _is_error(data):
        return {'error': data['_error']}
    repos = _get(
        f'https://api.github.com/users/{GITHUB_USERNAME}/repos',
        params={'per_page': 100, 'type': 'owner'}
    )
    total_stars = total_forks = 0
    if not _is_error(repos):
        for r in repos:
            total_stars += r.get('stargazers_count', 0)
            total_forks += r.get('forks_count', 0)
    return {
        'login':        data.get('login'),
        'name':         data.get('name') or data.get('login'),
        'avatar_url':   data.get('avatar_url'),
        'public_repos': data.get('public_repos', 0),
        'followers':    data.get('followers', 0),
        'following':    data.get('following', 0),
        'total_stars':  total_stars,
        'total_forks':  total_forks,
        'bio':          data.get('bio') or '',
        'html_url':     data.get('html_url'),
        'location':     data.get('location') or '',
        'company':      data.get('company') or '',
        'blog':         data.get('blog') or '',
        'created_at':   data.get('created_at', ''),
    }


def fetch_recent_repos():
    repos = _get(
        f'https://api.github.com/users/{GITHUB_USERNAME}/repos',
        params={'sort': 'updated', 'per_page': 20, 'type': 'owner'}
    )
    if _is_error(repos):
        return []
    return [
        {
            'name':        r['name'],
            'description': r.get('description') or '',
            'url':         r['html_url'],
            'language':    r.get('language') or 'N/A',
            'lang_color':  LANG_COLORS.get(r.get('language') or 'N/A', '#8b949e'),
            'stars':       r.get('stargazers_count', 0),
            'forks':       r.get('forks_count', 0),
            'open_issues': r.get('open_issues_count', 0),
            'updated_at':  r.get('updated_at', ''),
            'is_fork':     r.get('fork', False),
            'topics':      r.get('topics', []),
            'visibility':  r.get('visibility', 'public'),
        }
        for r in repos if not r.get('fork', False)
    ][:6]


def fetch_language_stats():
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
            'name':    lang,
            'count':   count,
            'percent': round(count / total * 100, 1),
            'color':   LANG_COLORS.get(lang, '#8b949e'),
        }
        for lang, count in lang_counter.most_common(8)
    ]


def fetch_commit_activity():
    """
    Fetch recent commits using three strategies in order:
      1. /users/{user}/events  (both public and, if token set, private)
      2. GitHub Search API: author:{user} committer-date:>=last-30-days
      3. Walk the 6 most-recently-updated repos and pull /commits
    Returns a list of up to 15 commit dicts.
    """
    commits = []

    # --- Strategy 1: events endpoint (works without token for public pushes) ---
    for endpoint in [
        f'https://api.github.com/users/{GITHUB_USERNAME}/events',
        f'https://api.github.com/users/{GITHUB_USERNAME}/events/public',
    ]:
        events = _get(endpoint, params={'per_page': 100})
        if _is_error(events) or not isinstance(events, list):
            continue
        for event in events:
            if event.get('type') == 'PushEvent':
                for c in event.get('payload', {}).get('commits', [])[:5]:
                    commits.append({
                        'repo':      event['repo']['name'].split('/')[-1],
                        'repo_full': event['repo']['name'],
                        'message':   c.get('message', '')[:80].split('\n')[0],
                        'sha':       c.get('sha', '')[:7],
                        'date':      event.get('created_at', ''),
                        'url':       f"https://github.com/{event['repo']['name']}/commit/{c.get('sha','')}",
                    })
            if len(commits) >= 15:
                break
        if commits:
            break

    if commits:
        return commits[:15]

    # --- Strategy 2: Search API (doesn't need a token for public repos) ---
    search = _get(
        'https://api.github.com/search/commits',
        params={
            'q': f'author:{GITHUB_USERNAME}',
            'sort': 'committer-date',
            'order': 'desc',
            'per_page': 15,
        }
    )
    if not _is_error(search) and isinstance(search.get('items'), list):
        for item in search['items']:
            c = item.get('commit', {})
            repo_name = item.get('repository', {}).get('name', '')
            commits.append({
                'repo':      repo_name,
                'repo_full': item.get('repository', {}).get('full_name', ''),
                'message':   c.get('message', '')[:80].split('\n')[0],
                'sha':       item.get('sha', '')[:7],
                'date':      c.get('committer', {}).get('date', ''),
                'url':       item.get('html_url', ''),
            })

    if commits:
        return commits[:15]

    # --- Strategy 3: Walk recent repos directly ---
    repos = _get(
        f'https://api.github.com/users/{GITHUB_USERNAME}/repos',
        params={'sort': 'updated', 'per_page': 6, 'type': 'owner'}
    )
    if not _is_error(repos) and isinstance(repos, list):
        for repo in repos[:6]:
            repo_name = repo.get('name', '')
            repo_commits = _get(
                f'https://api.github.com/repos/{GITHUB_USERNAME}/{repo_name}/commits',
                params={'author': GITHUB_USERNAME, 'per_page': 5}
            )
            if _is_error(repo_commits) or not isinstance(repo_commits, list):
                continue
            for c in repo_commits:
                commits.append({
                    'repo':      repo_name,
                    'repo_full': f'{GITHUB_USERNAME}/{repo_name}',
                    'message':   c.get('commit', {}).get('message', '')[:80].split('\n')[0],
                    'sha':       c.get('sha', '')[:7],
                    'date':      c.get('commit', {}).get('committer', {}).get('date', ''),
                    'url':       c.get('html_url', ''),
                })
            if len(commits) >= 15:
                break

    # Sort by date descending, newest first
    commits.sort(key=lambda x: x.get('date', ''), reverse=True)
    return commits[:15]


def fetch_event_summary():
    events = _get(
        f'https://api.github.com/users/{GITHUB_USERNAME}/events/public',
        params={'per_page': 100}
    )
    if _is_error(events) or not isinstance(events, list):
        return {}
    type_map = {
        'PushEvent':        'Pushes',
        'PullRequestEvent': 'Pull Requests',
        'IssuesEvent':      'Issues',
        'CreateEvent':      'Branches/Tags',
        'WatchEvent':       'Stars Given',
        'ForkEvent':        'Forks',
    }
    counts = Counter(
        type_map[e['type']] for e in events if e.get('type') in type_map
    )
    return dict(counts.most_common())


START_TIME = datetime.now(timezone.utc)


def get_uptime():
    delta = datetime.now(timezone.utc) - START_TIME
    hours, rem = divmod(int(delta.total_seconds()), 3600)
    minutes, seconds = divmod(rem, 60)
    return f'{hours}h {minutes}m {seconds}s'


def get_all_data():
    now_ist = datetime.now(IST)
    return {
        'profile':        fetch_github_profile(),
        'repos':          fetch_recent_repos(),
        'commits':        fetch_commit_activity(),
        'language_stats': fetch_language_stats(),
        'event_summary':  fetch_event_summary(),
        'uptime':         get_uptime(),
        'fetched_at':     now_ist.strftime('%d %b %Y, %I:%M %p IST'),
    }
