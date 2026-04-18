# Changelog

All notable changes to **devops-dashboard** are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [2.0.0] - 2026-04-19

### Added
- **Language breakdown bar** — color-coded bar chart + legend showing language distribution across all repos
- **Activity summary** — event type counts (Pushes, PRs, Issues, etc.) from last 100 GitHub events
- **`/api/stats` endpoint** — returns uptime, language stats, event summary; always fresh (no cache)
- **Uptime badge** in header showing live container uptime
- **Profile details section** — location, company, blog, member-since
- **CI/CD status widget** — shows pipeline stages inline on dashboard
- **Topics pills** on repo cards
- **Open issues count** on repo cards
- **Language color mapping** for 20+ languages using GitHub Linguist palette
- **`fetch_event_summary()`** in fetcher.py — aggregates event types
- **`fetch_language_stats()`** in fetcher.py — scans all repos for language counts
- **`get_uptime()`** in fetcher.py — tracks container start time
- **Multi-job CI pipeline** with separate `lint`, `build-and-push`, `security-scan` jobs
- **Trivy security scan** job runs after every push to main
- **Two endpoint tests** in CI — `/health` and `/api/stats`
- **Python syntax check** job before Docker build

### Changed
- `fetch_recent_repos()` now skips forks, shows 6 repos (was 6 including forks)
- `fetch_commit_activity()` now scans 30 events (was 10), shows 10 commits (was 8)
- `/health` response now includes `version` and `uptime_seconds`
- Dashboard UI fully redesigned: sticky header, hover transitions, responsive grid
- Repo cards now show language dot color, open issues, topics
- Commit feed shows repo name prominently as header

### Fixed
- `HEADERS` auth key now only set when `GITHUB_TOKEN` is non-empty (prevents sending empty `token ` header)
- Fetcher functions return empty list/dict on error instead of error-keyed dicts

---

## [1.0.0] - 2026-04-18

### Added
- Initial project scaffold
- Flask app with `/`, `/api/data`, `/health`, `/refresh` routes
- Redis caching with SimpleCache fallback
- GitHub API: profile, recent repos, commit events
- Dockerfile with Gunicorn + healthcheck
- Docker Compose with Redis service
- GitHub Actions CI/CD → GHCR publish
- `scripts/daily_report.sh`
