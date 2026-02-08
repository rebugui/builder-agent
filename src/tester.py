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
                if 'SyntaxError' in result.stderr: error_type = 'SyntaxError'
                elif 'IndentationError' in result.stderr: error_type = 'IndentationError'
                elif 'ModuleNotFoundError' in result.stderr: error_type = 'ModuleNotFoundError'
                elif 'AttributeError' in result.stderr: error_type = 'AttributeError'
                elif 'NameError' in result.stderr: error_type = 'NameError'
                elif 'AssertionError' in result.stderr: error_type = 'AssertionError'
                elif 'Exception' in result.stderr: error_type = 'Exception'

                stderr_lines = result.stderr.split('\n')
                for line in stderr_lines:
                    if 'Error:' in line or 'ERROR ' in line:
                        error_message = line.strip()
                        break

                if not error_message and result.stderr:
                    error_message = result.stderr.strip()[:200]

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

    def fix_error(self, project_dir: str, test_result: TestResult, project_name: str) -> bool:
        """에러 수정"""
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
            
            # Parse fixed code using new regex parser
            parsed_files = self.coder.parse_generated_code(fixed_code_raw, project_name)
            
            # If parse returns files, use the one matching error_file or fallback
            new_content = None
            if error_file in parsed_files:
                new_content = parsed_files[error_file]
            elif f"src/{error_file_path.name}" in parsed_files:
                new_content = parsed_files[f"src/{error_file_path.name}"]
            elif len(parsed_files) == 1:
                new_content = list(parsed_files.values())[0]
            
            # Fallback for legacy format if regex fails (though unlikely with prompt)
            if not new_content and not parsed_files:
                lines = fixed_code_raw.split('\n')
                code_lines = []
                in_block = False
                for line in lines:
                    if line.strip().startswith('```'):
                        in_block = not in_block
                        continue
                    if in_block:
                        code_lines.append(line)
                if code_lines:
                     new_content = '\n'.join(code_lines)
                else:
                     # Just assume raw text if no blocks
                     if "@@@START_FILE" not in fixed_code_raw:
                         new_content = fixed_code_raw

            if new_content:
                with open(error_file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                logger.info(f"Fixed error in {error_file}")
                return True
            else:
                 logger.error("Failed to parse fixed code.")
                 return False

        except Exception as e:
            logger.error(f"Error fixing code: {str(e)}")
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