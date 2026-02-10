#!/usr/bin/env python3
"""
Builder Agent - Notion Planner

Notion Database를 사용하여 프로젝트를 관리합니다.

Usage:
    from modules.builder.planner_notion import NotionPlanner
    planner = NotionPlanner()
    project = planner.select_topic()
"""

import os
import requests
from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class NotionProject:
    """Notion 프로젝트 데이터 클래스"""
    id: str
    name: str
    description: str
    status: str
    deployed_url: Optional[str]
    created_at: str
    spec_content: Optional[str] = None  # 상세 스펙 내용


class NotionPlanner:
    """Notion Planner (Notion Database 관리)"""

    def __init__(self, api_key: str = None, database_id: str = None):
        """초기화"""
        # 환경 변수 로드 - OPENCLAW_ROOT 지원
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        # 환경 변수로 지정된 PROJECT_ROOT 사용 (우선)
        env_root = os.getenv("OPENCLAW_ROOT")
        if env_root:
            project_root = env_root

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

        # Notion API 설정
        if api_key is None:
            api_key = os.getenv("BUILDER_NOTION_TOKEN", "")

        if database_id is None:
            database_id = os.getenv("BUILDER_DATABASE_ID", "")

        if not api_key:
            raise ValueError("BUILDER_NOTION_TOKEN 환경변수가 설정되지 않았습니다.")

        if not database_id:
            raise ValueError("BUILDER_DATABASE_ID 환경변수가 설정되지 않았습니다.")

        self.api_key = api_key
        self.database_id = database_id
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }

        # 캐싱: 유효한 상태값 목록
        self._valid_statuses = None

    def _get_valid_statuses(self) -> List[str]:
        """Notion DB에서 유효한 상태값 목록 조회"""
        if self._valid_statuses is not None:
            return self._valid_statuses

        try:
            response = requests.get(
                f"{self.base_url}/databases/{self.database_id}",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            db_info = response.json()

            for prop_name, prop_data in db_info['properties'].items():
                if prop_data.get('type') == 'status':
                    self._valid_statuses = [
                        option['name']
                        for option in prop_data['status']['options']
                    ]
                    break

            if self._valid_statuses is None:
                # fallback
                self._valid_statuses = ['백로그', 'In Progress', '초안 작성중', '검토중', 'Failed', '게시 완료']
        except Exception as e:
            print(f"⚠️ 상태값 조회 실패, 기본값 사용: {e}")
            self._valid_statuses = ['백로그', 'In Progress', '초안 작성중', '검토중', 'Failed', '게시 완료']

        return self._valid_statuses

    def _make_request(self, method: str, url: str, data: Dict = None) -> Dict:
        """Notion API 요청"""
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data,
                timeout=20
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if response is not None:
                print(f"Server Response: {response.text}")
            raise Exception(f"Notion API 요청 실패: {str(e)}")

    def _parse_project(self, result: Dict) -> NotionProject:
        """API 결과를 NotionProject 객체로 파싱"""
        properties = result.get("properties", {})

        # 이름 (Title)
        name_prop = properties.get("내용", {})
        name = ""
        if name_prop.get("type") == "title":
            title = name_prop.get("title", [])
            if title:
                name = title[0].get("plain_text", "")

        # 도구 설명 (Rich Text) - 우선순위 1
        desc_prop = properties.get("도구 설명", {})
        description = ""
        if desc_prop.get("type") == "rich_text":
            rich_texts = desc_prop.get("rich_text", [])
            if rich_texts:
                description = "".join([t.get("plain_text", "") for t in rich_texts])

        # URL (URL) - 설명이 비었으면 사용 (우선순위 2)
        url_prop = properties.get("URL", {})
        url_value = ""
        if url_prop.get("type") == "url":
            url_value = url_prop.get("url", "")
        
        if not description and url_value:
            description = url_value

        # 상태 (Status)
        status_prop = properties.get("상태", {})
        status = "백로그"
        if status_prop.get("type") == "status":
            status_select = status_prop.get("status")
            if status_select:
                status = status_select.get("name", "백로그")

        return NotionProject(
            id=result["id"],
            name=name,
            description=description,
            status=status,
            deployed_url=url_value,
            created_at=result.get("created_time", "")
        )

    def get_all_projects(self) -> List[NotionProject]:
        """모든 프로젝트 조회"""
        url = f"{self.base_url}/databases/{self.database_id}/query"
        try:
            response = self._make_request("POST", url, data={
                "sorts": [{"property": "생성 일시", "direction": "descending"}]
            })
            return [self._parse_project(r) for r in response.get("results", [])]
        except Exception as e:
            print(f"❌ 프로젝트 조회 실패: {str(e)}")
            return []

    def get_incomplete_projects(self) -> List[NotionProject]:
        """미완료 프로젝트 조회"""
        url = f"{self.base_url}/databases/{self.database_id}/query"
        try:
            response = self._make_request("POST", url, data={
                "filter": {
                    "property": "상태",
                    "status": {"does_not_equal": "게시 완료"}
                },
                "sorts": [{"property": "생성 일시", "direction": "ascending"}]
            })
            return [self._parse_project(r) for r in response.get("results", [])]
        except Exception as e:
            print(f"❌ 미완료 프로젝트 조회 실패: {str(e)}")
            return []

    def select_topic(self, keywords: List[str] = None) -> Optional[NotionProject]:
        """최적의 주제 선택 (다차원 점수화 시스템)"""
        projects = self.get_incomplete_projects()
        if not projects:
            print("⚠️  미완료 프로젝트가 없습니다.")
            return None

        # 키워드 필터링
        if keywords:
            keywords_lower = [kw.lower() for kw in keywords]
            filtered = []
            for p in projects:
                for kw in keywords_lower:
                    if kw in p.name.lower() or kw in p.description.lower():
                        filtered.append(p)
                        break
            if filtered:
                projects = filtered
                print(f"🔍 키워드 필터링: {len(projects)}개 프로젝트")

        # 다차원 점수화
        scored_projects = []
        current_time = datetime.now()

        for p in projects:
            score = 0
            score_details = []

            # 1. 설명 상세함 (+10점)
            desc_score = min(len(p.description) / 50, 10)
            score += desc_score
            score_details.append(f"설명상세함: +{desc_score:.1f}")

            # 2. 대기 시간 가중치 (+20점)
            try:
                created_time = datetime.fromisoformat(p.created_at.replace('Z', '+00:00'))
                days_waiting = (current_time - created_time.replace(tzinfo=None)).days
                waiting_score = min(days_waiting, 20)
                score += waiting_score
                score_details.append(f"대기시간({days_waiting}일): +{waiting_score}")
            except Exception as e:
                score_details.append(f"대기시간: N/A")

            # 3. 키워드 매칭 (+30점) - 키워드가 제공된 경우
            if keywords:
                keywords_lower = [kw.lower() for kw in keywords]
                keyword_matches = sum(
                    1 for kw in keywords_lower
                    if kw in p.name.lower() or kw in p.description.lower()
                )
                keyword_score = min(keyword_matches * 10, 30)
                score += keyword_score
                score_details.append(f"키워드매칭: +{keyword_score}")

            # 4. 이름 길이 적정성 (+5점) - 너무 길거나 짧은 이름 패널티
            name_length = len(p.name)
            if 10 <= name_length <= 50:
                score += 5
                score_details.append("이름길이적정: +5")
            else:
                score_details.append(f"이름길이({name_length}): 0")

            scored_projects.append((score, p, score_details))

        # 점수순 정렬
        scored_projects.sort(key=lambda x: x[0], reverse=True)

        # 상위 3개 출력
        print(f"\n📊 프로젝트 점수 순위:")
        for i, (score, p, details) in enumerate(scored_projects[:3], 1):
            print(f"  {i}. {p.name} (총점: {score:.1f})")
            for detail in details:
                print(f"     - {detail}")

        selected = scored_projects[0][1]
        print(f"\n📋 최종 선택된 프로젝트: {selected.name}")
        return selected

    def update_project_status(self, page_id: str, status: str) -> bool:
        """상태 업데이트"""
        # 유효한 상태값 확인
        valid_statuses = self._get_valid_statuses()

        if status not in valid_statuses:
            print(f"⚠️ Warning: '{status}' is not a valid status.")
            print(f"   Valid statuses: {', '.join(valid_statuses)}")
            print(f"   Using '검토중' instead.")
            status = '검토중'

        url = f"{self.base_url}/pages/{page_id}"
        try:
            self._make_request("PATCH", url, data={
                "properties": {"상태": {"status": {"name": status}}}
            })
            print(f"✅ 상태 업데이트: {status}")
            return True
        except Exception as e:
            print(f"❌ 상태 업데이트 실패: {e}")
            return False

    def update_project_url(self, page_id: str, deployed_url: str) -> bool:
        """URL 업데이트"""
        url = f"{self.base_url}/pages/{page_id}"
        try:
            self._make_request("PATCH", url, data={
                "properties": {"URL": {"url": deployed_url}}
            })
            print(f"✅ URL 업데이트: {deployed_url}")
            return True
        except Exception:
            return False

    def _create_text_block(self, text: str) -> Dict:
        """텍스트를 Notion Block(Paragraph)으로 변환"""
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": text[:2000]}}]
            }
        }

    def append_spec_to_page(self, page_id: str, content: str):
        """페이지 본문에 스펙 문서(Markdown) 추가"""
        url = f"{self.base_url}/blocks/{page_id}/children"
        
        # 헤더 추가
        header_block = {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "📋 상세 요구사항 명세서 (Generated by Builder Agent)"}}]
            }
        }

        # 본문 분할 (2000자 제한 안전하게 처리)
        chunks = [content[i:i+1800] for i in range(0, len(content), 1800)]
        content_blocks = [self._create_text_block(chunk) for chunk in chunks]

        children = [header_block] + content_blocks
        
        try:
            self._make_request("PATCH", url, data={"children": children})
            print(f"✅ 스펙 문서 Notion 페이지에 추가 완료")
        except Exception as e:
            print(f"❌ 스펙 문서 추가 실패: {e}")

    # add_project, list_projects 등 기존 메서드 유지
    def add_project(self, name: str, description: str, status: str = '백로그') -> str:
        # 유효한 상태값 확인
        valid_statuses = self._get_valid_statuses()

        if status not in valid_statuses:
            print(f"⚠️ Warning: '{status}' is not a valid status.")
            print(f"   Valid statuses: {', '.join(valid_statuses)}")
            print(f"   Using '백로그' instead.")
            status = '백로그'

        url = f"{self.base_url}/pages"
        request_data = {
            "parent": {"database_id": self.database_id},
            "properties": {
                "내용": {"title": [{"text": {"content": name}}]},
                "도구 설명": {"rich_text": [{"text": {"content": description}}]},
                "상태": {"status": {"name": status}}
            }
        }
        resp = self._make_request("POST", url, data=request_data)
        return resp.get("id")

    def list_projects(self, status: str = None):
        projects = self.get_all_projects()
        if status:
            projects = [p for p in projects if p.status == status]
        for p in projects:
            print(f"- {p.name} ({p.status}): {p.description[:50]}...")