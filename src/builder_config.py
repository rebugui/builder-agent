import os
from pathlib import Path

def load_env_file():
    """Load environment variables from .env file"""
    # 환경 변수로 지정된 PROJECT_ROOT 사용 (우선)
    # 또는 절대 경로로 직접 설정
    project_root = Path(os.getenv("OPENCLAW_ROOT", "/Users/nabang/Documents/OpenClaw"))

    # PROJECT_ROOT가 존재하는지 확인
    if not project_root.exists():
        # fallback: 상대 경로 계산
        current_file = Path(__file__).resolve()
        project_root = current_file.parents[2]  # Adjust based on depth

    env_path = project_root / '.env'

    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    try:
                        key, value = line.split('=', 1)
                        if key.strip() not in os.environ: # Don't overwrite existing env vars
                            os.environ[key.strip()] = value.strip()
                    except ValueError:
                        pass

# Load environment variables on import
load_env_file()

class Config:
    # GLM Settings (Builder Agent)
    GLM_API_KEY = os.getenv("BUILDER_LLM_API_KEY", "")
    GLM_BASE_URL = os.getenv("BUILDER_LLM_BASE_URL", "https://api.z.ai/api/coding/paas/v4")
    GLM_MODEL = os.getenv("BUILDER_LLM_MODEL", "glm-5")
    GLM_TIMEOUT = 120

    # Notion Settings (Builder Agent)
    NOTION_TOKEN = os.getenv("BUILDER_NOTION_TOKEN", "")
    NOTION_DATABASE_ID = os.getenv("BUILDER_DATABASE_ID", "")

    # GitHub Settings
    GITHUB_TOKEN = os.getenv("BUILDER_GITHUB_TOKEN", "")

    # Paths
    MODULE_ROOT = Path(__file__).parent.resolve()
    PROJECT_ROOT = Path(os.getenv("OPENCLAW_ROOT", MODULE_ROOT.parents[1]))
    PROJECTS_DIR = MODULE_ROOT / 'projects'
    DATABASE_PATH = MODULE_ROOT / 'database' / 'history.db'

    # Ensure directories exist
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    (MODULE_ROOT / 'database').mkdir(parents=True, exist_ok=True)

config = Config()
