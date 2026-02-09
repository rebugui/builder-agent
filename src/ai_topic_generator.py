#!/usr/bin/env python3
"""
Builder Agent - AI Topic Generator

GLM-4.7을 사용하여 새로운 프로젝트 주제를 생성합니다.
"""

import os
import sys
import json
from typing import Dict, List

# 프로젝트 루트 경로 추가
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

# Builder Agent 자체 LLM 클라이언트 사용
from modules.builder.llm_client import GLMClient


class AITopicGenerator:
    """AI 주제 생성기"""

    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        """
        초기화

        Args:
            api_key: GLM API Key
            base_url: GLM API Base URL
            model: 사용할 모델
        """
        # 환경 변수 로드
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

        # API 설정
        if api_key is None:
            api_key = os.getenv("GLM_API_KEY", "")

        if base_url is None:
            base_url = os.getenv("GLM_BASE_URL", "https://api.z.ai/api/coding/paas/v4/")

        if model is None:
            model = os.getenv("GLM_MODEL", "glm-4.7")

        if not api_key:
            raise ValueError("GLM_API_KEY 환경변수가 설정되지 않았습니다.")

        self.api_key = api_key
        self.base_url = base_url
        self.model = model

        # GLM Client 초기화
        self.client = GLMClient(api_key, base_url, model)

    def generate_topic(self, category: str = None, count: int = 1) -> List[Dict]:
        """
        새로운 프로젝트 주제 생성

        Args:
            category: 카테고리 (devops, security, utility, all)
            count: 생성할 주제 개수

        Returns:
            생성된 주제 리스트
        """
        # 시스템 프롬프트
        system_prompt = """당신은 10년 이상 경력의 DevOps 엔지니어이자 보안 전문가입니다.
실무에서 바로 사용 가능한 유용한 프로젝트 주제를 제안해주세요.

## 주제 제안 가이드라인

### 1. 창의성
- 기존 도구의 개선이나 새로운 조합
- 실제 개발 현장의 pain point 해결
- automation 가능한 반복 작업

### 2. 실용성
- Python 3.11+로 구현 가능한 규모
- 오픈소스 라이브러리 활용 가능
- 1-2주 안에 MVP 개발 가능

### 3. 기술 요구사항
- 최신 기술 트렌드 반영 (Docker, K8s, CI/CD, 보안)
- 명확한 input/output 정의
- 테스트 가능한 기능 포함

## 출력 형식

반드시 JSON 배열 형식으로 출력해주세요:

```json
[
  {
    "name": "프로젝트 이름",
    "description": "2-3문장으로 된 프로젝트 설명",
    "category": "devops|security|utility",
    "features": ["기능1", "기능2", "기능3"],
    "tech_stack": ["기술1", "기술2"]
  }
]
```
"""

        # 사용자 프롬프트
        if category == "devops":
            category_desc = "DevOps/Docker/Kubernetes/CI/CD 관련 도구"
        elif category == "security":
            category_desc = "보안/취약점 스캔/보안 분석 도구"
        elif category == "utility":
            category_desc = "개발자 유틸리티/텍스트 처리/파일 변환 도구"
        else:
            category_desc = "DevOps, 보안, 유틸리티 전체"

        user_prompt = f"""새로운 프로젝트 주제 {count}개를 제안해주세요.

## 카테고리
{category_desc}

## 요구사항
- 실무에서 바로 사용 가능한 주제
- Python 3.11+로 구현 가능
- 1-2주 안에 MVP 개발 가능
- 창의적이고 실용적인 기능

## 주의사항
- 반드시 JSON 배열 형식으로만 출력
- JSON 외의 텍스트는 포함하지 마세요
- name, description, category, features, tech_stack 필드 필수

주제를 제안해주세요:"""

        try:
            # GLM 호출
            response = self.client.chat(
                system_prompt=system_prompt,
                user_prompt=user_prompt
            )

            # JSON 파싱
            topics = self._parse_json_response(response)

            return topics

        except Exception as e:
            print(f"❌ 주제 생성 실패: {e}")
            return []

    def _parse_json_response(self, response: str) -> List[Dict]:
        """
        GLM 응답에서 JSON 파싱

        Args:
            response: GLM 응답

        Returns:
            파싱된 주제 리스트
        """
        try:
            # markdown 코드블록 제거
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]

            response = response.strip()

            # JSON 파싱
            topics = json.loads(response)

            if not isinstance(topics, list):
                topics = [topics]

            return topics

        except json.JSONDecodeError as e:
            print(f"⚠️ JSON 파싱 실패: {e}")
            print(f"응답: {response[:500]}")

            # fallback: 수동 파싱 시도
            return self._fallback_parse(response)

    def _fallback_parse(self, response: str) -> List[Dict]:
        """
        JSON 파싱 실패 시 fallback 파싱

        Args:
            response: GLM 응답

        Returns:
            파싱된 주제 리스트
        """
        topics = []

        try:
            # 간단한 패턴 매칭
            import re

            # name 추출
            names = re.findall(r'"name":\s*"([^"]+)"', response)
            descriptions = re.findall(r'"description":\s*"([^"]+)"', response)
            categories = re.findall(r'"category":\s*"([^"]+)"', response)

            for i in range(min(len(names), len(descriptions))):
                topics.append({
                    "name": names[i],
                    "description": descriptions[i],
                    "category": categories[i] if i < len(categories) else "utility",
                    "features": [],
                    "tech_stack": ["Python"]
                })

        except Exception as e:
            print(f"⚠️ Fallback 파싱 실패: {e}")

        return topics


