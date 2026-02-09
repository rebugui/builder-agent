#!/usr/bin/env python3
"""
Builder Agent - Self-Correction Tester

샌드박스 환경에서 코드를 실행하고, 에러를 감지하여 자가 수정 루프를 수행합니다.
"""

import os
import subprocess
import sys
import json
import re
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

# Add project root to sys.path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parents[1]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from modules.builder.builder_config import config
from modules.builder.utils.logger import setup_logger
from modules.builder.coder import CodeGenerator

logger = setup_logger("SelfCorrectionTester")

@dataclass
class TestResult:
    """테스트 결과 데이터 클래스"""
    passed: bool
    stdout: str
    stderr: str
    return_code: int
    error_type: Optional[str] = None
    error_message: Optional[str] = None


class SelfCorrectionTester:
    """Self-Correction Tester (자가 수정 테스터)"""

    def __init__(self, coder: CodeGenerator = None):
        """초기화"""
        self.coder = coder if coder else CodeGenerator()
        self.max_retries = 3
        self.timeout = 30

    def run_unit_tests(self, project_dir: str) -> TestResult:
        """단위 테스트 실행 (pytest)"""
        try:
            result = subprocess.run(
                ['python3', '-m', 'pytest', 'tests/', '-v'],
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            passed = result.returncode == 0
            error_type = None
            error_message = None

            if not passed:
                # 에러 타입 감지
                if 'SyntaxError' in result.stderr: error_type = 'SyntaxError'
                elif 'IndentationError' in result.stderr: error_type = 'IndentationError'
                elif 'ModuleNotFoundError' in result.stderr: error_type = 'ModuleNotFoundError'
                elif 'AttributeError' in result.stderr: error_type = 'AttributeError'
                elif 'NameError' in result.stderr: error_type = 'NameError'
                elif 'AssertionError' in result.stderr: error_type = 'AssertionError'
                elif 'ImportError' in result.stderr: error_type = 'ImportError'
                elif 'TypeError' in result.stderr: error_type = 'TypeError'
                elif 'ValueError' in result.stderr: error_type = 'ValueError'
                elif 'Exception' in result.stderr: error_type = 'Exception'

                # 개선된 에러 메시지 추출
                stderr_lines = result.stderr.split('\n')
                stdout_lines = result.stdout.split('\n')

                # stderr와 stdout 모두 검사
                all_lines = stderr_lines + stdout_lines

                # 에러 라인 찾기 (컨텍스트 포함)
                for i, line in enumerate(all_lines):
                    stripped = line.strip()
                    # 다양한 에러 패턴 매칭
                    if any(pattern in stripped for pattern in [
                        'Error:', 'ERROR ', 'FAILED', 'Error ', 'error:',
                        'AssertionError:', 'Traceback', 'Exception in'
                    ]):
                        # 컨텍스트 포함 (이전 2줄, 이후 2줄)
                        context_start = max(0, i - 2)
                        context_end = min(len(all_lines), i + 3)
                        context = all_lines[context_start:context_end]
                        error_message = '\n'.join(context).strip()
                        break

                # 여전히 못 찾았으면 stdout에서 FAILED 라인 찾기
                if not error_message:
                    for i, line in enumerate(stdout_lines):
                        if 'FAILED' in line or 'failed' in line:
                            context_start = max(0, i - 1)
                            context_end = min(len(stdout_lines), i + 2)
                            context = stdout_lines[context_start:context_end]
                            error_message = '\n'.join(context).strip()
                            break

                # 최후의 수단: stdout/stderr 앞부분 사용
                if not error_message:
                    if result.stdout:
                        error_message = result.stdout.strip()[:500]
                    elif result.stderr:
                        error_message = result.stderr.strip()[:500]
                    else:
                        error_message = "Test failed with no output"

                # 디버그 로그에 전체 출력 기록
                logger.debug(f"=== Test Output (DEBUG) ===")
                logger.debug(f"STDOUT:\n{result.stdout}")
                logger.debug(f"STDERR:\n{result.stderr}")
                logger.debug(f"=== End Debug Output ===")

            return TestResult(
                passed=passed,
                stdout=result.stdout,
                stderr=result.stderr,
                return_code=result.returncode,
                error_type=error_type,
                error_message=error_message
            )

        except subprocess.TimeoutExpired:
            return TestResult(
                passed=False,
                stdout="",
                stderr="Timeout: Test execution exceeded time limit",
                return_code=-1,
                error_type='Timeout',
                error_message='Test execution exceeded time limit'
            )
        except Exception as e:
            return TestResult(
                passed=False,
                stdout="",
                stderr=str(e),
                return_code=-1,
                error_type='Exception',
                error_message=str(e)
            )

    def run_lint_checks(self, project_dir: str) -> TestResult:
        """Lint 체크 (파이썬 문법 검사) - 모든 src/*.py 파일 검사"""
        try:
            src_dir = Path(project_dir) / 'src'
            if not src_dir.exists():
                 return TestResult(False, "", "src directory not found", -1, "FileNotFound", "src directory not found")
            
            py_files = list(src_dir.glob('*.py'))
            if not py_files:
                 return TestResult(False, "", "No python files found in src/", -1, "FileNotFound", "No python files found")

            for py_file in py_files:
                result = subprocess.run(
                    ['python3', '-m', 'py_compile', str(py_file)],
                    cwd=project_dir,
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if result.returncode != 0:
                    return TestResult(
                        passed=False,
                        stdout=result.stdout,
                        stderr=result.stderr,
                        return_code=result.returncode,
                        error_type='SyntaxError',
                        error_message=f"Syntax error in {py_file.name}: {result.stderr.strip() if result.stderr else 'Unknown syntax error'}"
                    )

            return TestResult(True, "All files passed lint check", "", 0)

        except subprocess.TimeoutExpired:
            return TestResult(
                passed=False,
                stdout="",
                stderr="Timeout: Lint check exceeded time limit",
                return_code=-1,
                error_type='Timeout',
                error_message='Lint check exceeded time limit'
            )
        except Exception as e:
            return TestResult(
                passed=False,
                stdout="",
                stderr=str(e),
                return_code=-1,
                error_type='Exception',
                error_message=str(e)
            )

    def analyze_error_with_llm(self, error_message: str, source_code: str, project_name: str) -> str:
        """LLM을 사용하여 에러 분석 및 수정 코드 생성"""
        fix_prompt = f"""다음 Python 코드에서 에러를 수정해주세요.

=== 에러 정보 ===
에러 메시지:
{error_message}

=== 원본 코드 ===
{source_code}

=== 수정 요구사항 ===

1. 에러를 수정하세요.
2. 기존 기능을 유지하세요.
3. 보안 코딩 가이드라인을 준수하세요.

=== 출력 형식 (필수) ===

반드시 아래 형식을 사용하여 수정된 코드를 출력하세요.

@@@START_FILE:수정된파일경로@@@
수정된 코드 내용
@@@END_FILE@@@

예시:
@@@START_FILE:src/main.py@@@
import sys
...
@@@END_FILE@@@
"""
        fixed_code = self.coder.client.chat(
            system_prompt="당신은 Python 코드 디버깅 전문가입니다.",
            user_prompt=fix_prompt
        )
        return fixed_code

    def _parse_with_delimiters(self, code: str, project_name: str) -> Dict[str, str]:
        """커스텀 딜리미터 방식 파싱 (@@@START_FILE:@@@)"""
        pattern = r"@@@START_FILE:\s*(.*?)\s*@@@\n(.*?)\n@@@END_FILE@@@"
        matches = list(re.finditer(pattern, code, re.DOTALL))

        if matches:
            files = {}
            for match in matches:
                filepath = match.group(1).strip()
                content = match.group(2)
                files[filepath] = content
            return files
        return {}

    def _parse_with_code_blocks(self, code: str, project_name: str) -> Dict[str, str]:
        """코드 블록 방식 파싱 (```python``` 등)"""
        files = {}
        pattern = r"```(?:python|py)?\n*(.*?)```"

        matches = re.finditer(pattern, code, re.DOTALL)
        for match in matches:
            content = match.group(1).strip()
            if content and not content.startswith("@@@"):  # 딜리미터가 아닌 경우
                # 기본 파일 경로 추정
                files['src/main.py'] = content
                break

        return files

    def _parse_raw_text(self, code: str, project_name: str) -> Dict[str, str]:
        """원본 텍스트 파싱 (딜리미터/코드블록이 없는 경우)"""
        # 딜리미터나 코드 블록이 없으면 전체를 코드로 간주
        if "@@@START_FILE" not in code and "```" not in code:
            lines = code.split('\n')
            # 불필요한 서술 제거
            code_lines = []
            for line in lines:
                stripped = line.strip()
                # 일반적인 코드 시작 패턴
                if stripped and not stripped.startswith(('Here', 'The', 'This', 'Fixed', 'Corrected')):
                    code_lines.append(line)
            if code_lines:
                return {'src/main.py': '\n'.join(code_lines)}
        return {}

    def _validate_syntax(self, code: str) -> bool:
        """파이썬 구문 검증"""
        try:
            compile(code, '<string>', 'exec')
            return True
        except SyntaxError:
            return False

    def fix_error(self, project_dir: str, test_result: TestResult, project_name: str) -> bool:
        """에러 수정 (다중 파싱 전략)"""
        error_file = 'src/main.py'

        # Try to infer filename from error message
        match = re.search(r"in ([\w\.]+):", test_result.error_message or "")
        if match:
            error_file = f"src/{match.group(1)}"

        error_file_path = Path(project_dir) / error_file

        # If inferred file doesn't exist, try finding *any* python file in src/
        if not error_file_path.exists():
             src_files = list((Path(project_dir) / 'src').glob('*.py'))
             if src_files:
                 error_file_path = src_files[0]
                 error_file = f"src/{error_file_path.name}"
             else:
                 logger.error(f"Error file not found: {error_file}")
                 return False

        with open(error_file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()

        error_message = f"Error Type: {test_result.error_type}\nError Message: {test_result.error_message}\nStderr: {test_result.stderr}"

        logger.info(f"Analyzing error in {error_file} with LLM...")

        try:
            fixed_code_raw = self.analyze_error_with_llm(error_message, source_code, project_name)

            # 다중 파싱 전략 시도
            parsers = [
                ("Custom Delimiters", lambda: self._parse_with_delimiters(fixed_code_raw, project_name)),
                ("Code Blocks", lambda: self._parse_with_code_blocks(fixed_code_raw, project_name)),
                ("Raw Text", lambda: self._parse_raw_text(fixed_code_raw, project_name)),
            ]

            new_content = None
            parsed_files = {}

            for parser_name, parser_func in parsers:
                try:
                    parsed_files = parser_func()
                    if parsed_files:
                        # 파일 찾기
                        if error_file in parsed_files:
                            new_content = parsed_files[error_file]
                        elif f"src/{error_file_path.name}" in parsed_files:
                            new_content = parsed_files[f"src/{error_file_path.name}"]
                        elif len(parsed_files) == 1:
                            new_content = list(parsed_files.values())[0]

                        # 구문 검증
                        if new_content and self._validate_syntax(new_content):
                            logger.info(f"✅ Successfully parsed using {parser_name} strategy")
                            break
                        else:
                            logger.debug(f"⚠️ {parser_name} parsing failed syntax validation")
                            new_content = None
                except Exception as e:
                    logger.debug(f"⚠️ {parser_name} parser failed: {e}")
                    continue

            if new_content:
                with open(error_file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                logger.info(f"✅ Fixed error in {error_file}")
                return True
            else:
                 logger.error("❌ All parsing strategies failed. LLM output:")
                 logger.error(f"First 500 chars: {fixed_code_raw[:500]}")
                 return False

        except Exception as e:
            logger.error(f"❌ Error fixing code: {str(e)}")
            return False

    def test_and_fix(self, project_dir: str, project_name: str, max_retries: int = None) -> Tuple[bool, TestResult, int]:
        """테스트 및 자가 수정 루프 실행"""
        if max_retries is None:
            max_retries = self.max_retries

        logger.info(f"Starting self-correction loop (Max retries: {max_retries})")

        for attempt in range(1, max_retries + 1):
            logger.info(f"Attempt {attempt}/{max_retries}:")

            # 1. Lint Check
            lint_result = self.run_lint_checks(project_dir)
            if not lint_result.passed:
                logger.warning(f"Lint check failed: {lint_result.error_message}")
                if not self.fix_error(project_dir, lint_result, project_name):
                    logger.error("Failed to fix lint error.")
                    return False, lint_result, attempt
                continue

            # 2. Unit Tests
            test_result = self.run_unit_tests(project_dir)
            if test_result.passed:
                logger.info("Tests passed!")
                return True, test_result, attempt
            else:
                logger.warning(f"Tests failed: {test_result.error_message}")
                if not self.fix_error(project_dir, test_result, project_name):
                    logger.error("Failed to fix test error.")
                    return False, test_result, attempt

        logger.error(f"Max retries exceeded ({max_retries})")
        final_result = self.run_unit_tests(project_dir)
        return False, final_result, max_retries

if __name__ == "__main__":
    pass