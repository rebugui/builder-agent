#!/usr/bin/env python3
"""
Builder Agent - Code Generator

GLM-5 + OpenCode를 사용하여 구조화된 Python 코드를 생성합니다.
OpenCode 통합으로 에이전트 기반 코드 생성 지원
"""

import os
import sys
import re
from typing import Dict, List, Optional
from pathlib import Path
from enum import Enum

# Add project root to sys.path
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.append(str(current_dir))

from builder_config import config
from prompts import Prompts
from utils.logger import setup_logger

# OpenCode Client
try:
    from opencode_client import OpenCodeClient, OpenCodeResult
    OPENCODE_AVAILABLE = True
except ImportError:
    OPENCODE_AVAILABLE = False

# Intelligence Agent GLM Client (Fallback)
try:
    from llm_client import GLMClient
except ImportError:
    try:
        from modules.intelligence.llm_client import GLMClient
    except ImportError:
        GLMClient = None 

logger = setup_logger("CodeGenerator")


class CodeGeneratorMode(Enum):
    """코드 생성 모드"""
    OPENCODE = "opencode"   # OpenCode CLI 사용 (권장)
    GLM_DIRECT = "glm"      # GLM API 직접 호출 (Fallback)


class CodeGenerator:
    """
    Code Generator (코드 생성)
    
    OpenCode CLI를 우선 사용하고, 실패 시 GLM API로 Fallback
    """

    def __init__(self, mode: str = "opencode"):
        """
        초기화
        
        Args:
            mode: 생성 모드 ("opencode" 또는 "glm")
        """
        self.mode = CodeGeneratorMode(mode)
        self.api_key = config.GLM_API_KEY
        self.base_url = config.GLM_BASE_URL
        self.model = config.GLM_MODEL
        self.project_path = str(config.PROJECT_ROOT)
        
        # OpenCode 클라이언트 초기화
        self.opencode_client = None
        if self.mode == CodeGeneratorMode.OPENCODE and OPENCODE_AVAILABLE:
            try:
                self.opencode_client = OpenCodeClient(
                    model="zai-coding-plan/glm-5",
                    project_path=self.project_path,
                    timeout=300
                )
                logger.info("✅ OpenCode 클라이언트 초기화 성공")
            except Exception as e:
                logger.warning(f"OpenCode 초기화 실패, GLM Fallback: {e}")
                self.mode = CodeGeneratorMode.GLM_DIRECT
        
        # GLM Client 초기화 (Fallback)
        if self.mode == CodeGeneratorMode.GLM_DIRECT:
            if not self.api_key:
                raise ValueError("GLM_API_KEY 환경변수가 설정되지 않았습니다.")
            
            if GLMClient:
                self.client = GLMClient(self.api_key, self.base_url, self.model)
                logger.info("✅ GLM Client 초기화 성공 (Direct Mode)")
            else:
                raise ImportError("GLMClient module not found. Check your python path.")

        self.system_prompt = Prompts.DEVOPS_EXPERT_SYSTEM
        logger.info(f"CodeGenerator 모드: {self.mode.value}")

    def generate_spec(self, project_name: str, short_description: str) -> str:
        """상세 요구사항 명세서 생성"""
        logger.info(f"Generating technical spec for: {project_name}")
        
        spec_prompt = f"""You are a Software Architect. Create a detailed technical specification for the project '{project_name}'.

Short Description: {short_description}

The specification must be in Markdown format and include:
1. Project Overview
2. User Stories / Requirements
3. Architecture & Tech Stack (Python based)
4. API Design / CLI Commands
5. Database Schema (if applicable)
6. Directory Structure

Output ONLY the Markdown content, starting with '# Technical Specification'."""
        
        if self.mode == CodeGeneratorMode.OPENCODE and self.opencode_client:
            result = self.opencode_client.run(spec_prompt, agent="plan")
            if result.success:
                return result.output
            logger.warning(f"OpenCode 실패, Fallback: {result.error}")
        
        if GLMClient and hasattr(self, 'client'):
            try:
                return self.client.chat(
                    system_prompt="You are an expert Software Architect.",
                    user_prompt=spec_prompt
                )
            except Exception as e:
                logger.error(f"Error generating spec: {e}")
        
        return f"# Technical Specification (Fallback)\n\n{short_description}"

    def generate_code(self, project_name: str, project_description: str) -> str:
        """Python 코드 생성"""
        logger.info(f"Generating code for project: {project_name} (mode: {self.mode.value})")
        
        user_prompt = Prompts.get_code_generation_prompt(project_name, project_description)
        
        if self.mode == CodeGeneratorMode.OPENCODE and self.opencode_client:
            result = self.opencode_client.run(user_prompt, agent="build")
            if result.success:
                logger.info("OpenCode로 코드 생성 성공")
                return result.output
            logger.warning(f"OpenCode 실패, GLM Fallback: {result.error}")
        
        if GLMClient and hasattr(self, 'client'):
            try:
                generated_code = self.client.chat(
                    system_prompt=self.system_prompt,
                    user_prompt=user_prompt
                )
                logger.info("GLM Direct로 코드 생성 성공")
                return generated_code
            except Exception as e:
                logger.error(f"Error generating code: {e}")
                raise
        
        raise RuntimeError("사용 가능한 코드 생성기가 없습니다.")

    def generate_code_with_opencode(
        self,
        project_name: str,
        description: str,
        files_needed: List[str] = None
    ) -> Dict[str, str]:
        """OpenCode로 직접 코드 생성 (파일 딕셔너리 반환)"""
        if not self.opencode_client:
            raise RuntimeError("OpenCode 클라이언트가 초기화되지 않았습니다.")
        
        result = self.opencode_client.generate_code(project_name, description, files_needed)
        
        if result.success and result.files:
            return result.files
        
        raise RuntimeError(f"코드 생성 실패: {result.error}")

    def review_code(self, code: str) -> Dict:
        """코드 리뷰 (OpenCode 사용)"""
        if self.opencode_client:
            result = self.opencode_client.review_code(code)
            if result.success:
                return {"review": result.output, "success": True}
        
        return {"review": None, "success": False}

    def fix_code(self, code: str, error_message: str, error_type: str = None) -> Dict[str, str]:
        """코드 수정 (OpenCode 사용)"""
        if self.opencode_client:
            result = self.opencode_client.fix_code(code, error_message, error_type)
            if result.success and result.files:
                return result.files
        
        return {}

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

        # Default AGPL-3.0 LICENSE if missing
        if 'LICENSE' not in files:
            license_content = """GNU AFFERO GENERAL PUBLIC LICENSE
Version 3, 19 November 2007

Copyright (C) 2024 OpenClaw Project

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.

Additional permission under GNU AGPL version 3 section 7:
If you modify this program, or any covered work, by linking or combining
it with other code, the resulting work must be licensed under AGPL-3.0.
"""
            (project_dir / 'LICENSE').write_text(license_content, encoding='utf-8')
            logger.info("Created: LICENSE (AGPL-3.0)")

        # Default README.md if missing
        if 'README.md' not in files and 'docs/README.md' not in files:
            readme_content = f"""# {project_name}

## Description

{project_name}

## License

This project is licensed under AGPL-3.0. See [LICENSE](LICENSE) for details.

## Development

### Installation

```bash
pip install -r requirements.txt
```

### Running Tests

```bash
pytest tests/
```

## Generated by OpenClaw Builder Agent

This project was automatically generated by [OpenClaw](https://github.com/openclaw/openclaw) Builder Agent.
"""
            (project_dir / 'README.md').write_text(readme_content, encoding='utf-8')
            logger.info("Created: README.md (default)")
        
        logger.info(f"Project created at: {project_dir}")
        return str(project_dir)

if __name__ == "__main__":
    try:
        coder = CodeGenerator()
        print("✅ CodeGenerator initialized successfully.")
    except Exception as e:
        print(f"❌ Initialization failed: {e}")