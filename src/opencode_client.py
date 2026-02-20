#!/usr/bin/env python3
"""
OpenCode Client - OpenCode CLI/Server 연동

OpenCode를 활용한 코드 생성, 리뷰, 테스트 기능 제공
"""

import os
import re
import json
import subprocess
import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class OpenCodeModel(Enum):
    """OpenCode 지원 모델"""
    GLM_5 = "zai-coding-plan/glm-5"
    GLM_4_7 = "zai-coding-plan/glm-4.7"
    GLM_4_7_FLASH = "zai-coding-plan/glm-4.7-flash"
    GPT_5_NANO = "opencode/gpt-5-nano"
    BIG_PICKLE = "opencode/big-pickle"


class OpenCodeAgent(Enum):
    """OpenCode 에이전트"""
    BUILD = "build"
    PLAN = "plan"
    EXPLORE = "explore"
    SUMMARY = "summary"


@dataclass
class OpenCodeResult:
    """OpenCode 실행 결과"""
    success: bool
    output: str
    error: Optional[str] = None
    files: Optional[Dict[str, str]] = None
    session_id: Optional[str] = None


class OpenCodeClient:
    """
    OpenCode CLI 클라이언트
    
    Note: OpenCode CLI는 대화형 TUI 도구입니다.
    subprocess에서 실행 시 타이밍 이슈가 있을 수 있어
    GLM Direct 모드를 기본으로 사용하는 것을 권장합니다.
    
    Usage:
        client = OpenCodeClient()
        
        # 코드 생성
        result = client.generate_code("Docker Monitor", "도커 컨테이너 모니터링 도구")
        
        # 코드 리뷰
        review = client.review_code(code_content)
        
        # 테스트 생성
        tests = client.generate_tests(source_code)
    """
    
    def __init__(
        self,
        model: str = "zai-coding-plan/glm-5",
        project_path: str = None,
        timeout: int = 300
    ):
        self.model = model
        self.project_path = Path(project_path or os.getcwd())
        self.timeout = timeout
        
        self.opencode_path = self._find_opencode()
        self._available = self.opencode_path is not None
        
        if self._available:
            logger.info(f"OpenCode 클라이언트 초기화: model={model}, path={self.opencode_path}")
        else:
            logger.warning("OpenCode를 찾을 수 없습니다. GLM Direct 모드를 사용하세요.")
    
    def _find_opencode(self) -> Optional[str]:
        """OpenCode 실행 파일 경로 찾기"""
        paths = [
            "/usr/local/bin/opencode",
            "/usr/bin/opencode",
            os.path.expanduser("~/.opencode/bin/opencode"),
            os.path.expanduser("~/.local/bin/opencode"),
        ]
        
        for path in paths:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                return path
        
        # PATH에서 찾기
        result = subprocess.run(
            ["which", "opencode"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return result.stdout.strip()
        
        return None
    
    def run(
        self,
        prompt: str,
        agent: str = None,
        session_id: str = None,
        format: str = "default",
        timeout: int = None
    ) -> OpenCodeResult:
        """
        OpenCode 실행
        
        Args:
            prompt: 프롬프트
            agent: 에이전트 타입 (build, plan, explore) - None이면 기본 에이전트
            session_id: 세션 ID (이어서 작업할 때)
            format: 출력 형식 (default, json)
            timeout: 타임아웃 (초)
        
        Returns:
            OpenCodeResult
        """
        cmd = [
            self.opencode_path, "run",
            "-m", self.model,
        ]
        
        if agent:
            cmd.extend(["--agent", agent])
        
        if session_id:
            cmd.extend(["-c", "-s", session_id])
        
        cmd.append(prompt)
        
        logger.debug(f"OpenCode 실행: {' '.join(cmd[:5])}...")
        
        env = os.environ.copy()
        env["PATH"] = "/usr/local/bin:/usr/bin:/bin:" + env.get("PATH", "")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=timeout or self.timeout,
                env=env
            )
            
            combined_output = result.stdout
            if result.stderr and "subagent" not in result.stderr.lower():
                logger.warning(f"OpenCode stderr: {result.stderr[:500]}")
            
            if result.returncode != 0:
                return OpenCodeResult(
                    success=False,
                    output=combined_output,
                    error=result.stderr if result.stderr else "Unknown error"
                )
            
            return OpenCodeResult(
                success=True,
                output=combined_output
            )
            
        except subprocess.TimeoutExpired:
            return OpenCodeResult(
                success=False,
                output="",
                error=f"Timeout after {timeout or self.timeout} seconds"
            )
        except FileNotFoundError as e:
            return OpenCodeResult(
                success=False,
                output="",
                error=f"OpenCode executable not found: {e}"
            )
        except Exception as e:
            return OpenCodeResult(
                success=False,
                output="",
                error=str(e)
            )
    
    def generate_code(
        self,
        project_name: str,
        description: str,
        files_needed: List[str] = None
    ) -> OpenCodeResult:
        """
        프로젝트 코드 생성
        
        Args:
            project_name: 프로젝트 이름
            description: 프로젝트 설명
            files_needed: 필요한 파일 목록
        
        Returns:
            OpenCodeResult (files 필드에 파싱된 코드)
        """
        files_spec = files_needed or [
            "src/__init__.py",
            "src/main.py",
            "src/core.py",
            "tests/__init__.py",
            "tests/test_main.py",
            "docs/README.md",
            "requirements.txt"
        ]
        
        prompt = f"""
다음 DevOps/보안 도구의 Python 코드를 작성해주세요.

프로젝트 이름: {project_name}
설명: {description}

필요한 파일:
{chr(10).join(f'- {f}' for f in files_spec)}

코딩 가이드라인:
1. 보안 코딩 원칙 준수 (입력 검증, 에러 처리)
2. 모든 함수에 docstring 작성
3. type hints 사용
4. pytest 기반 단위 테스트 작성

각 파일은 반드시 다음 형식으로 작성해주세요:
@@@START_FILE:파일경로@@@
파일내용
@@@END_FILE@@@

예시:
@@@START_FILE:src/main.py@@@
import sys

def main():
    print("Hello")

if __name__ == "__main__":
    main()
@@@END_FILE@@@
"""
        
        result = self.run(prompt, agent="build")
        
        if result.success:
            result.files = self._parse_files(result.output)
        
        return result
    
    def review_code(
        self,
        code: str,
        focus_areas: List[str] = None
    ) -> OpenCodeResult:
        """
        코드 리뷰
        
        Args:
            code: 리뷰할 코드
            focus_areas: 집중할 영역 (security, performance, readability)
        
        Returns:
            OpenCodeResult
        """
        areas = focus_areas or ["security", "performance", "readability", "testability"]
        
        prompt = f"""
다음 코드를 리뷰하고 개선점을 제안해주세요.

```python
{code}
```

평가 항목:
{chr(10).join(f'- {a}' for a in areas)}

다음 형식으로 JSON 응답해주세요:
{{
    "overall_score": 1-10,
    "issues": [
        {{"type": "security", "severity": "high/medium/low", "line": N, "description": "...", "suggestion": "..."}}
    ],
    "improvements": ["..."],
    "positive_aspects": ["..."]
}}
"""
        
        return self.run(prompt, agent="build")
    
    def generate_tests(
        self,
        source_code: str,
        test_framework: str = "pytest"
    ) -> OpenCodeResult:
        """
        테스트 코드 생성
        
        Args:
            source_code: 소스 코드
            test_framework: 테스트 프레임워크
        
        Returns:
            OpenCodeResult
        """
        prompt = f"""
다음 코드에 대한 {test_framework} 테스트 코드를 작성해주세요.

```python
{source_code}
```

테스트 가이드라인:
1. 모든 함수/메서드에 대한 테스트 케이스
2. 정상 케이스 + 경계 케이스 + 에러 케이스
3. mock을 적절히 활용
4. 테스트 커버리지 최대화

테스트 코드를 @@@START_FILE:tests/test_code.py@@@ 와 @@@END_FILE@@@ 사이에 작성해주세요.
"""
        
        result = self.run(prompt, agent="build")
        
        if result.success:
            result.files = self._parse_files(result.output)
        
        return result
    
    def fix_code(
        self,
        code: str,
        error_message: str,
        error_type: str = None
    ) -> OpenCodeResult:
        """
        코드 수정 (에러 해결)
        
        Args:
            code: 문제가 있는 코드
            error_message: 에러 메시지
            error_type: 에러 타입
        
        Returns:
            OpenCodeResult
        """
        prompt = f"""
다음 코드에서 발생한 에러를 수정해주세요.

```python
{code}
```

에러 타입: {error_type or "Unknown"}
에러 메시지:
{error_message}

수정된 코드를 @@@START_FILE:fixed.py@@@ 와 @@@END_FILE@@@ 사이에 작성해주세요.
수정 내용을 간단히 설명해주세요.
"""
        
        result = self.run(prompt, agent="build")
        
        if result.success:
            result.files = self._parse_files(result.output)
        
        return result
    
    def plan_project(
        self,
        project_name: str,
        description: str
    ) -> OpenCodeResult:
        """
        프로젝트 계획 수립
        
        Args:
            project_name: 프로젝트 이름
            description: 프로젝트 설명
        
        Returns:
            OpenCodeResult
        """
        prompt = f"""
다음 프로젝트의 상세 구현 계획을 수립해주세요.

프로젝트 이름: {project_name}
설명: {description}

계획에 포함할 내용:
1. 아키텍처 설계
2. 모듈 구조
3. API 설계
4. 데이터 모델
5. 의존성
6. 구현 단계 (우선순위 포함)
7. 테스트 전략
8. 배포 계획

Markdown 형식으로 작성해주세요.
"""
        
        return self.run(prompt, agent="plan")
    
    def _parse_files(self, output: str) -> Dict[str, str]:
        """
        출력에서 파일 파싱
        
        Args:
            output: OpenCode 출력
        
        Returns:
            파일 경로 -> 내용 딕셔너리
        """
        files = {}
        
        # 패턴 1: @@@START_FILE:path@@@ ... @@@END_FILE@@@
        pattern1 = r'@@@START_FILE:(.+?)@@@\n(.*?)\n?@@@END_FILE@@@'
        matches1 = re.findall(pattern1, output, re.DOTALL)
        
        for filepath, content in matches1:
            files[filepath.strip()] = content.strip()
        
        # 패턴 2: ```python ... ``` (파일명 없는 경우)
        if not files:
            pattern2 = r'```python\n(.*?)\n```'
            matches2 = re.findall(pattern2, output, re.DOTALL)
            
            for i, content in enumerate(matches2):
                files[f"code_{i+1}.py"] = content.strip()
        
        return files
    
    def save_files(
        self,
        files: Dict[str, str],
        output_dir: str
    ) -> List[str]:
        """
        파일 저장
        
        Args:
            files: 파일 딕셔너리
            output_dir: 출력 디렉토리
        
        Returns:
            저장된 파일 경로 목록
        """
        output_path = Path(output_dir)
        saved_files = []
        
        for filepath, content in files.items():
            file_path = output_path / filepath
            
            # 디렉토리 생성
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 파일 저장
            file_path.write_text(content, encoding='utf-8')
            saved_files.append(str(file_path))
            
            logger.info(f"파일 저장: {file_path}")
        
        return saved_files


class OpenCodeAsyncClient(OpenCodeClient):
    """비동기 OpenCode 클라이언트"""
    
    async def run_async(
        self,
        prompt: str,
        agent: str = "build",
        session_id: str = None,
        format: str = "default",
        timeout: int = None
    ) -> OpenCodeResult:
        """비동기 실행"""
        cmd = [
            self.opencode_path, "run",
            "-m", self.model,
            "--agent", agent,
            "--format", format,
        ]
        
        if session_id:
            cmd.extend(["-s", session_id])
        
        cmd.append(prompt)
        
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=self.project_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout or self.timeout
            )
            
            stdout_str = stdout.decode('utf-8') if stdout else ""
            stderr_str = stderr.decode('utf-8') if stderr else ""
            
            if proc.returncode != 0:
                return OpenCodeResult(
                    success=False,
                    output=stdout_str,
                    error=stderr_str
                )
            
            return OpenCodeResult(
                success=True,
                output=stdout_str
            )
            
        except asyncio.TimeoutError:
            return OpenCodeResult(
                success=False,
                output="",
                error=f"Timeout after {timeout or self.timeout} seconds"
            )
        except Exception as e:
            return OpenCodeResult(
                success=False,
                output="",
                error=str(e)
            )
    
    async def generate_code_async(
        self,
        project_name: str,
        description: str
    ) -> OpenCodeResult:
        """비동기 코드 생성"""
        sync_result = self.generate_code(project_name, description)
        # 동기 메서드 재사용 (OpenCode CLI는 어차피 subprocess)
        return sync_result


# 편의 함수
def get_default_client() -> OpenCodeClient:
    """기본 OpenCode 클라이언트 반환"""
    return OpenCodeClient(
        model="zai-coding-plan/glm-5",
        project_path=os.getenv("OPENCLAW_ROOT", os.getcwd())
    )
