#!/usr/bin/env python3
"""
Builder Agent - Coding Agent 활용 예시

Usage:
    python3 builder_example.py
"""

# GLM API Client 활용 (기존 Intelligence Agent 스킬 사용)
# Intelligence Agent의 BlogWriter 모듈이 GLM API를 사용하고 있으므로, 이를 활용하여 코드 생성을 수행합니다.

from modules.intelligence.writer import GLMClient, BlogWriter

class BuilderAgent:
    """Builder Agent (DevOps 도구 자동 생성)"""

    def __init__(self, api_key: str, base_url: str, model: str):
        """
        초기화

        Args:
            api_key: GLM API Key
            base_url: GLM API Base URL
            model: GLM Model
        """
        self.client = GLMClient(api_key, base_url, model)
        self.model = model

    def generate_python_code(self, tool_name: str, description: str) -> str:
        """
        Python 코드 생성 (LLM 활용)

        Args:
            tool_name: 도구 이름 (예: "Docker Container Monitor")
            description: 도구 설명 (예: "도커 컨테이너의 리소스 사용량을 모니터링하는 도구입니다.")

        Returns:
            생성된 Python 코드
        """
        # 시스템 프롬프트 (DevOps Expert 페르소나)
        system_prompt = """당신은 10년 이상 경력을 가진 DevOps 엔지니어입니다.
Docker, Kubernetes, Helm, CI/CD 파이프라인에 깊은 지식을 보유하고 있습니다.

## 코드 작성 가이드라인

1. **구조화된 코드 작성**
   - `src/`: 핵 모듈
   - `tests/`: 단위 테스트
   - `docs/`: 문서화
   - `README.md`: 프로젝트 설명

2. **보안 코딩**
   - input validation (사용자 입력 검증)
   - `subprocess`, `eval`, `exec` 사용 제한
   - 에러 처리 (try-catch)

3. **문서화**
   - docstrings 작성 (함수 설명)
   - README 작성 (사용법, 요구사항)

## 출력 형식 (Markdown)

```python
# src/main.py
import subprocess
import socket

def scan_container(container_name):
    \"\"\"도커 컨테이너 리소스 스캔\"\"\"
    try:
        # 보안 코딩: subprocess 사용
        result = subprocess.check_output(
            ['docker', 'stats', '--no-stream', container_name],
            timeout=10
        )
        return result.decode('utf-8')
    except subprocess.TimeoutExpired:
        return "Timeout"
    except Exception as e:
        return f"Error: {str(e)}"
```

## 요구사항

1. 도구 이름: {tool_name}
2. 설명: {description}
3. 언어: Python 3.11+
4. 라이브러리: subprocess, socket (기본 라이브러리 사용)
"""

        # 사용자 프롬프트
        user_prompt = f"""다음 DevOps 도구의 Python 코드를 작성해주세요.

=== 도구 정보 ===
도구 이름: {tool_name}
설명: {description}
언어: Python 3.11+
라이브러리: subprocess, socket (기본 라이브러리만 사용)

=== 요구사항 ===
1. 구조화된 코드 작성
   - `src/`: 핵 모듈
   - `tests/`: 단위 테스트
   - `docs/`: 문서화
   - `README.md`: 프로젝트 설명

2. 보안 코딩
   - input validation (사용자 입력 검증)
   - `subprocess`, `eval`, `exec` 사용 제한
   - 에러 처리 (try-catch)

3. 문서화
   - docstrings 작성 (함수 설명)
   - README 작성 (사용법, 요구사항)

=== 출력 형식 (Markdown) ===
1. 전체 코드 파일 구조 (폴더 포함)
2. 각 파일의 내용
   - src/main.py
   - tests/test_main.py
   - docs/DESIGN.md
   - README.md

모든 코드를 Markdown으로 작성해주세요.
"""

        # GLM 호출
        generated_code = self.client.chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )

        return generated_code

    def parse_generated_code(self, generated_code: str, tool_name: str) -> dict:
        """
        생성된 코드를 파싱하여 파일별로 분리

        Args:
            generated_code: 생성된 코드
            tool_name: 도구 이름 (kebab-case로 변환)

        Returns:
            파일별 분리된 코드 딕셔너리
        """
        # 간단한 파싱 로직 (백틱(````)로 구분)
        files = {}
        current_file = None
        content = []

        lines = generated_code.split('\n')

        for line in lines:
            # 파일 시작 감지
            if line.strip().startswith('# ') or line.strip().startswith('```'):
                # 이전 파일 내용 저장
                if current_file and content:
                    files[current_file] = '\n'.join(content).strip()

                # 새 파일 감지
                if 'main.py' in line:
                    current_file = 'src/main.py'
                    content = []
                elif 'test_main.py' in line:
                    current_file = 'tests/test_main.py'
                elif 'DESIGN.md' in line:
                    current_file = 'docs/DESIGN.md'
                elif 'README.md' in line:
                    current_file = 'README.md'
            else:
                # 코드 내용 추가
                content.append(line)

        # 마지막 파일 내용 저장
        if current_file and content:
            files[current_file] = '\n'.join(content).strip()

        return files

def main():
    """메인 함수"""
    print("=" * 60)
    print("🚀 Builder Agent - Coding Agent 활용 예시")
    print("=" * 60)
    print()

    # Builder Agent 인스턴스 생성 (GLM API 활용)
    from dotenv import load_dotenv
    load_dotenv()

    import os

    api_key = os.getenv("GLM_API_KEY")
    base_url = "https://api.z.ai/api/coding/paas/v4/"
    model = "glm-4.7"

    builder = BuilderAgent(api_key, base_url, model)

    # Python 코드 생성
    tool_name = "Docker Container Monitor"
    description = "도커 컨테이너의 리소스 사용량을 모니터링하는 도구입니다."

    print(f"📋 도구: {tool_name}")
    print(f"📝 설명: {description}")
    print()
    print("🚀 GLM-4.7을 사용하여 Python 코드 생성 중...")
    print()

    generated_code = builder.generate_python_code(tool_name, description)

    print("✅ Python 코드 생성 완료!")
    print()
    print("=" * 60)
    print("📋 생성된 코드:")
    print("=" * 60)
    print(generated_code)
    print()

    # 코드 파싱
    print("=" * 60)
    print("🔄 코드 파싱 중...")
    print("=" * 60)
    print()

    tool_name_kebab = tool_name.lower().replace(' ', '-')

    files = builder.parse_generated_code(generated_code, tool_name_kebab)

    print("✅ 코드 파싱 완료!")
    print()
    print("=" * 60)
    print("📋 생성된 파일 구조:")
    print("=" * 60)
    print()

    for filename, content in files.items():
        print(f"📄 {filename}")
        print(f"---")
        print(content[:200] + ("..." if len(content) > 200 else ""))
        print()

    print("=" * 60)
    print("✅ Builder Agent 완료!")
    print("=" * 60)

if __name__ == "__main__":
    main()
