"""
ChatDev 2.0 Client - ChatDev 2.0 API 연동
"""
import os
import json
import time
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import requests
import aiohttp

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.idea import ProjectIdea, DevelopmentResult


class ChatDevClient:
    """ChatDev 2.0 API 클라이언트"""
    
    def __init__(self, base_url: str = "http://localhost:6400"):
        self.base_url = base_url
        self.glm_base_url = os.getenv("BASE_URL", "https://api.z.ai/api/coding/paas/v4")
        self.glm_api_key = os.getenv("API_KEY")
        self.timeout = 600  # 10 minutes
    
    def health_check(self) -> bool:
        """서버 상태 확인"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.json().get("status") == "healthy"
        except:
            return False
    
    async def develop_project(self, idea: ProjectIdea) -> DevelopmentResult:
        """
        ChatDev 2.0을 사용하여 프로젝트 개발
        
        Args:
            idea: 프로젝트 아이디어
            
        Returns:
            DevelopmentResult: 개발 결과
        """
        start_time = time.time()
        
        try:
            # 1. 워크플로우 생성
            workflow = self._create_workflow(idea)
            
            # 2. 세션 시작
            session_id = await self._start_session(workflow, idea)
            
            # 3. 실행 및 모니터링
            result = await self._monitor_and_collect(session_id, idea)
            
            result.execution_time = time.time() - start_time
            return result
            
        except Exception as e:
            return DevelopmentResult(
                idea=idea,
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    def _create_workflow(self, idea: ProjectIdea) -> Dict[str, Any]:
        """프로젝트에 맞는 워크플로우 생성"""
        # 기본 워크플로우 템플릿
        workflow = {
            "version": "0.4.0",
            "vars": {
                "PROJECT_NAME": idea.name,
                "PROJECT_DESC": idea.description,
                "REQUIREMENTS": "\n".join(f"- {req}" for req in idea.requirements),
                "TECH_STACK": ", ".join(idea.technical_stack),
                "COMMON_PROMPT": f"""
Project: {idea.name}
Description: {idea.description}

Requirements:
{chr(10).join('- ' + req for req in idea.requirements)}

Technical Stack: {', '.join(idea.technical_stack)}
Difficulty: {idea.difficulty}

