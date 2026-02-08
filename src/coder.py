#!/usr/bin/env python3
"""
Builder Agent - Code Generator

GLM-4.7을 사용하여 구조화된 Python 코드를 생성합니다.
"""

import os
import sys
import re
from typing import Dict, List, Optional
from pathlib import Path

# Add project root and intelligence module to sys.path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parents[1]
intelligence_dir = project_root / 'modules' / 'intelligence'

for path in [str(project_root), str(intelligence_dir)]:
    if path not in sys.path:
        sys.path.append(path)

from modules.builder.builder_config import config
from modules.builder.prompts import Prompts
from modules.builder.utils.logger import setup_logger

# Intelligence Agent GLM Client
try:
    from llm_client import GLMClient
except ImportError:
    try:
        from modules.intelligence.llm_client import GLMClient
    except ImportError:
        GLMClient = None 

logger = setup_logger("CodeGenerator")

class CodeGenerator:
    """Code Generator (코드 생성)"""

    def __init__(self):
        """초기화"""
        self.api_key = config.GLM_API_KEY
        self.base_url = config.GLM_BASE_URL
        self.model = config.GLM_MODEL
        
        if not self.api_key:
             raise ValueError("GLM_API_KEY 환경변수가 설정되지 않았습니다.")

        # GLM Client 초기화
        if GLMClient:
            self.client = GLMClient(self.api_key, self.base_url, self.model)
        else:
            raise ImportError("GLMClient module not found. Check your python path.")

        self.system_prompt = Prompts.DEVOPS_EXPERT_SYSTEM

    def generate_spec(self, project_name: str, short_description: str) -> str:
        """상세 요구사항 명세서 생성"""
        logger.info(f"Generating technical spec for: {project_name}")
        
        spec_prompt = (
            f"You are a Software Architect. Create a detailed technical specification for the project '{project_name}'.\n"
            f"Short Description: {short_description}\n\n"
            "The specification must be in Markdown format and include:\n"
            "1. Project Overview\n"
            "2. User Stories / Requirements\n"
            "3. Architecture & Tech Stack (Python based)\n"
            "4. API Design / CLI Commands\n"
            "5. Database Schema (if applicable)\n"
            "6. Directory Structure\n\n"
            "Output ONLY the Markdown content, starting with '# Technical Specification'."
        )
        
        try:
            spec_content = self.client.chat(
                system_prompt="You are an expert Software Architect.",
                user_prompt=spec_prompt
            )
            return spec_content
        except Exception as e:
            logger.error(f"Error generating spec: {e}")
            return f"# Technical Specification (Fallback)\n\n{short_description}"

    def generate_code(self, project_name: str, project_description: str) -> str:
        """Python 코드 생성"""
        logger.info(f"Generating code for project: {project_name}")
        
        user_prompt = Prompts.get_code_generation_prompt(project_name, project_description)

        try:
            generated_code = self.client.chat(
                system_prompt=self.system_prompt,
                user_prompt=user_prompt
            )
            return generated_code
        except Exception as e:
            logger.error(f"Error generating code: {e}")
            raise

    def parse_generated_code(self, generated_code: str, project_name: str) -> Dict[str, str]:
        """생성된 코드를 파일별로 분리 (Regex 사용)"""
        files = {}
        
        # Pattern: @@@START_FILE:path@@@\n(content)\n@@@END_FILE@@@
        # Allow optional whitespace around filename
        pattern = r"@@@START_FILE:\s*(.*?)\s*@@@\n(.*?)\n@@@END_FILE@@@"
        
        matches = list(re.finditer(pattern, generated_code, re.DOTALL))
        
        if matches:
            logger.info(f"Found {len(matches)} files using custom delimiters.")
            for match in matches:
                filepath = match.group(1).strip()
                content = match.group(2)
                files[filepath] = content
        else:
            logger.warning("No custom file delimiters found. Fallback to legacy parsing.")
            # Legacy parsing (fallback)
            current_file = None
            content = []
            lines = generated_code.split('\n')
            for line in lines:
                line_strip = line.strip()
                detected_file = None
                if 'src/main.py' in line: detected_file = 'src/main.py'
                elif 'src/scanner.py' in line: detected_file = 'src/scanner.py'
                elif 'tests/test_main.py' in line: detected_file = 'tests/test_main.py'
                elif 'docs/README.md' in line: detected_file = 'docs/README.md'
                
                if detected_file and (line_strip.startswith('```') or line_strip.startswith('#')):
                    if current_file and content:
                        files[current_file] = '\n'.join(content).strip()
                    current_file = detected_file
                    content = []
                else:
                    if current_file:
                        if line_strip.startswith('```'): continue
                        content.append(line)
            if current_file and content:
                files[current_file] = '\n'.join(content).strip()

        return files

    def save_code_to_files(self, project_name: str, files: Dict[str, str], output_dir: str) -> str:
        """코드를 파일로 저장 (Scaffolding 포함)"""
        project_name_kebab = project_name.lower().replace(' ', '-').replace('_', '-')
        project_dir = Path(output_dir) / project_name_kebab

        # Ensure directories
        (project_dir / 'src').mkdir(parents=True, exist_ok=True)
        (project_dir / 'tests').mkdir(parents=True, exist_ok=True)
        (project_dir / 'docs').mkdir(parents=True, exist_ok=True)

        # Scaffolding: Create __init__.py if not present
        if 'src/__init__.py' not in files:
            files['src/__init__.py'] = ""
        if 'tests/__init__.py' not in files:
            files['tests/__init__.py'] = ""

        for filename, content in files.items():
            filepath = project_dir / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Created: {filename}")

        # Default requirements.txt if missing
        if 'requirements.txt' not in files:
            (project_dir / 'requirements.txt').write_text("pytest>=7.4.0\nrequests>=2.31.0\n", encoding='utf-8')
            logger.info("Created: requirements.txt (default)")
        
        # Default .gitignore if missing
        if '.gitignore' not in files:
            gitignore_content = "__pycache__/\n*.py[cod]\n.env\nvenv/\n.DS_Store\n"
            (project_dir / '.gitignore').write_text(gitignore_content, encoding='utf-8')
            logger.info("Created: .gitignore (default)")
        
        logger.info(f"Project created at: {project_dir}")
        return str(project_dir)

if __name__ == "__main__":
    try:
        coder = CodeGenerator()
        print("✅ CodeGenerator initialized successfully.")
    except Exception as e:
        print(f"❌ Initialization failed: {e}")