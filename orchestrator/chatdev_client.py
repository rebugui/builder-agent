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
        self.timeout = 14400  # 4 hours (long-running development)
    
    def health_check(self) -> bool:
        """서버 상태 확인"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.json().get("status") == "healthy"
        except:
            return False
    
    def get_active_sessions(self) -> int:
        """
        현재 실행 중인 활성 세션 수 확인
        
        Returns:
            int: 활성 세션 수 (0 이상)
        """
        try:
            # ChatDev 서버의 로그 파일에서 활성 세션 파악
            # 또는 WebSocket으로 상태 요청
            import subprocess
            
            # 로그 파일에서 running 상태 세션 수 계산
            log_file = "/Users/nabang/Documents/OpenClaw/logs/chatdev_server.log"
            
            if not os.path.exists(log_file):
                return 0
            
            # grep으로 직접 세션 상태 로그 추출 (더 정확함)
            result = subprocess.run(
                ["grep", "-E", "status to (running|completed)|Session.*cleaned", log_file],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            log_content = result.stdout
            
            # running 세션 수 계산
            import re
            
            # "Updated session xxx status to running" 찾기
            running_sessions = set()
            completed_sessions = set()
            
            for line in log_content.split('\n'):
                # running 상태
                match = re.search(r'Updated session ([a-f0-9-]+) status to running', line)
                if match:
                    running_sessions.add(match.group(1))
                
                # completed 상태
                match = re.search(r'Updated session ([a-f0-9-]+) status to completed', line)
                if match:
                    completed_sessions.add(match.group(1))
                
                # cleaned 상태
                match = re.search(r'Session ([a-f0-9-]+) cleaned', line)
                if match:
                    completed_sessions.add(match.group(1))
            
            # 활성 세션 = running - completed
            active = running_sessions - completed_sessions
            return len(active)
            
        except Exception as e:
            print(f"   [WARN] 활성 세션 확인 실패: {e}")
            return 0
    
    def wait_for_available_slot(self, max_wait: int = 300, check_interval: int = 30) -> bool:
        """
        사용 가능한 슬롯이 생길 때까지 대기
        
        Args:
            max_wait: 최대 대기 시간 (초)
            check_interval: 확인 간격 (초)
            
        Returns:
            bool: 슬롯 확보 성공 여부
        """
        waited = 0
        
        while waited < max_wait:
            active = self.get_active_sessions()
            
            if active == 0:
                return True
            
            print(f"   ⏳ 활성 세션 {active}개 대기 중... ({waited}초)")
            time.sleep(check_interval)
            waited += check_interval
        
        print(f"   ⚠️ 최대 대기 시간 초과 ({max_wait}초)")
        return False
    
    async def develop_project(self, idea: ProjectIdea) -> DevelopmentResult:
        """
        ChatDev 2.0을 사용하여 프로젝트 개발 (WebSocket 방식)
        
        Args:
            idea: 프로젝트 아이디어
            
        Returns:
            DevelopmentResult: 개발 결과
        """
        start_time = time.time()
        
        try:
            # WebSocket으로 직접 ChatDev 서버에 연결
            import websockets
            
            uri = f"{self.base_url.replace('http://', 'ws://')}/ws"
            
            async with websockets.connect(uri, ping_interval=20, ping_timeout=60) as ws:
                # 1. 연결 대기
                response = await asyncio.wait_for(ws.recv(), timeout=10)
                data = json.loads(response)
                session_id = data.get("data", {}).get("session_id")
                
                if not session_id:
                    raise Exception("Failed to get session ID")
                
                # 2. 워크플로우 시작 (상세 스펙 활용)
                task_prompt = idea.get_detailed_prompt()
                
                workflow_request = {
                    "type": "start_workflow",
                    "data": {
                        "yaml_file": "ChatDev_v1.yaml",
                        "task_prompt": task_prompt,
                        "log_level": "info"
                    }
                }
                
                await ws.send(json.dumps(workflow_request))
                
                # 3. 실행 모니터링
                files = []
                agent_count = 0
                token_usage = {}
                
                while True:
                    try:
                        response = await asyncio.wait_for(ws.recv(), timeout=self.timeout)
                        data = json.loads(response)
                        msg_type = data.get("type", "unknown")
                        
                        if msg_type == "workflow_started":
                            pass  # 진행 중
                            
                        elif msg_type == "agent_message":
                            agent_count += 1
                            agent = data.get("data", {}).get("agent", "unknown")
                            
                        elif msg_type == "workflow_completed":
                            results = data.get("data", {}).get("results", {})
                            code_files = data.get("data", {}).get("code_files", [])
                            token_usage = data.get("data", {}).get("token_usage", {})
                            files = code_files
                            break
                            
                        elif msg_type == "workflow_cancelled":
                            raise Exception("Workflow cancelled")
                            
                        elif msg_type == "error":
                            error_msg = data.get("data", {}).get("message", "Unknown error")
                            raise Exception(error_msg)
                            
                    except asyncio.TimeoutError:
                        raise Exception("Workflow timeout")
            
            execution_time = time.time() - start_time
            
            return DevelopmentResult(
                idea=idea,
                success=True,
                files=files,
                execution_time=execution_time,
                token_usage=token_usage
            )
            
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
                "COMMON_PROMPT": f"""
You are a helpful AI assistant working at ChatDev.
Always provide detailed, accurate responses.
When writing code, ensure it is complete and functional.
Output in the requested format without extra explanations.

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
                "start": ["ceo"],
                "nodes": self._create_nodes(idea),
                "edges": [
                    {"from": "ceo", "to": "cto"},
                    {"from": "cto", "to": "programmer"},
                    {"from": "programmer", "to": "reviewer"},
                    {"from": "reviewer", "to": "tester"},
                    {"from": "tester", "to": "cto_final"}
                ]
            }
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
    
    def _sanitize_filename(self, name: str) -> str:
        """파일명을 안전하게 변환 (공백, 특수문자 제거)"""
        import re
        # 공백과 특수문자를 언더스코어로 변환
        safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
        # 연속된 언더스코어 제거
        safe_name = re.sub(r'_+', '_', safe_name)
        # 앞뒤 언더스코어 제거
        safe_name = safe_name.strip('_').lower()
        return safe_name or 'project'
    
    async def _start_session(self, workflow: Dict[str, Any], idea: ProjectIdea) -> str:
        """개발 세션 시작"""
        # 파일명 안전하게 변환
        safe_name = self._sanitize_filename(idea.name)
        
        async with aiohttp.ClientSession() as session:
            # 워크플로우 파일 업로드
            workflow_data = {
                "filename": f"builder_{safe_name}.yaml",
                "content": json.dumps(workflow, indent=2)
            }
            
            async with session.post(
                f"{self.base_url}/api/workflows/upload/content",
                json=workflow_data,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status != 200:
                    raise Exception(f"Failed to upload workflow: {await response.text()}")
            
            # 세션 ID 생성 (타임스탬프 기반)
            import uuid
            session_id = f"builder_{safe_name}_{int(time.time())}_{uuid.uuid4().hex[:8]}"
            
            # 워크플로우 실행
            execute_data = {
                "session_id": session_id,
                "yaml_file": f"builder_{safe_name}.yaml",
                "task_prompt": idea.description
            }
            
            async with session.post(
                f"{self.base_url}/api/workflow/execute",
                json=execute_data,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status != 200:
                    raise Exception(f"Failed to execute workflow: {await response.text()}")
                
                result = await response.json()
                return session_id
    
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