You are developing a {idea.project_type.value} for the Builder Agent v3 system.
Generate clean, well-documented, production-ready code.
                """
            },
            "graph": {
                "id": f"builder_{idea.name}",
                "description": f"Development workflow for {idea.name}",
                "is_majority_voting": False,
                "start": ["ceo"]
            },
            "nodes": self._create_nodes(idea),
            "edges": [
                {"from": "ceo", "to": "cto"},
                {"from": "cto", "to": "programmer"},
                {"from": "programmer", "to": "reviewer"},
                {"from": "reviewer", "to": "tester"},
                {"from": "tester", "to": "cto_final"}
            ]
        }
        
        return workflow
    
    def _create_nodes(self, idea: ProjectIdea) -> List[Dict[str, Any]]:
        """워크플로우 노드 생성"""
        nodes = [
            {
                "id": "ceo",
                "type": "agent",
                "config": {
                    "provider": "openai",
                    "base_url": "${BASE_URL}",
                    "api_key": "${API_KEY}",
                    "name": "glm-5",
                    "role": "${COMMON_PROMPT}\n\nYou are CEO. Analyze requirements and define project scope.\n\nOutput format:\n<INFO>\nPROJECT_SCOPE: [scope]\nKEY_FEATURES:\n- [feature 1]\n- [feature 2]\nDELIVERABLES:\n- [file1.py]\n- [file2.py]\n</INFO>",
                    "params": {"temperature": 0.7, "max_tokens": 2000}
                }
            },
            {
                "id": "cto",
                "type": "agent",
                "config": {
                    "provider": "openai",
                    "base_url": "${BASE_URL}",
                    "api_key": "${API_KEY}",
                    "name": "glm-5",
                    "role": "${COMMON_PROMPT}\n\nYou are CTO. Design technical architecture.\n\nOutput format:\n<INFO>\nARCHITECTURE:\n- [component 1]: [description]\n- [component 2]: [description]\nMODULES:\n- [module1.py]: [purpose]\n- [module2.py]: [purpose]\n</INFO>",
                    "params": {"temperature": 0.7, "max_tokens": 2000}
                }
            },
            {
                "id": "programmer",
                "type": "agent",
                "config": {
                    "provider": "openai",
                    "base_url": "${BASE_URL}",
                    "api_key": "${API_KEY}",
                    "name": "glm-5",
                    "role": "${COMMON_PROMPT}\n\nYou are a Senior Programmer. Write complete, functional Python code.\n\nRequirements:\n1. Implement all features\n2. Include docstrings\n3. Handle errors properly\n4. Follow PEP 8\n\nOutput ONLY Python code, no explanations.",
                    "params": {"temperature": 0.7, "max_tokens": 4000}
                }
            },
            {
                "id": "reviewer",
                "type": "agent",
                "config": {
                    "provider": "openai",
                    "base_url": "${BASE_URL}",
                    "api_key": "${API_KEY}",
                    "name": "glm-5",
                    "role": "${COMMON_PROMPT}\n\nYou are Code Reviewer. Review code for quality and correctness.\n\nOutput format:\n<INFO>\nREVIEW_STATUS: [APPROVED/NEEDS_REVISION]\nISSUES:\n- [issue 1]\nSUGGESTIONS:\n- [suggestion 1]\n</INFO>\n\nIf APPROVED, output: <INFO> FINISHED </INFO>",
                    "params": {"temperature": 0.7, "max_tokens": 2000}
                }
            },
            {
                "id": "tester",
                "type": "agent",
                "config": {
                    "provider": "openai",
                    "base_url": "${BASE_URL}",
                    "api_key": "${API_KEY}",
                    "name": "glm-5",
                    "role": "${COMMON_PROMPT}\n\nYou are Test Engineer. Write pytest unit tests.\n\nRequirements:\n1. Cover all public methods\n2. Include edge cases\n3. Use fixtures\n4. High coverage\n\nOutput ONLY pytest code.",
                    "params": {"temperature": 0.7, "max_tokens": 3000}
                }
            },
            {
                "id": "cto_final",
                "type": "agent",
                "config": {
                    "provider": "openai",
                    "base_url": "${BASE_URL}",
                    "api_key": "${API_KEY}",
                    "name": "glm-5",
                    "role": "${COMMON_PROMPT}\n\nYou are CTO doing final review. Verify and summarize.\n\nOutput:\n<INFO>\nPROJECT_SUMMARY:\nNAME: [Project Name]\nFILES:\n- [filename]: [Purpose]\nSTATUS: COMPLETE\n</INFO>",
                    "params": {"temperature": 0.7, "max_tokens": 2000}
                }
            }
        ]
        
        return nodes
    
    async def _start_session(self, workflow: Dict[str, Any], idea: ProjectIdea) -> str:
        """개발 세션 시작"""
        async with aiohttp.ClientSession() as session:
            # 워크플로우 파일 업로드
            workflow_data = {
                "name": f"builder_{idea.name}.yaml",
                "content": json.dumps(workflow, indent=2)
            }
            
            async with session.post(
                f"{self.base_url}/api/workflows/upload",
                json=workflow_data,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status != 200:
                    raise Exception(f"Failed to upload workflow: {await response.text()}")
            
            # 세션 시작
            session_data = {
                "workflow": f"builder_{idea.name}.yaml",
                "task": idea.description
            }
            
            async with session.post(
                f"{self.base_url}/api/sessions",
                json=session_data,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                result = await response.json()
                return result["session_id"]
    
    async def _monitor_and_collect(self, session_id: str, idea: ProjectIdea) -> DevelopmentResult:
        """세션 모니터링 및 결과 수집"""
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            while time.time() - start_time < self.timeout:
                # 상태 확인
                async with session.get(
                    f"{self.base_url}/api/sessions/{session_id}",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    status_data = await response.json()
                    status = status_data.get("status")
                    
                    if status == "completed":
                        # 결과 수집
                        return await self._collect_results(session_id, idea, status_data)
                    elif status == "failed":
                        error = status_data.get("error", "Unknown error")
                        return DevelopmentResult(
                            idea=idea,
                            success=False,
                            error=error
                        )
                    
                    # 대기
                    await asyncio.sleep(10)
            
            # 타임아웃
            return DevelopmentResult(
                idea=idea,
                success=False,
                error="Development timeout"
            )
    
    async def _collect_results(self, session_id: str, idea: ProjectIdea, status_data: Dict) -> DevelopmentResult:
        """개발 결과 수집"""
        async with aiohttp.ClientSession() as session:
            # 생성된 파일 목록 조회
            async with session.get(
                f"{self.base_url}/api/sessions/{session_id}/files",
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                files_data = await response.json()
                
                files = {}
                for file_info in files_data.get("files", []):
                    file_name = file_info["name"]
                    file_content = file_info.get("content", "")
                    files[file_name] = file_content
                
                return DevelopmentResult(
                    idea=idea,
                    success=True,
                    files=files,
                    review_comments=status_data.get("review_comments"),
                    documentation=status_data.get("documentation")
                )


if __name__ == "__main__":
    # 테스트
    async def test():
        from ..models.idea import ProjectIdea, IdeaSource, ProjectType, Priority
        
        client = ChatDevClient()
        
        if not client.health_check():
            print("❌ ChatDev 2.0 server is not running")
            return
        
        print("✅ ChatDev 2.0 server is healthy")
        
        # 테스트 아이디어
        idea = ProjectIdea(
            name="test-calculator",
            description="A simple calculator with add and subtract",
            source=IdeaSource.MANUAL,
            project_type=ProjectType.CLI_APP,
            priority=Priority.MEDIUM,
            requirements=["Add function", "Subtract function"],
            technical_stack=["Python"]
        )
        
        result = await client.develop_project(idea)
        print(f"Success: {result.success}")
        print(f"Files: {list(result.files.keys())}")
    
    asyncio.run(test())