def main():
    """메인 함수"""
    print("=" * 80)
    print("🤖 AI 주제 생성기")
    print("=" * 80)
    print()

    # 카테고리 선택
    print("카테고리를 선택하세요:")
    print("  1. DevOps (Docker, K8s, CI/CD)")
    print("  2. Security (취약점, 스캐너)")
    print("  3. Utility (유틸리티, 변환기)")
    print("  4. 전체")

    choice = input("\n선택 (1-4): ").strip()

    category_map = {
        "1": "devops",
        "2": "security",
        "3": "utility",
        "4": None
    }

    category = category_map.get(choice)

    # 개수 입력
    count_input = input("생성할 주제 개수 (기본값: 3): ").strip()
    count = int(count_input) if count_input.isdigit() else 3

    print()
    print("🚀 GLM-4.7로 주제 생성 중...")
    print()

    # 주제 생성
    generator = AITopicGenerator()
    topics = generator.generate_topic(category=category, count=count)

    if not topics:
        print("❌ 주제 생성 실패")
        return

    # 결과 출력
    print("=" * 80)
    print(f"✅ {len(topics)}개 주제 생성 완료!")
    print("=" * 80)
    print()

    for i, topic in enumerate(topics, 1):
        print(f"📋 주제 {i}")
        print(f"   이름: {topic.get('name', 'N/A')}")
        print(f"   설명: {topic.get('description', 'N/A')}")
        print(f"   카테고리: {topic.get('category', 'N/A')}")
        print(f"   기능: {', '.join(topic.get('features', []))}")
        print(f"   기술 스택: {', '.join(topic.get('tech_stack', []))}")
        print()

    # 데이터베이스에 추가 여부 확인
    add_to_db = input("이 주제들을 데이터베이스에 추가하시겠습니까? (y/n): ").strip().lower()

    if add_to_db == 'y':
        from modules.builder.planner import TopicPlanner
        from modules.builder.planner_notion import NotionPlanner

        planner = TopicPlanner()

        for topic in topics:
            try:
                # SQLite에 추가
                project_id = planner.add_project(
                    name=topic['name'],
                    description=topic['description'],
                    status='Planning'
                )
                print(f"  ✅ SQLite: {topic['name']} (ID: {project_id})")

                # Notion에 추가 (선택)
                try:
                    notion = NotionPlanner()
                    page_id = notion.add_project(
                        name=topic['name'],
                        description=topic['description'],
                        status='백로그'
                    )
                    print(f"  ✅ Notion: {topic['name']} (Page ID: {page_id[:16]}...)")
                except Exception as e:
                    print(f"  ⚠️ Notion 추가 실패: {e}")

            except Exception as e:
                print(f"  ❌ 추가 실패: {topic.get('name', 'N/A')} - {e}")

        print()
        print("=" * 80)
        print("✅ 데이터베이스 추가 완료!")
        print("=" * 80)


if __name__ == "__main__":
    main()
