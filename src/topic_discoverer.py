#!/usr/bin/env python3
"""
Builder Agent - Topic Discoverer

외부 소스(GitHub, CVE, News)에서 DevOps/보안 주제를 자동으로 발견하고
데이터베이스에 추가합니다.

Usage:
    python3 modules/builder/topic_discoverer.py --source github --count 5
    python3 modules/builder/topic_discoverer.py --source cve --count 3
    python3 modules/builder/topic_discoverer.py --source all
"""

import os
import sys
import json
import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta

# GLM Client 임포트
try:
    from modules.intelligence.writer import GLMClient
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from modules.intelligence.writer import GLMClient

# Planner 임포트 (Notion)
from planner_notion import NotionPlanner


class TopicDiscoverer:
    """Topic Discoverer (주제 자동 발견)**

    외부 소스에서 DevOps/보안 주제를 자동으로 발견합니다.
    """

    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        """
        초기화

        Args:
            api_key: GLM API Key
            base_url: GLM API Base URL
            model: GLM Model
        """
        # 환경 변수 로드
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

        # GLM Client 초기화
        if api_key is None:
            api_key = os.getenv("GLM_API_KEY", "")

        if base_url is None:
            base_url = os.getenv("GLM_BASE_URL", "https://api.z.ai/api/coding/paas/v4/")

        if model is None:
            model = os.getenv("GLM_MODEL", "glm-4.7")

        if not api_key:
            raise ValueError("GLM_API_KEY 환경변수가 설정되지 않았습니다.")

        self.client = GLMClient(api_key, base_url, model)

        # Planner 초기화 (Notion)
        self.planner = NotionPlanner()

        # 시스템 프롬프트
        self.system_prompt = """당신은 DevOps 및 보안 도구 주제 발견 전문가입니다.

## 📘 역할

보안 뉴스, 취약점 데이터, GitHub 트렌딩 등을 분석하여
실제로 구현 가능하고 유용한 DevOps 도구 주제를 추천합니다.

## 📋 주제 추천 기준

1. **유용성 (Usefulness)**
   - 실제 보안 문제 해결에 도움이 되는 도구
   - DevOps 엔지니어가 실제로 사용할 도구

2. **구현 가능성 (Implementability)**
   - Python으로 구현 가능한 도구
   - 최신 기술 스택 활용 (Docker, Kubernetes, CI/CD)

3. **관련성 (Relevance)**
   - 최신 보안 동향 반영
   - 취약점 대응에 유용한 도구

## 📝 출력 형식 (JSON)

주제를 JSON 형식으로 출력해주세요:

```json
[
  {
    "name": "도구 이름",
    "description": "상세한 설명 (20자 이상)"
  }
]
```

## 🚨 상태 옵션 (Notion Database)

Notion Database에 있는 상태 옵션만 사용해주세요:
- **백로그**: 초기 상태
- **초안 작성중**: 코드 생성 중
- **구현 중**: 코드 구현 및 테스트 중
- **검토중**: 사용자 검토 중
- **검토 완료**: 사용자 검토 완료
- **배포 완료**: 배포 완료
- **게시 완료**: 게시 완료

**주의사항:**
- 최소 3개, 최대 5개 주제 추천
- 도구 이름은 구체적이고 명확하게
- 설명은 상세하게 작성
- 중복 주제 피하기
- 이미 존재하는 도구와 유사한 것 피하기
"""

    def discover_from_github_trending(self, count: int = 5) -> List[Dict[str, str]]:
        """
        GitHub Trending에서 주제 발견

        Args:
            count: 찾을 주제 수

        Returns:
            주제 리스트 [{"name": "...", "description": "..."}]
        """
        print("🔍 GitHub Trending에서 주제 발견 중...")
        print()

        # GitHub Trending API (GitHub Search API 활용)
        # DevOps/Security 관련 키워드로 검색
        keywords = [
            "docker",
            "kubernetes",
            "security",
            "vulnerability",
            "devops",
            "cicd"
        ]

        repositories = []

        # 각 키워드로 검색
        for keyword in keywords[:3]:  # 최대 3개 키워드
            try:
                # GitHub Search API
                url = "https://api.github.com/search/repositories"
                params = {
                    "q": f"{keyword} language:python stars:>100",
                    "sort": "stars",
                    "order": "desc",
                    "per_page": 5
                }

                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    for repo in data.get("items", []):
                        repositories.append({
                            "name": repo["name"],
                            "description": repo["description"],
                            "url": repo["html_url"],
                            "stars": repo["stargazers_count"],
                            "language": repo["language"]
                        })
            except Exception as e:
                print(f"  ⚠️  GitHub 검색 실패: {str(e)}")
                continue

        # 인기 저장소 필터링
        if not repositories:
            print("  ⚠️  GitHub Trending 데이터를 가져올 수 없습니다.")
            return []

        # 상위 저장소 선택
        repositories.sort(key=lambda x: x["stars"], reverse=True)
        top_repos = repositories[:10]

        print(f"  ✅ {len(top_repos)}개 인기 저장소 발견")
        for repo in top_repos[:5]:
            print(f"     - {repo['name']} ({repo['stars']}★)")
        print()

        # LLM을 사용하여 주제 변환
        return self._convert_to_topics_with_llm(top_repos, count)

    def discover_from_cve(self, count: int = 5) -> List[Dict[str, str]]:
        """
        CVE 데이터베이스에서 주제 발견

        Args:
            count: 찾을 주제 수

        Returns:
            주제 리스트 [{"name": "...", "description": "..."}]
        """
        print("🔍 CVE 데이터베이스에서 주제 발견 중...")
        print()

        # NVD (National Vulnerability Database) API
        # 최신 CVE 조회
        try:
            # NIST NVD API v2.0
            url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
            params = {
                "resultsPerPage": 20,
                "lastModStartDate": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%dT00:00:00.000"),
                "lastModEndDate": datetime.now().strftime("%Y-%m-%dT23:59:59.999")
            }

            response = requests.get(url, params=params, timeout=30)

            if response.status_code != 200:
                print(f"  ⚠️  NVD API 요청 실패: {response.status_code}")
                return []

            data = response.json()
            cves = data.get("vulnerabilities", [])[:10]

            print(f"  ✅ {len(cves)}개 최신 CVE 발견")
            for cve in cves[:5]:
                cve_id = cve.get("cve", {}).get("id", "Unknown")
                description = cve.get("cve", {}).get("descriptions", [{}])[0].get("value", "")
                print(f"     - {cve_id}: {description[:80]}...")
            print()

            # LLM을 사용하여 주제 변환
            return self._convert_cves_to_topics(cves, count)

        except Exception as e:
            print(f"  ⚠️  CVE 조회 실패: {str(e)}")
            print()
            return []

    def discover_from_security_news(self, count: int = 5) -> List[Dict[str, str]]:
        """
        보안 뉴스에서 주제 발견

        Args:
            count: 찾을 주제 수

        Returns:
            주제 리스트 [{"name": "...", "description": "..."}]
        """
        print("🔍 보안 뉴스에서 주제 발견 중...")
        print()

        # Google News RSS (보안 뉴스)
        rss_urls = [
            "https://news.google.com/rss/search?q=vulnerability&hl=ko&gl=KR&ceid=KR:ko",
            "https://news.google.com/rss/search?q=security&hl=ko&gl=KR&ceid=KR:ko",
            "https://news.google.com/rss?q=docker+kubernetes&hl=en&gl=US&ceid=US:en"
        ]

        articles = []

        for rss_url in rss_urls:
            try:
                response = requests.get(rss_url, timeout=10)
                if response.status_code == 200:
                    # RSS 파싱 (간단한 파싱)
                    import xml.etree.ElementTree as ET

                    root = ET.fromstring(response.text)
                    items = root.findall(".//item")

                    for item in items[:3]:  # 각 RSS에서 3개만
                        title = item.find("title").text if item.find("title") is not None else ""
                        description = item.find("description").text if item.find("description") is not None else ""
                        link = item.find("link").text if item.find("link") is not None else ""

                        articles.append({
                            "title": title,
                            "description": description,
                            "link": link
                        })
            except Exception as e:
                print(f"  ⚠️  RSS 파싱 실패: {str(e)}")
                continue

        if not articles:
            print("  ⚠️  보안 뉴스 데이터를 가져올 수 없습니다.")
            return []

        print(f"  ✅ {len(articles)}개 보안 뉴스 발견")
        for article in articles[:5]:
            print(f"     - {article['title'][:60]}...")
        print()

        # LLM을 사용하여 주제 변환
        return self._convert_news_to_topics(articles, count)

    def _convert_to_topics_with_llm(self, repositories: List[Dict], count: int) -> List[Dict[str, str]]:
        """
        GitHub 저장소를 주제로 변환 (LLM 활용)

        Args:
            repositories: 저장소 리스트
            count: 찾을 주제 수

        Returns:
            주제 리스트
        """
        # 인기 저장소 정보 추출
        repo_info = "\n".join([
            f"- {repo['name']}: {repo['description'][:100]} ({repo['stars']}★)"
            for repo in repositories
        ])

        # LLM 프롬프트 생성
        user_prompt = f"""다음 GitHub 인기 저장소를 참고하여 DevOps/보안 도구 주제를 추천해주세요.

=== 인기 저장소 ===
{repo_info}

=== 주제 추천 요구사항 ===

1. 기존 저장소와 유사하지 않은 새로운 주제
2. Docker, Kubernetes, Security, DevOps 관련
3. Python으로 구현 가능한 도구
4. 취약점 대응/보안 강화에 유용한 도구

=== 출력 형식 (JSON) ===

{count}개 주제를 JSON 형식으로 출력해주세요:

```json
[
  {{
    "name": "도구 이름",
    "description": "상세한 설명 (20자 이상)"
  }}
]
```

---

JSON만 출력해주세요. 설명은 필요 없습니다.
"""

        # LLM 호출
        response = self.client.chat(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt
        )

        # JSON 파싱
        return self._parse_json_response(response)

    def _convert_cves_to_topics(self, cves: List[Dict], count: int) -> List[Dict[str, str]]:
        """
        CVE를 주제로 변환 (LLM 활용)

        Args:
            cves: CVE 리스트
            count: 찾을 주제 수

        Returns:
            주제 리스트
        """
        # CVE 정보 추출
        cve_info = "\n".join([
            f"- {cve.get('cve', {}).get('id', 'Unknown')}: {cve.get('cve', {}).get('descriptions', [{}])[0].get('value', '')[:150]}"
            for cve in cves
        ])

        # LLM 프롬프트 생성
        user_prompt = f"""다음 최신 취약점(CVE)을 참고하여 DevOps/보안 도구 주제를 추천해주세요.

=== 최신 CVE ===
{cve_info}

=== 주제 추천 요구사항 ===

1. 해당 CVE 대응/탐지에 유용한 도구
2. Docker, Kubernetes, Security, DevOps 관련
3. Python으로 구현 가능한 도구
4. 취약점 스캐너, 감사 도구, 모니터링 도구

=== 출력 형식 (JSON) ===

{count}개 주제를 JSON 형식으로 출력해주세요:

```json
[
  {{
    "name": "도구 이름",
    "description": "상세한 설명 (20자 이상)"
  }}
]
```

---

JSON만 출력해주세요. 설명은 필요 없습니다.
"""

        # LLM 호출
        response = self.client.chat(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt
        )

        # JSON 파싱
        return self._parse_json_response(response)

    def _convert_news_to_topics(self, articles: List[Dict], count: int) -> List[Dict[str, str]]:
        """
        보안 뉴스를 주제로 변환 (LLM 활용)

        Args:
            articles: 뉴스 기사 리스트
            count: 찾을 주제 수

        Returns:
            주제 리스트
        """
        # 뉴스 정보 추출
        news_info = "\n".join([
            f"- {article['title'][:100]}: {article['description'][:150]}"
            for article in articles
        ])

        # LLM 프롬프트 생성
        user_prompt = f"""다음 보안 뉴스를 참고하여 DevOps/보안 도구 주제를 추천해주세요.

=== 보안 뉴스 ===
{news_info}

=== 주제 추천 요구사항 ===

1. 뉴스와 관련된 도구 주제
2. Docker, Kubernetes, Security, DevOps 관련
3. Python으로 구현 가능한 도구
4. 최신 보안 동향 반영

=== 출력 형식 (JSON) ===

{count}개 주제를 JSON 형식으로 출력해주세요:

```json
[
  {{
    "name": "도구 이름",
    "description": "상세한 설명 (20자 이상)"
  }}
]
```

---

JSON만 출력해주세요. 설명은 필요 없습니다.
"""

        # LLM 호출
        response = self.client.chat(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt
        )

        # JSON 파싱
        return self._parse_json_response(response)

    def _parse_json_response(self, response: str) -> List[Dict[str, str]]:
        """
        LLM 응답에서 JSON 파싱

        Args:
            response: LLM 응답

        Returns:
            주제 리스트
        """
        # JSON 코드블록 추출
        import re

        # ```json ... ``` 패턴 찾기
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)

        if json_match:
            json_str = json_match.group(1)
        else:
            # 코드블록이 없으면 전체에서 JSON 찾기
            json_str = response

        try:
            topics = json.loads(json_str)

            # 주제 리스트 검증
            if not isinstance(topics, list):
                print("  ⚠️  JSON 형식 오류: 리스트가 아님")
                return []

            validated_topics = []
            for topic in topics:
                if isinstance(topic, dict) and "name" in topic and "description" in topic:
                    validated_topics.append({
                        "name": topic["name"],
                        "description": topic["description"]
                    })

            return validated_topics

        except json.JSONDecodeError as e:
            print(f"  ⚠️  JSON 파싱 실패: {str(e)}")
            print(f"  응답: {response[:200]}")
            return []

    def add_topics_to_database(self, topics: List[Dict[str, str]]) -> int:
        """
        주제를 데이터베이스에 추가

        Args:
            topics: 주제 리스트

        Returns:
            추가된 주제 수
        """
        added_count = 0

        for topic in topics:
            try:
                # 이미 존재하는 프로젝트 확인
                existing_projects = self.planner.get_all_projects()
                existing_names = [p.name.lower() for p in existing_projects]

                # 중복 체크
                if topic["name"].lower() in existing_names:
                    print(f"  ⏭️  중복된 주제 무시: {topic['name']}")
                    continue

                # 데이터베이스에 추가
                self.planner.add_project(
                    name=topic["name"],
                    description=topic["description"],
                    status="Planning"
                )
                added_count += 1
                print(f"  ✅ 주제 추가: {topic['name']}")

            except Exception as e:
                print(f"  ❌ 주제 추가 실패 ({topic['name']}): {str(e)}")
                continue

        return added_count

    def discover_and_add(self, source: str = "all", count: int = 5) -> int:
        """
        주제 발견 및 데이터베이스 추가

        Args:
            source: 데이터 소스 (github, cve, news, all)
            count: 찾을 주제 수

        Returns:
            추가된 주제 수
        """
        print("=" * 80)
        print("🔍 Topic Discoverer - 자동 주제 발견")
        print("=" * 80)
        print()

        total_added = 0

        if source == "github" or source == "all":
            print("📂 GitHub Trending")
            print("-" * 80)
            topics = self.discover_from_github_trending(count)
            added = self.add_topics_to_database(topics)
            total_added += added
            print()

        if source == "cve" or source == "all":
            print("🛡️  CVE Database")
            print("-" * 80)
            topics = self.discover_from_cve(count)
            added = self.add_topics_to_database(topics)
            total_added += added
            print()

        if source == "news" or source == "all":
            print("📰 Security News")
            print("-" * 80)
            topics = self.discover_from_security_news(count)
            added = self.add_topics_to_database(topics)
            total_added += added
            print()

        print("=" * 80)
        print(f"✅ 총 {total_added}개 주제 추가 완료!")
        print("=" * 80)

        return total_added


def main():
    """메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(description="Topic Discoverer - 자동 주제 발견")
    parser.add_argument(
        '--source',
        choices=['github', 'cve', 'news', 'all'],
        default='all',
        help='데이터 소스'
    )
    parser.add_argument(
        '--count',
        type=int,
        default=5,
        help='찾을 주제 수'
    )

    args = parser.parse_args()

    # Topic Discoverer 인스턴스 생성
    discoverer = TopicDiscoverer()

    # 주제 발견 및 추가
    discoverer.discover_and_add(source=args.source, count=args.count)


if __name__ == "__main__":
    main()
