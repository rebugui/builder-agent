#!/usr/bin/env python3
"""
Builder Agent - DevOps 도구 자동 생성 (Intelligence Agent GLM Client 재사용)

Usage:
    python3 builder_agent.py
"""

import os
import re
import requests
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum

# Intelligence Agent GLM Client 재사용
# 상대 경로로 임포트 (같은 프로젝트 내)
try:
    from modules.intelligence.writer import GLMClient
except ImportError:
    # 프로젝트 루트가 달라지 않을 경우 처리
    # 이 경우는 Builder Agent를 별도로 실행하는 것이므로,
    # 현재 디렉토리 기준으로 임포트를 시도합니다.
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from modules.intelligence.writer import GLMClient

# 환경 변수 로드
def load_env():
    """환경 변수 로드 헬퍼 함수"""
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    env_path = os.path.join(project_root, '.env')

    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    try:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
                    except ValueError:
                        pass

# 시작 시 .env 로드
load_env()

# API 설정 (환경 변수)
GLM_API_KEY = os.getenv("GLM_API_KEY", "")


def sanitize_project_name(name: str) -> str:
    """
    프로젝트 이름을 안전한 경로명으로 변환
    경로 순회(Path Traversal) 공격 방지
    """
    if not name:
        return "unnamed-project"
    
    sanitized = name.lower()
    sanitized = sanitized.replace(' ', '-')
    sanitized = re.sub(r'\.{2,}', '', sanitized)
    sanitized = re.sub(r'[/\\:]', '-', sanitized)
    sanitized = re.sub(r'[^a-z0-9\-_]', '', sanitized)
    sanitized = re.sub(r'-{2,}', '-', sanitized)
    sanitized = sanitized.strip('-_')
    
    return sanitized if sanitized else "unnamed-project"


def validate_output_path(base_dir: str, project_name: str) -> str:
    """
    출력 경로가 기본 디렉토리 내에 있는지 검증
    """
    safe_name = sanitize_project_name(project_name)
    base_path = Path(base_dir).resolve()
    target_path = (base_path / safe_name).resolve()
    
    try:
        target_path.relative_to(base_path)
    except ValueError:
        raise ValueError(f"Invalid project path: {target_path} is outside {base_path}")
    
    return str(target_path)
GLM_BASE_URL = os.getenv("GLM_BASE_URL", "https://api.z.ai/api/coding/paas/v4/")
GLM_MODEL = os.getenv("GLM_MODEL", "glm-4.7")


