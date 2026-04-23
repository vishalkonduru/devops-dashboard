🚀 My GitHub Dashboard

> A production-ready personal DevOps dashboard built with **Flask**, **Redis**, and the **GitHub API** — containerized with Docker and deployed via GitHub Actions CI/CD.



 ✨ Features

- 📊 **Live GitHub Stats** — repos, followers, recent commits
- ⚡ **Redis Caching** — 5-minute TTL to avoid API rate limits
- 🐳 **Fully Containerized** — Docker + Docker Compose
- 🔄 **CI/CD Pipeline** — auto-builds on push, publishes to GHCR
- 🏥 **Health Checks** — `/health` endpoint for container orchestration
- 📦 **JSON API** — `/api/data` for programmatic access

 🏃 Quick Start

```bash
# Clone
git clone https://github.com/vishalkonduru/devops-dashboard.git
cd devops-dashboard

# Run with Docker Compose
docker-compose up -d

# Open dashboard
open http://localhost:5000
```

 🐳 Docker Commands

```bash
# Build locally
docker build -t devops-dashboard:latest .

# Run standalone
docker run -d -p 5000:5000 \
  -e GITHUB_USERNAME=vishalkonduru \
  devops-dashboard:latest



 🔧 Environment Variables

| Variable | Default | Description |
|---|---|---|
| `GITHUB_USERNAME` | `vishalkonduru` | GitHub username to display |
| `REDIS_URL` | _(auto via compose)_ | Redis connection URL |

 🗂️ Project Structure

```
devops-dashboard/
├── app.py                  # Flask app, routes, caching
├── fetcher.py              # GitHub API data fetcher
├── requirements.txt        # Python dependencies
├── Dockerfile              # Multi-stage build
├── docker-compose.yml      # App + Redis orchestration
├── templates/
│   └── index.html          # Dashboard UI
├── scripts/
│   └── daily_report.sh     # CLI daily summary script
└── .github/workflows/
    └── docker-build.yml    # CI/CD pipeline
```

 📡 API Endpoints

| Endpoint | Description |
|---|---|
| `GET /` | Dashboard UI |
| `GET /health` | Health check (JSON) |
| `GET /api/data` | Raw GitHub data (JSON) |
| `GET /refresh` | Clear cache |

 🔗 Links
- **Live Dashboard:** https://devops-dashboard-4iu4.onrender.com
