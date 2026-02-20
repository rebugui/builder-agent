"""
Builder Agent v2.0 - 개선된 프롬프트

2단계 코드 생성:
1. 소스 코드 생성
2. 구조 분석 기반 테스트 코드 생성
"""


class PromptsV2:
    """개선된 프롬프트 클래스"""
    
    DEVOPS_EXPERT_SYSTEM = '''당신은 10년 이상의 경력을 가진 DevOps 엔지니어입니다.
Docker, Kubernetes, Helm, CI/CD 파이프라인에 깊은 지식을 보유하고 있습니다.

## 📘 코딩 가이드라인

### 1. 구조화된 코드 작성
- `src/`: 핵심 모듈 (main logic)
- `tests/`: 단위 테스트
- `docs/`: 문서화

### 2. 모듈화
- 기능별로 분리 (scanner, parser, analyzer, reporter)
- 각 모듈은 독립적으로 테스트 가능해야 함
- `src/main.py`: 진입점

### 3. 보안 코딩
- 입력 검증 필수
- subprocess, eval, exec 사용 제한
- 에러 처리 철저히

### 4. 출력 형식 (Custom Delimiters)

@@@START_FILE:파일경로@@@
파일내용
@@@END_FILE@@@
'''

    @staticmethod
    def get_source_code_prompt(tool_name: str, description: str) -> str:
        """소스 코드 생성 프롬프트 (1단계)"""
        return f'''다음 DevOps 도구의 **소스 코드만** 작성해주세요. 테스트 코드는 작성하지 마세요.

=== 도구 정보 ===
도구 이름: {tool_name}
설명: {description}

=== 작업 요구사항 ===

1. **프로젝트 구조** (소스만):
   - `src/__init__.py`: (비어 있음)
   - `src/main.py`: 메인 진입점
   - `src/core.py`: 핵심 기능 구현
   - 필요시 추가 모듈: `src/utils.py`, `src/models.py` 등

2. **기능 구현**:
   - 설명에 맞는 기능을 완벽하게 구현
   - `python3 -m src.main`으로 실행 가능해야 함
   - 모든 함수와 클래스에 docstring 작성

3. **모듈 구조**:
   - `main.py`는 진입점만 담당 (argument parsing, main 호출)
   - `core.py`는 핵심 로직 구현
   - 필요한 경우 추가 모듈 생성

4. **보안 코딩**:
   - Input validation 필수
   - Error handling 필수

=== 출력 형식 (필수) ===

반드시 아래 형식을 준수하세요. 테스트 코드는 포함하지 마세요.

@@@START_FILE:src/__init__.py@@@
@@@END_FILE@@@

@@@START_FILE:src/main.py@@@
"""메인 진입점"""
import argparse
from .core import main

def cli():
    parser = argparse.ArgumentParser(...)
    # ...

if __name__ == "__main__":
    cli()
@@@END_FILE@@@

@@@START_FILE:src/core.py@@@
"""핵심 기능 구현"""

def process_data(data):
    """데이터 처리"""
    # ...
@@@END_FILE@@@

@@@START_FILE:requirements.txt@@@
pytest>=7.0.0
requests>=2.28.0
@@@END_FILE@@@

@@@START_FILE:docs/README.md@@@
# {tool_name}
## 설치
## 사용법
@@@END_FILE@@@

소스 코드만 작성해주세요!
'''

    @staticmethod
    def get_test_code_prompt(tool_name: str, source_structure: dict) -> str:
        """테스트 코드 생성 프롬프트 (2단계) - 소스 구조 기반"""
        
        # 소스 구조를 텍스트로 변환
        structure_text = ""
        for module, info in source_structure.items():
            structure_text += f"\n### {module}\n"
            if info.get('classes'):
                structure_text += "클래스:\n"
                for cls in info['classes']:
                    structure_text += f"  - {cls['name']}: {cls.get('docstring', '설명 없음')}\n"
                    if cls.get('methods'):
                        for method in cls['methods']:
                            structure_text += f"    - {method['name']}({', '.join(method.get('args', []))})\n"
            if info.get('functions'):
                structure_text += "함수:\n"
                for func in info['functions']:
                    structure_text += f"  - {func['name']}({', '.join(func.get('args', []))}): {func.get('docstring', '')[:50]}\n"
        
        return f'''다음 소스 코드 구조를 기반으로 **테스트 코드만** 작성해주세요.

=== 도구 정보 ===
도구 이름: {tool_name}

=== 소스 코드 구조 ===
{structure_text}

=== 작업 요구사항 ===

1. **테스트 파일 구조**:
   - `tests/__init__.py`: (비어 있음)
   - `tests/test_core.py`: core.py의 단위 테스트
   - 필요시 추가: `tests/test_utils.py`

2. **중요 - Import 경로**:
   - 반드시 실제 소스 구조와 일치해야 함
   - `from src.core import ...` 형식 사용
   - `from src.utils import ...` 형식 사용
   - 존재하지 않는 모듈은 import하지 마세요!

3. **테스트 작성 가이드**:
   - pytest 사용
   - 각 함수/클래스 메서드에 대한 테스트 작성
   - 정상 케이스 + 예외 케이스 모두 포함
   - mock 사용 최소화 (실제 동작 테스트)

=== 출력 형식 (필수) ===

@@@START_FILE:tests/__init__.py@@@
@@@END_FILE@@@

@@@START_FILE:tests/test_core.py@@@
"""core.py 단위 테스트"""
import pytest
from src.core import process_data, main

class TestProcessData:
    def test_process_data_valid_input(self):
        # 정상 입력 테스트
        pass
    
    def test_process_data_invalid_input(self):
        # 예외 입력 테스트
        pass
@@@END_FILE@@@

테스트 코드만 작성해주세요! Import 경로가 정확한지 확인하세요!
'''

    @staticmethod
    def get_code_generation_prompt(tool_name: str, description: str) -> str:
        """기존 호환성 유지를 위한 메서드"""
        return PromptsV2.get_source_code_prompt(tool_name, description)
