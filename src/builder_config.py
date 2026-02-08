import os
from pathlib import Path

def load_env_file():
    """Load environment variables from .env file"""
    # Find the project root (assuming this file is in modules/builder/)
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
    # GLM Settings
    GLM_API_KEY = os.getenv("GLM_API_KEY", "")
    GLM_BASE_URL = os.getenv("GLM_BASE_URL", "https://api.z.ai/api/coding/paas/v4/")
    GLM_MODEL = os.getenv("GLM_MODEL", "glm-4.7")
    GLM_TIMEOUT = 120

    # GitHub Settings
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

    # Paths
    MODULE_ROOT = Path(__file__).parent.resolve()
    PROJECT_ROOT = MODULE_ROOT.parents[1]
    PROJECTS_DIR = MODULE_ROOT / 'projects'
    DATABASE_PATH = MODULE_ROOT / 'database' / 'history.db'

    # Ensure directories exist
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    (MODULE_ROOT / 'database').mkdir(parents=True, exist_ok=True)

config = Config()
