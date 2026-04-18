import os
import requests
from datetime import datetime

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')
GITHUB_USERNAME = os.getenv('GITHUB_USERNAME', 'vishalkonduru')

HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}' if GITHUB_TOKEN else '',
    'Accept': 'application/vnd.github.v3+json',
}


def fetch_github_profile():
    """Fetch GitHub user profile data."""
    try:
        url = f'https://api.github.com/users/{GITHUB_USERNAME}'
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return {
            'login': data.get('login'),
            'name': data.get('name', data.get('login')),
            'avatar_url': data.get('avatar_url'),
            'public_repos': data.get('public_repos', 0),
            'followers': data.get('followers', 0),
            'following': data.get('following', 0),
            'bio': data.get('bio', ''),
            'html_url': data.get('html_url'),
        }
    except Exception as e:
        return {'error': str(e)}


def fetch_recent_repos():
    """Fetch the most recent repositories."""
    try:
        url = f'https://api.github.com/users/{GITHUB_USERNAME}/repos?sort=updated&per_page=6'
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        repos = resp.json()
        return [
            {
                'name': r['name'],
                'description': r.get('description', ''),
                'url': r['html_url'],
                'language': r.get('language', 'N/A'),
                'stars': r.get('stargazers_count', 0),
                'forks': r.get('forks_count', 0),
                'updated_at': r.get('updated_at', ''),
            }
            for r in repos
        ]
    except Exception as e:
        return [{'error': str(e)}]


def fetch_commit_activity():
    """Fetch recent commit events."""
    try:
        url = f'https://api.github.com/users/{GITHUB_USERNAME}/events?per_page=10'
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        events = resp.json()
        commits = []
        for event in events:
            if event.get('type') == 'PushEvent':
                for c in event.get('payload', {}).get('commits', [])[:2]:
                    commits.append({
                        'repo': event['repo']['name'],
                        'message': c.get('message', '')[:80],
                        'sha': c.get('sha', '')[:7],
                        'date': event.get('created_at', ''),
                    })
        return commits[:8]
    except Exception as e:
        return [{'error': str(e)}]


def get_all_data():
    """Aggregate all fetched data with a timestamp."""
    return {
        'profile': fetch_github_profile(),
        'repos': fetch_recent_repos(),
        'commits': fetch_commit_activity(),
        'fetched_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
    }