class BuilderAgent:
    """Builder Agent (DevOps 도구 자동 생성) - Intelligence Agent GLM Client 재사용"""

    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        """
        초기화 (GLM Client 재사용)

        Args:
            api_key: GLM API Key (None이면 환경변수에서 자동 로드)
            base_url: GLM API Base URL
            model: 사용할 모델 (기본: glm-4.7)
        """
        if api_key is None:
            api_key = GLM_API_KEY

        if base_url is None:
            base_url = GLM_BASE_URL

        if model is None:
            model = GLM_MODEL

        if not api_key:
            raise ValueError("GLM_API_KEY 환경변수가 설정되지 않았습니다.")

        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.timeout = 120  # 타임아웃 120초

        # Intelligence Agent GLM Client 재사용
        self.client = GLMClient(api_key, base_url, model)

        # 시스템 프롬프트 (DevOps Expert 페르소나)
        self.system_prompt = """당신은 10년 이상의 경력을 가진 DevOps 엔지니어입니다.
Docker, Kubernetes, Helm, CI/CD 파이프라인에 깊은 지식을 보유하고 있습니다.

## 📘 DevOps Expert 페르소나 가이드라인

### 1. 코드 작성 가이드라인

**구조화된 코드 작성:**
- `src/`: 핵 모듈 (main logic)
- `tests/`: 단위 테스트
- `docs/`: 문서화 (README, DESIGN)

**모듈화:**
- 기능별로 분리 (scanner, parser, analyzer, reporter)
- 각 모듈은 독립적으로 실행 가능해야 함
- `__main__.py`: 진입점

**파일 명명:**
- 알파벳, 숫자, 언더스코어(_) 사용
- 기능을 설명하는 이름 사용 (예: `docker_scanner.py`)

### 2. 보안 코딩 가이드라인

**보안 코딩 원칙 (Security First):**
- **입력 검증 (Input Validation)**:
  - 모든 사용자 입력을 검증하고 필터링
  - SQL Injection 방지 (prepared statements)
  - Command Injection 방지 (subprocess 인자 분리)

- **위험한 함수 사용 제한**:
  - `subprocess`, `eval`, `exec` 사용 최소화
  - 사용 시, 인자를 리스트로 전달하고 shell=False 설정
  - 절대 사용자 입력을 command 인자로 직접 전달하지 않음

- **에러 처리 (Error Handling)**:
  - 모든 예외를 잡고 처리
  - 사용자에게 안전한 에러 메시지 제공
  - 중요한 정보(암호, 키 등)는 로그에 남기지 않음

### 3. 문서화 가이드라인

**코드 문서화 (Code Documentation):**
- 모든 함수에 docstrings 작성 (Google Style)
- docstrings: 기능, 인자, 반환값, 예시 포함
- 모듈 레벨 docstring 작성

**README 작성:**
- 프로젝트 설명
- 설치 및 실행 방법
- 사용 예시
- 라이선스 (MIT)

**아키텍처 문서:**
- 시스템 아키텍처 다이어그램 (Mermaid)
- 데이터 흐름 설명
- 주요 모듈 간 상호작용 설명

### 4. 테스트 가이드라인

**단위 테스트 (Unit Tests):**
- pytest 사용
- 각 모듈별로 테스트 작성 (scanner_test.py, parser_test.py)
- 경계 조건 테스트 (valid input, invalid input)
- Mock 사용 (데이터베이스, API 호출)

---

## 🚀 Builder Agent 기능

### 1. 주제 선정 (Topic Selection)
- 데이터베이스에서 미완료 주제 조회
- 필터링: 유용성, 구현 가능성, 취약점 관련성
- 추천: 최적의 주제 1개 추천
- README.md 생성: 주제 설명, 요구사항, 아키텍처

### 2. 코드 생성 (Code Generation)
- LLM을 사용하여 Python 코드 생성 (GLM-4.7)
- 구조화된 코드 작성 (src/, tests/, docs/)
- 보안 코딩 가이드라인 준수 (input validation, subprocess 제한)
- 문서화 (docstrings, README)

### 3. 자가 수정 루프 (Self-Correction Loop)
- 샌드박스 환경에서 코드 실행 (Docker/venv)
- 에러 감지 및 LLM 분석
- 자동 수정 및 재시도 (최대 3회)
- 성공 시 완료

### 4. GitOps (GitHub 통합)
- GitHub API를 사용하여 저장소 생성
- 코드 push 및 자동 배포
- 릴리즈 노트 작성
- URL 추적

---

## 📋 출력 형식 (Markdown)

코드는 Markdown 형식으로 작성되어야 합니다:

```python
# src/main.py
import subprocess
import socket

def scan_web_directory(target_url):
    '''웹 디렉토리 스캐너 예제'''
    try:
        response = subprocess.check_output(
            ['ping', '-c', '1', target_url],
            timeout=10,
            shell=False,
            capture_output=True
        )
        return response.decode('utf-8')
    except subprocess.TimeoutExpired:
        return "Timeout"
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    target = "example.com"
    result = scan_web_directory(target)
    print(result)
```

```python
# tests/test_scanner.py
import unittest
from src.main import scan_web_directory

class TestScanner(unittest.TestCase):
    def test_scan_success(self):
        result = scan_web_directory("google.com")
        self.assertNotEqual(result, "Timeout")
        self.assertNotEqual(result, "Error")

    def test_scan_timeout(self):
        result = scan_web_directory("invalid-url")
        self.assertEqual(result, "Error")

if __name__ == "__main__":
    unittest.main()
```

---

## 💡 DevOps Expert 페르소나 특화

**Docker, Kubernetes, Helm, CI/CD에 특화된 전문 지식 활용:**
- 최신 DevOps 트렌드 (GitOps, DevSecOps, IaC)
- 보안 취약점 (Container escape, K8s RBAC, CI/CD secrets)
- 모범 사례 (Production-ready configuration, Immutable infrastructure)

---

## 🎯 작업 요구사항

1. **구조화된 코드 작성**: src/, tests/, docs/ 폴더 구조
2. **보안 코딩 가이드라인 준수**: input validation, subprocess 제한
3. **문서화**: docstrings, README, DESIGN.md
4. **테스트**: pytest 사용, 경계 조건 테스트, Mock 사용
5. **코드 생성**: GLM-4.7을 사용하여 Python 코드 생성
6. **자가 수정 루프**: 에러 감지 및 자동 수정 (최대 3회)
7. **GitOps**: GitHub API 통합 (repo 생성, push, 릴리즈)

---

## 🚀 코드 생성 시작

요청한 주제에 맞는 DevOps 도구의 Python 코드를 작성해주세요.
"""

    def generate_python_code(self, tool_name: str, description: str) -> str:
        """
        Python 코드 생성 (Intelligence Agent GLM Client 재사용)

        Args:
            tool_name: 도구 이름 (예: "Docker Container Monitor")
            description: 도구 설명 (예: "도커 컨테이너 리소스 사용량을 모니터링하는 도구입니다.")

        Returns:
            생성된 Python 코드 (Markdown 형식)
        """
        # 사용자 프롬프트 생성
        user_prompt = f"""다음 DevOps 도구의 Python 코드를 작성해주세요.

=== 도구 정보 ===
도구 이름: {tool_name}
설명: {description}

=== 작업 요구사항 ===

1. **구조화된 코드 작성**:
   - `src/`: 핵 모듈 (main logic)
   - `tests/`: 단위 테스트
   - `docs/`: 문서화 (README, DESIGN)

2. **모듈화**:
   - 기능별로 분리 (scanner, parser, analyzer, reporter)
   - 각 모듈은 독립적으로 실행 가능해야 함
   - `__main__.py`: 진입점

3. **보안 코딩 가이드라인**:
   - 모든 사용자 입력을 검증하고 필터링
   - SQL Injection 방지 (prepared statements)
   - Command Injection 방지 (subprocess 인자 분리, shell=False)
   - 에러 처리 (try-catch)

4. **문서화**:
   - 모든 함수에 docstrings 작성 (Google Style)
   - README 작성 (설치 및 실행 방법, 사용 예시, 라이선스)

5. **테스트**:
   - pytest 사용
   - 단위 테스트 작성 (scanner_test.py, parser_test.py)
   - 경계 조건 테스트 (valid input, invalid input)

=== 출력 형식 (Markdown) ===

모든 코드는 Markdown 형식으로 작성되어야 합니다.

```python
# src/main.py
import subprocess
import socket

def scan_web_directory(target_url):
    '''웹 디렉토리 스캐너 예제'''
    try:
        response = subprocess.check_output(
            ['ping', '-c', '1', target_url],
            timeout=10,
            shell=False,
            capture_output=True
        )
        return response.decode('utf-8')
    except subprocess.TimeoutExpired:
        return "Timeout"
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    target = "example.com"
    result = scan_web_directory(target)
    print(result)
```

```python
# tests/test_scanner.py
import unittest
from src.main import scan_web_directory

class TestScanner(unittest.TestCase):
    def test_scan_success(self):
        result = scan_web_directory("google.com")
        self.assertNotEqual(result, "Timeout")
        self.assertNotEqual(result, "Error")

    def test_scan_timeout(self):
        result = scan_web_directory("invalid-url")
        self.assertEqual(result, "Error")

if __name__ == "__main__":
    unittest.main()
```

---

모든 코드를 Markdown으로 작성해주세요.
"""

        # GLM 호출 (Intelligence Agent GLM Client 재사용)
        generated_code = self.client.chat(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt
        )

        return generated_code

    def parse_generated_code(self, generated_code: str, tool_name: str) -> dict:
        """
        생성된 코드를 파일별로 분리

        Args:
            generated_code: 생성된 코드
            tool_name: 도구 이름 (kebab-case로 변환)

        Returns:
            파일별 분리된 코드 딕셔너리
        """
        # 간단한 파싱 로직 (backtick(````)으로 구분)
        files = {}
        current_file = None
        content = []

        lines = generated_code.split('\n')

        for line in lines:
            # 파일 시작 감지
            if line.strip().startswith('```') or line.strip().startswith('# '):
                # 이전 파일 내용 저장
                if current_file and content:
                    files[current_file] = '\n'.join(content).strip()

                # 새 파일 감지
                if 'src/' in line:
                    current_file = 'src/main.py'
                    content = []
                elif 'tests/' in line:
                    current_file = f'tests/test_{tool_name.replace("-", "_")}.py'
                    content = []
                elif 'docs/' in line:
                    current_file = 'docs/README.md'
                    content = []
            else:
                # 코드 내용 추가
                content.append(line)

        # 마지막 파일 내용 저장
        if current_file and content:
            files[current_file] = '\n'.join(content).strip()

        return files

    def create_readme(self, tool_name: str, description: str) -> str:
        """
        README.md 생성

        Args:
            tool_name: 도구 이름
            description: 도구 설명

        Returns:
            README.md 내용
        """
        tool_name_kebab = tool_name.lower().replace(' ', '-')

        readme = f"""# {tool_name}

## 설명

{description}

## 기능

- Docker Container Monitor
- Kubernetes Pod Resource Analyzer
- CI/CD Pipeline Optimizer

## 설치

```bash
pip install -r requirements.txt
```

## 사용법

```bash
python3 -m src.main
```

## 구조

```
{tool_name_kebab}/
├── src/
│   ├── main.py
│   ├── scanner.py
│   ├── parser.py
│   └── reporter.py
├── tests/
│   ├── test_scanner.py
│   ├── test_parser.py
│   └── test_reporter.py
└── docs/
    ├── README.md
    └── DESIGN.md
```

## 라이선스

MIT License

## 연락

이 프로젝트는 OpenClaw "Digital Duo"의 일부입니다.
"""

        return readme

    def generate_project_structure(self, tool_name: str, files: dict) -> str:
        """
        프로젝트 구조 생성

        Args:
            tool_name: 도구 이름
            files: 파일별 코드

        Returns:
            프로젝트 구조 (Markdown)
        """
        tool_name_kebab = sanitize_project_name(tool_name)

        project_structure = f"""
# {tool_name_kebab}

## 프로젝트 구조

```
{tool_name_kebab}/
├── src/
├── tests/
├── docs/
└── README.md
```

## 파일 목록

"""

        for filename in files.keys():
            project_structure += f"- {filename}\n"

        return project_structure

    def save_code_to_files(self, tool_name: str, files: dict, output_dir: str):
        """
        코드를 파일로 저장 (경로 순회 공격 방지)

        Args:
            tool_name: 도구 이름
            files: 파일별 코드
            output_dir: 출력 디렉토리

        Raises:
            ValueError: 유효하지 않은 경로인 경우
        """
        tool_name_kebab = sanitize_project_name(tool_name)
        project_dir = validate_output_path(output_dir, tool_name)
        
        project_path = Path(project_dir).resolve()
        output_path = Path(output_dir).resolve()
        
        if not str(project_path).startswith(str(output_path)):
            raise ValueError(f"Security: Path traversal attempt detected")

        os.makedirs(os.path.join(project_dir, 'src'), exist_ok=True)
        os.makedirs(os.path.join(project_dir, 'tests'), exist_ok=True)
        os.makedirs(os.path.join(project_dir, 'docs'), exist_ok=True)

        for filename, content in files.items():
            safe_filename = sanitize_project_name(filename.replace('.py', '')) + '.py'
            filepath = os.path.join(project_dir, safe_filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  → Created: {safe_filename}")

        readme_content = self.create_readme(tool_name, f"{tool_name} DevOps 도구")
        readme_path = os.path.join(project_dir, 'README.md')
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        print(f"  → Created: README.md")

        print(f"\n✅ 프로젝트 생성 완료: {project_dir}")


def main():
    """메인 함수"""
    print("=" * 60)
    print("🚀 Builder Agent (Intelligence Agent GLM Client 재사용)")
    print("=" * 60)
    print()

    # Builder Agent 인스턴스 생성
    builder = BuilderAgent()

    # 테스트: DevOps 도구 코드 생성
    tool_name = "Docker Container Monitor"
    description = "도커 컨테이너 리소스 사용량을 모니터링하는 도구입니다."

    print(f"📋 도구: {tool_name}")
    print(f"📝 설명: {description}")
    print()

    print("🚀 GLM-4.7을 사용하여 Python 코드 생성 중...")
    print()

    # 코드 생성
    generated_code = builder.generate_python_code(tool_name, description)

    print("✅ Python 코드 생성 완료!")
    print()
    print("=" * 60)
    print("📋 생성된 코드:")
    print("=" * 60)
    print(generated_code)
    print("=" * 60)
    print()

    # 코드 파싱
    print("🔄 코드 파싱 중...")
    print()

    tool_name_kebab = sanitize_project_name(tool_name)
    files = builder.parse_generated_code(generated_code, tool_name_kebab)

    print("✅ 코드 파싱 완료!")
    print()
    print("=" * 60)
    print("📋 생성된 파일 구조:")
    print("=" * 60)
    for filename, content in files.items():
        print(f"📄 {filename}")
        print("-" * 60)
        print(content[:200] + ("..." if len(content) > 200 else ""))
        print()

    # 프로젝트 구조 생성
    print("🏗️  프로젝트 구조 생성 중...")
    print()

    project_structure = builder.generate_project_structure(tool_name, files)

    print("✅ 프로젝트 구조 생성 완료!")
    print()
    print("=" * 60)
    print("📋 프로젝트 구조:")
    print("=" * 60)
    print(project_structure)
    print()

    # 코드 파일 저장
    print("💾  코드 파일 저장 중...")
    print()

    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'projects')
    builder.save_code_to_files(tool_name, files, output_dir)

    print()
    print("=" * 60)
    print("🎉 Builder Agent 완료! (Intelligence Agent GLM Client 재사용)")
    print("=" * 60)


if __name__ == "__main__":
    main()
