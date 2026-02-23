# Builder Agent v3

🚀 **Automated Software Development with ChatDev 2.0 and GLM-5**

## Overview

Builder Agent v3 is an automated software development system that:
- **Discovers** project ideas from multiple sources (GitHub Trending, Security News, etc.)
- **Develops** projects using ChatDev 2.0 multi-agent collaboration
- **Publishes** completed projects to GitHub automatically

## Architecture

```
┌──────────────────┐    ┌──────────────┐    ┌──────────────┐
│ Topic Discoverer │───▶│  ChatDev 2.0 │───▶│ Git Publisher│
└──────────────────┘    └──────────────┘    └──────────────┘
         │                      │                    │
         ▼                      ▼                    ▼
  - GitHub Trending      - CEO              - Repo Create
  - CVE Database         - CTO              - File Upload
  - Security News        - Programmer       - README
  - arXiv                - Reviewer         - CI/CD
                         - Tester           - Push
                         - CTO Final
```

## Features

### 🎯 Topic Discovery
- GitHub Trending analysis
- CVE database monitoring
- Security news aggregation
- Hacker News trends
- Predefined project pool

### 🤖 Multi-Agent Development
- **CEO** - Requirements analysis
- **CTO** - Architecture design
- **Programmer** - Code generation
- **Reviewer** - Code quality review
- **Tester** - Test generation
- **CTO Final** - Final verification

### 🚀 Automated Publishing
- GitHub repository creation
- README generation
- Requirements.txt
- .gitignore
- GitHub Actions CI/CD

## Installation

```bash
cd /Users/nabang/Documents/OpenClaw/builder-agent-v3

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

## Configuration

### Required Environment Variables

```bash
# ChatDev 2.0
CHATDEV_URL=http://localhost:6400

# GLM API
BASE_URL=https://api.z.ai/api/coding/paas/v4
API_KEY=your_glm_api_key

# GitHub
GITHUB_TOKEN=your_github_token
GITHUB_USERNAME=rebugui
```

### Optional

```bash
# Telegram Notifications
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

## Usage

### 1. Discover Ideas

```bash
python main.py discover --limit 10
```

### 2. Develop a Project

```bash
python main.py develop \
  --name my-tool \
  --description "A useful CLI tool" \
  --type cli_app
```

### 3. Start Scheduler

```bash
# Run as daemon (continuous)
python main.py scheduler

# Run once (for testing)
python main.py scheduler --once
```

### 4. Check Environment

```bash
python main.py check
```

## Scheduling

By default, Builder Agent v3 runs:

- **Daily at 9:00 AM** - Discovers and develops 1 project
- **Weekdays at 10:00 AM** - Additional weekday-only development

Edit `config.yaml` to customize the schedule.

## Project Types

- `security_tool` - Security analysis tools
- `development_tool` - Development utilities
- `data_analysis` - Data analysis tools
- `automation` - Automation scripts
- `cli_app` - Command-line applications
- `web_app` - Web applications
- `api_service` - API services
- `library` - Reusable libraries

## Workflow

1. **Discovery** (9:00 AM)
   - Scan GitHub Trending, CVE DB, Security News
   - Select top 5 project ideas
   - Prioritize by relevance and difficulty

2. **Development** (9:30 AM)
   - ChatDev 2.0 multi-agent collaboration
   - CEO → CTO → Programmer → Reviewer → Tester → CTO Final
   - ~30-60 minutes per project

3. **Publishing** (10:30 AM)
   - Create GitHub repository
   - Upload files
   - Generate README
   - Configure CI/CD

4. **Notification** (10:45 AM)
   - Send Telegram notification with repo URL

## Generated Projects

Each generated project includes:

- ✅ Complete Python code
- ✅ Unit tests (pytest)
- ✅ README.md
- ✅ requirements.txt
- ✅ .gitignore
- ✅ GitHub Actions CI/CD

## Example Projects

| Project | Description | URL |
|---------|-------------|-----|
| robots-scanner | robots.txt scanner for bulk domain analysis | github.com/rebugui/robots-scanner |

## Technical Stack

- **Language:** Python 3.9+
- **AI Model:** GLM-5 (Zhipu AI)
- **Framework:** ChatDev 2.0
- **Scheduling:** APScheduler
- **GitHub API:** PyGithub
- **CLI:** Click + Rich

## Project Structure

```
builder-agent-v3/
├── main.py                    # Main entry point
├── requirements.txt           # Python dependencies
├── config.yaml               # Configuration
├── .env.example              # Environment template
├── discoverer/
│   └── topic_discoverer.py   # Idea discovery
├── orchestrator/
│   └── chatdev_client.py     # ChatDev 2.0 integration
├── publisher/
│   └── github_publisher.py   # GitHub publishing
├── scheduler/
│   └── scheduler.py          # Job scheduling
├── models/
│   └── idea.py               # Data models
└── logs/
    └── *.log                 # Log files
```

## Monitoring

```bash
# Check logs
tail -f logs/builder_agent.log

# Check project history
cat logs/project_history.json

# Check discovered ideas
cat logs/discovered_ideas.json
```

## Troubleshooting

### ChatDev 2.0 not running

```bash
cd /Users/nabang/Documents/OpenClaw/chatdev-v2
python server_main.py --port 6400
```

### GitHub Token Issues

```bash
# Generate token at: https://github.com/settings/tokens
export GITHUB_TOKEN=ghp_xxxx
```

### GLM API Errors

```bash
# Check API key
echo $API_KEY

# Test API
curl -X POST https://api.z.ai/api/coding/paas/v4/chat/completions \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "glm-5", "messages": [{"role": "user", "content": "Hello"}]}'
```

## License

MIT License

## Author

Generated by Builder Agent v3

## Links

- ChatDev 2.0: https://github.com/OpenBMB/ChatDev
- GLM-5: https://www.zhipuai.cn
- Repository: https://github.com/rebugui
