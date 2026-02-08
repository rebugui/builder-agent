# Builder Agent

> AI-powered DevOps project automation and code generation system

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

Builder Agent is an automated AI system that:
- Generates DevOps and security tool projects from requirements
- Creates production-ready Python code with tests
- Manages Git repositories automatically
- Integrates with Notion for project tracking
- Plans and executes multi-step development tasks

## Architecture

```
Topic Generation → Planning → Coding → Testing → Git Management → Notion Sync
```

### Key Components

- **AI Topic Generator**: Generates project ideas from security/devops trends
- **Planner**: Creates detailed development plans (local DB or Notion-based)
- **Coder**: Generates clean, documented Python code
- **Tester**: Creates comprehensive unit tests
- **Git Manager**: Handles repository creation and commits
- **Project Import**: Imports existing projects to Notion

## Features

- ✅ Multi-step planning with AI
- ✅ Production-ready code generation
- ✅ Automatic test creation
- ✅ Git repository automation
- ✅ Notion database integration
- ✅ Existing project import
- ✅ Local DB-based planning

## Installation

```bash
# Clone repository
git clone https://github.com/rebugui/builder-agent.git
cd builder-agent

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

## Configuration

Required environment variables:

```bash
# Notion
NOTION_API_KEY=your_notion_api_key
BUILDER_DATABASE_ID=your_builder_database_id

# LLM (OpenAI or ZhipuAI)
OPENAI_API_KEY=your_openai_api_key
# or
GLM_API_KEY=your_glm_api_key

# Git
GITHUB_TOKEN=your_github_token
DEFAULT_ORG=your_github_org
```

## Usage

### Generate New Project

```bash
# Generate project from AI topic
python -m src.main --topic "Security scanning tool"
```

### Import Existing Projects

```bash
# Import from local directory
python src/import_existing_projects.py

# Import from GitHub
python src/import_github_repos.py

# Import to Notion
python src/import_to_notion.py
```

### Planning

```bash
# Local DB-based planning
python src/planner.py

# Notion-based planning
python src/planner_notion.py
```

### Git Management

```bash
# Clone all project repos
python src/clone_all_repos.py

# Check git status
python src/check_git_status.py
```

## Project Structure

```
builder-agent/
├── src/                    # Core Python modules
│   ├── main.py            # Main entry point
│   ├── builder_agent.py   # Core builder logic
│   ├── coder.py           # Code generation
│   ├── tester.py          # Test generation
│   ├── planner.py         # Local DB planning
│   ├── planner_notion.py  # Notion-based planning
│   ├── git_manager.py     # Git operations
│   ├── ai_topic_generator.py # AI topic generation
│   ├── llm_client.py      # LLM integration (sync)
│   ├── llm_client_async.py # LLM integration (async)
│   ├── database/          # Database utilities
│   └── utils/             # Shared utilities
├── config/                # Configuration files
├── tests/                 # Test files
├── docs/                  # Documentation
└── requirements.txt       # Python dependencies
```

## Generated Projects

Builder Agent can create various types of projects:

- **Security Tools**: Scanners, analyzers, pentest tools
- **DevOps Utilities**: Automation scripts, CI/CD tools
- **Web Applications**: Flask/FastAPI backends
- **CLI Tools**: Command-line utilities
- **API Clients**: REST API wrappers

## Development Workflow

1. **Topic Generation**: AI generates project ideas
2. **Planning**: Break down into development steps
3. **Coding**: Generate production-ready code
4. **Testing**: Create comprehensive tests
5. **Git Management**: Initialize repo and commit
6. **Notion Sync**: Track in database

## Code Quality

Builder Agent generates code that follows:
- PEP 8 style guidelines
- Comprehensive docstrings
- Type hints where applicable
- Error handling
- Logging and debugging
- Unit tests with pytest

## Documentation

- [Technical Report](docs/BUILDER_AGENT_V2_REPORT.md)
- [Architecture](docs/README.md)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

**rebugui** - [GitHub](https://github.com/rebugui)

## Dependencies

- **OpenAI API**: GPT models for code generation
- **ZhipuAI GLM**: Alternative LLM support
- **PyGithub**: GitHub API integration
- **Notion Client**: Notion database integration
- **GitPython**: Git operations

## Acknowledgments

- OpenAI GPT for powerful code generation
- Notion for excellent project management
- GitHub for version control integration
