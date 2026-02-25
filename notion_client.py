#!/usr/bin/env python3
"""
Notion Client for Builder Agent v3
Manages project ideas and development status in Notion database
"""
import os
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import requests
from dotenv import load_dotenv

# Load environment
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))


@dataclass
class ProjectIdea:
    """Project idea model"""
    name: str
    description: str
    category: str
    tags: List[str]
    source_url: Optional[str] = None
    priority: str = "보통"
    project_type: str = "CLI"
    tech_stack: List[str] = None
    
    def __post_init__(self):
        if self.tech_stack is None:
            self.tech_stack = ["Python"]


class NotionClient:
    """Notion API client for Builder Agent"""
    
    # Status mapping (Builder → Notion)
    STATUS_MAP = {
        "아이디어": "아이디어",       # Newly discovered
        "검토 대기": "검토 대기",     # Waiting for review
        "개발 대기": "개발 대기",     # Approved, in queue
        "개발중": "개발중",           # In development
        "테스트중": "테스트중",       # Testing
        "배포 완료": "배포 완료",     # Published
        "개발 실패": "개발 실패",     # Failed
        "보류": "보류"                # Rejected/On hold
    }
    
    # Reverse mapping (Notion → Builder)
    REVERSE_STATUS_MAP = {
        "아이디어": "discovered",
        "검토 대기": "review_pending",
        "개발 대기": "in_queue",
        "개발중": "in_progress",
        "테스트중": "testing",
        "배포 완료": "completed",
        "개발 실패": "failed",
        "보류": "on_hold",
        # Legacy mappings (기존 호환성)
        "백로그": "in_queue",
        "In Progress": "in_progress",
        "검토중": "testing",
        "Failed": "failed",
        "게시 완료": "completed"
    }
    
    def __init__(self):
        self.token = os.getenv("BUILDER_NOTION_TOKEN")
        self.database_id = os.getenv("BUILDER_NOTION_DATABASE_ID")
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
    
    def _request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Make API request to Notion"""
        url = f"{self.base_url}/{endpoint}"
        response = requests.request(
            method=method,
            url=url,
            headers=self.headers,
            json=data,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    
    def add_idea(self, idea: ProjectIdea, detailed_spec: str = None) -> str:
        """Add a new project idea to Notion database
        
        Args:
            idea: ProjectIdea object
            detailed_spec: Detailed spec content for Notion body (markdown)
        
        Returns:
            Page ID of created entry
        """
        # 상세 스펙을 설명에 포함 (Notion 2000자 제한)
        full_description = idea.description
        if detailed_spec:
            # 마크다운에서 텍스트만 추출하여 설명에 추가
            spec_text = detailed_spec.replace('#', '').replace('*', '').replace('`', '')
            full_description = f"{idea.description}\n\n{spec_text}"[:1900]
        
        properties = {
            "내용": {
                "title": [{"text": {"content": idea.name}}]
            },
            "도구 설명": {
                "rich_text": [{"text": {"content": full_description}}]
            },
            "카테고리": {
                "select": {"name": idea.category}
            },
            "테그": {
                "multi_select": [{"name": tag} for tag in idea.tags[:5]]
            },
            "상태": {
                "status": {"name": "아이디어"}
            }
        }
        
        # URL 필드는 배포 완료 후 GitHub 저장소 주소용
        # 아이디어 발굴 시에는 URL을 입력하지 않음
        
        data = {
            "parent": {"database_id": self.database_id},
            "properties": properties
        }
        
        result = self._request("POST", "pages", data)
        page_id = result["id"]
        
        # 상세 스펙을 Notion 페이지 본문에 추가
        if detailed_spec:
            self._add_page_content(page_id, detailed_spec)
        
        return page_id
    
    def _add_page_content(self, page_id: str, content: str) -> bool:
        """Add content to Notion page body
        
        Args:
            page_id: Notion page ID
            content: Markdown content to add
        
        Returns:
            True if successful
        """
        # Notion API는 블록 단위로 콘텐츠 추가
        # 마크다운을 Notion 블록으로 변환
        blocks = self._markdown_to_blocks(content)
        
        if not blocks:
            return False
        
        try:
            # Notion API: POST /v1/blocks/{block_id}/children
            # block_id는 페이지 ID
            url = f"{self.base_url}/blocks/{page_id}/children"
            
            # 한 번에 최대 100개 블록까지 추가 가능
            for i in range(0, len(blocks), 100):
                chunk = blocks[i:i+100]
                response = requests.patch(
                    url,
                    headers=self.headers,
                    json={"children": chunk},
                    timeout=30
                )
                response.raise_for_status()
            return True
        except Exception as e:
            print(f"Error adding page content: {e}")
            return False
    
    def _markdown_to_blocks(self, markdown: str) -> List[Dict]:
        """Convert markdown to Notion blocks"""
        blocks = []
        lines = markdown.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # 빈 줄 건너뛰기
            if not line.strip():
                i += 1
                continue
            
            # 헤딩
            if line.startswith('## '):
                blocks.append({
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": line[3:]}}]
                    }
                })
            elif line.startswith('### '):
                blocks.append({
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [{"type": "text", "text": {"content": line[4:]}}]
                    }
                })
            # 코드 블록
            elif line.startswith('```'):
                code_lines = []
                i += 1
                while i < len(lines) and not lines[i].startswith('```'):
                    code_lines.append(lines[i])
                    i += 1
                code_content = '\n'.join(code_lines)
                # Notion 제한: 2000자
                if len(code_content) > 1900:
                    code_content = code_content[:1900] + "\n..."
                blocks.append({
                    "object": "block",
                    "type": "code",
                    "code": {
                        "rich_text": [{"type": "text", "text": {"content": code_content}}],
                        "language": "python" if "python" in line else "plain text"
                    }
                })
            # 테이블 (간단한 마크다운 테이블)
            elif '|' in line and line.startswith('|'):
                # 테이블 파싱 (단순화)
                table_rows = []
                while i < len(lines) and '|' in lines[i]:
                    row = [cell.strip() for cell in lines[i].split('|')[1:-1]]
                    if row and not all(c in '-|' for c in ''.join(row)):
                        table_rows.append(row)
                    i += 1
                i -= 1
                
                if table_rows:
                    blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": "📊 " + ' | '.join(table_rows[0]) if table_rows else ""}}]
                        }
                    })
            # 리스트
            elif line.startswith('- '):
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": line[2:]}}]
                    }
                })
            # 일반 텍스트
            else:
                if len(line) > 2000:
                    line = line[:2000]
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": line}}]
                    }
                })
            
            i += 1
        
        return blocks
    
    def get_pending_ideas(self, limit: int = 10) -> List[Dict]:
        """Get ideas waiting for review (상태 = 아이디어 or 검토 대기)"""
        data = {
            "filter": {
                "or": [
                    {"property": "상태", "status": {"equals": "아이디어"}},
                    {"property": "상태", "status": {"equals": "검토 대기"}},
                    # Legacy support
                    {"property": "상태", "status": {"equals": "백로그"}}
                ]
            },
            "sorts": [
                {"property": "생성 일시", "direction": "descending"}
            ],
            "page_size": limit
        }
        
        result = self._request("POST", f"databases/{self.database_id}/query", data)
        return result.get("results", [])
    
    def get_development_ready(self, limit: int = 10) -> List[Dict]:
        """Get multiple ideas ready for development (상태 = 개발 대기)
        
        Args:
            limit: Maximum number of ideas to return
            
        Returns:
            List of Notion pages ready for development, sorted by creation date
        """
        data = {
            "filter": {
                "property": "상태",
                "status": {"equals": "개발 대기"}
            },
            "sorts": [
                {"property": "생성 일시", "direction": "ascending"}
            ],
            "page_size": limit
        }
        
        result = self._request("POST", f"databases/{self.database_id}/query", data)
        return result.get("results", [])
    
    def get_development_queue(self) -> List[Dict]:
        """Get full development queue with priorities
        
        Returns:
            List of items in queue with their priorities
        """
        items = self.get_development_ready(limit=20)
        
        queue = []
        for i, page in enumerate(items, 1):
            idea = self.parse_page_to_idea(page)
            queue.append({
                "position": i,
                "page_id": page["id"],
                "name": idea.name,
                "category": idea.category,
                "tags": idea.tags,
                "description": idea.description[:100] + "..." if len(idea.description) > 100 else idea.description,
                "created_at": page.get("created_time", "Unknown")
            })
        
        return queue
    
    def update_status(self, page_id: str, status: str, github_url: str = None) -> bool:
        """Update project status
        
        Args:
            page_id: Notion page ID
            status: New status (발굴됨, 개발 대기, 개발중, 테스트중, 배포 완료, 실패)
            github_url: GitHub repository URL (optional)
        
        Returns:
            True if successful
        """
        notion_status = self.STATUS_MAP.get(status, status)
        
        # Status 필드는 name이 아닌 직접 상태 이름을 사용
        properties = {
            "상태": {
                "status": {"name": notion_status}
            }
        }
        
        if github_url:
            properties["URL"] = {"url": github_url}
        
        data = {"properties": properties}
        
        try:
            self._request("PATCH", f"pages/{page_id}", data)
            return True
        except Exception as e:
            print(f"Error updating status: {e}")
            return False
    
    def mark_development_started(self, page_id: str) -> bool:
        """Mark project as in development"""
        return self.update_status(page_id, "개발중")
    
    def mark_development_completed(self, page_id: str, github_url: str) -> bool:
        """Mark project as completed with GitHub URL"""
        return self.update_status(page_id, "배포 완료", github_url)
    
    def mark_development_failed(self, page_id: str, error: str = None) -> bool:
        """Mark project as failed"""
        return self.update_status(page_id, "실패")
    
    def parse_page_to_idea(self, page: Dict) -> ProjectIdea:
        """Parse Notion page to ProjectIdea"""
        props = page["properties"]
        
        # Get title
        title_prop = props.get("내용", {})
        name = ""
        if title_prop.get("title"):
            name = title_prop["title"][0]["text"]["content"]
        
        # Get description
        desc_prop = props.get("도구 설명", {})
        description = ""
        if desc_prop.get("rich_text"):
            description = desc_prop["rich_text"][0]["text"]["content"]
        
        # Get category (None-safe)
        cat_prop = props.get("카테고리", {})
        category = "기타"
        if cat_prop and cat_prop.get("select"):
            category = cat_prop["select"].get("name", "기타") or "기타"
        
        # Get tags
        tags_prop = props.get("테그", {})
        tags = [t["name"] for t in tags_prop.get("multi_select", [])] if tags_prop else []
        
        # Get URL
        url_prop = props.get("URL", {})
        source_url = url_prop.get("url") if url_prop else None
        
        return ProjectIdea(
            name=name,
            description=description,
            category=category,
            tags=tags,
            source_url=source_url
        )
    
    def add_discovered_ideas(self, ideas: List[ProjectIdea]) -> int:
        """Add multiple discovered ideas to Notion
        
        Returns:
            Number of ideas added
        """
        added = 0
        for idea in ideas:
            try:
                self.add_idea(idea)
                added += 1
                print(f"  ✅ Added: {idea.name}")
            except Exception as e:
                print(f"  ❌ Failed to add {idea.name}: {e}")
        return added


# Test
if __name__ == "__main__":
    client = NotionClient()
    
    # Test: Get pending ideas
    print("📋 Pending ideas:")
    pending = client.get_pending_ideas(limit=5)
    for page in pending:
        idea = client.parse_page_to_idea(page)
        print(f"  - {idea.name} ({idea.category})")
    
    print(f"\n📊 Total: {len(pending)} ideas pending")
