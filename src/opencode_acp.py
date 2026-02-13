#!/usr/bin/env python3
"""
OpenCode ACP (Agent Client Protocol) Client

OpenCode의 ACP 서버와 통신하여 에이전트 기능을 사용합니다.
"""

import asyncio
import json
import logging
import subprocess
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from pathlib import Path
from enum import Enum

import httpx

logger = logging.getLogger(__name__)


class ACPMessageType(Enum):
    TASK = "task"
    RESPONSE = "response"
    ERROR = "error"
    STATUS = "status"
    HEARTBEAT = "heartbeat"


@dataclass
class ACPTask:
    task_id: str
    prompt: str
    agent: str = "build"
    model: str = "zai-coding-plan/glm-5"
    context: Optional[Dict] = None


@dataclass
class ACPResponse:
    task_id: str
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    files: Optional[Dict[str, str]] = None


class OpenCodeACPServer:
    """
    OpenCode ACP 서버 관리
    
    ACP 서버를 시작하고 관리합니다.
    """
    
    def __init__(
        self,
        port: int = 4097,
        project_path: str = None,
        auto_start: bool = False
    ):
        self.port = port
        self.project_path = project_path or str(Path.cwd())
        self.process: Optional[subprocess.Popen] = None
        self.base_url = f"http://localhost:{port}"
        self.client = httpx.AsyncClient(timeout=300.0)
        
        if auto_start:
            self.start()
    
    def start(self) -> bool:
        if self.is_running():
            logger.info(f"ACP 서버 이미 실행 중: {self.base_url}")
            return True
        
        cmd = [
            "opencode", "acp",
            "--port", str(self.port),
            "--cwd", self.project_path
        ]
        
        logger.info(f"ACP 서버 시작: port={self.port}")
        
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        for _ in range(10):
            time.sleep(0.5)
            if self.is_running():
                logger.info(f"✅ ACP 서버 시작 완료: {self.base_url}")
                return True
        
        logger.error("ACP 서버 시작 실패")
        return False
    
    def stop(self):
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=5)
            self.process = None
            logger.info("ACP 서버 중지")
    
    def is_running(self) -> bool:
        try:
            response = httpx.get(f"{self.base_url}/health", timeout=2.0)
            return response.status_code == 200
        except:
            return False
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


class OpenCodeACPClient:
    """
    OpenCode ACP 클라이언트
    
    ACP 서버와 통신하여 작업을 실행합니다.
    """
    
    def __init__(
        self,
        server: OpenCodeACPServer = None,
        port: int = 4097,
        model: str = "zai-coding-plan/glm-5"
    ):
        self.server = server or OpenCodeACPServer(port=port)
        self.model = model
        self.client = httpx.AsyncClient(timeout=300.0)
        self.task_callbacks: Dict[str, Callable] = {}
    
    async def connect(self) -> bool:
        if not self.server.is_running():
            if not self.server.start():
                return False
        
        for _ in range(5):
            if self.server.is_running():
                return True
            await asyncio.sleep(0.5)
        
        return False
    
    async def submit_task(self, task: ACPTask) -> str:
        if not await self.connect():
            raise ConnectionError("ACP 서버에 연결할 수 없습니다.")
        
        payload = {
            "type": "task",
            "task_id": task.task_id,
            "prompt": task.prompt,
            "agent": task.agent,
            "model": task.model or self.model,
            "context": task.context or {}
        }
        
        response = await self.client.post(
            f"{self.server.base_url}/task",
            json=payload
        )
        
        if response.status_code != 200:
            raise Exception(f"작업 제출 실패: {response.text}")
        
        return task.task_id
    
    async def get_response(self, task_id: str, timeout: float = 300.0) -> ACPResponse:
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = await self.client.get(
                    f"{self.server.base_url}/response/{task_id}"
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return ACPResponse(
                        task_id=task_id,
                        success=data.get("success", False),
                        output=data.get("output"),
                        error=data.get("error"),
                        files=data.get("files")
                    )
                
                elif response.status_code == 202:
                    await asyncio.sleep(1.0)
                    continue
                
                else:
                    return ACPResponse(
                        task_id=task_id,
                        success=False,
                        error=f"응답 조회 실패: {response.status_code}"
                    )
                    
            except Exception as e:
                logger.error(f"응답 조회 중 에러: {e}")
                await asyncio.sleep(1.0)
        
        return ACPResponse(
            task_id=task_id,
            success=False,
            error=f"Timeout after {timeout} seconds"
        )
    
    async def execute(
        self,
        prompt: str,
        agent: str = "build",
        task_id: str = None,
        timeout: float = 300.0
    ) -> ACPResponse:
        import uuid
        
        task = ACPTask(
            task_id=task_id or str(uuid.uuid4()),
            prompt=prompt,
            agent=agent,
            model=self.model
        )
        
        await self.submit_task(task)
        return await self.get_response(task.task_id, timeout)
    
    async def generate_code(
        self,
        project_name: str,
        description: str
    ) -> ACPResponse:
        prompt = f"""
다음 DevOps 도구의 Python 코드를 작성해주세요.

프로젝트 이름: {project_name}
설명: {description}

필요한 파일:
- src/__init__.py
- src/main.py
- src/core.py
- tests/__init__.py
- tests/test_main.py
- docs/README.md
- requirements.txt

각 파일은 @@@START_FILE:경로@@@ 와 @@@END_FILE@@@ 사이에 작성해주세요.
"""
        
        return await self.execute(prompt, agent="build")
    
    async def review_code(self, code: str) -> ACPResponse:
        prompt = f"""
다음 코드를 리뷰하고 개선점을 제안해주세요:

```python
{code}
```

평가 항목:
- 보안 (Security)
- 성능 (Performance)
- 가독성 (Readability)
- 테스트 가능성 (Testability)

JSON 형식으로 결과를 반환해주세요.
"""
        
        return await self.execute(prompt, agent="build", timeout=120.0)
    
    async def close(self):
        await self.client.aclose()


class OpenCodeServeClient:
    """
    OpenCode Serve 모드 클라이언트
    
    OpenCode serve 명령으로 시작된 서버와 통신합니다.
    """
    
    def __init__(
        self,
        port: int = 4096,
        model: str = "zai-coding-plan/glm-5"
    ):
        self.port = port
        self.base_url = f"http://localhost:{port}"
        self.model = model
        self.client = httpx.AsyncClient(timeout=300.0)
        self.process: Optional[subprocess.Popen] = None
    
    def start_server(self) -> bool:
        if self.is_running():
            return True
        
        cmd = [
            "opencode", "serve",
            "--port", str(self.port)
        ]
        
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        for _ in range(10):
            time.sleep(0.5)
            if self.is_running():
                return True
        
        return False
    
    def is_running(self) -> bool:
        try:
            response = httpx.get(f"{self.base_url}/health", timeout=2.0)
            return response.status_code == 200
        except:
            return False
    
    def stop_server(self):
        if self.process:
            self.process.terminate()
            self.process = None
    
    async def chat(
        self,
        message: str,
        session_id: str = None
    ) -> Dict:
        payload = {
            "message": message,
            "model": self.model
        }
        
        if session_id:
            payload["session_id"] = session_id
        
        response = await self.client.post(
            f"{self.base_url}/chat",
            json=payload
        )
        
        return response.json()
    
    async def close(self):
        await self.client.aclose()
        self.stop_server()


def create_acp_client(
    port: int = 4097,
    model: str = "zai-coding-plan/glm-5",
    auto_start: bool = True
) -> OpenCodeACPClient:
    server = OpenCodeACPServer(port=port, auto_start=auto_start)
    return OpenCodeACPClient(server=server, model=model)


async def test_acp_connection():
    print("🧪 ACP 연결 테스트")
    
    client = create_acp_client()
    
    try:
        connected = await client.connect()
        print(f"1. 연결 상태: {'✅ 성공' if connected else '❌ 실패'}")
        
        if connected:
            response = await client.execute(
                "간단한 Python 함수 하나 작성해줘.",
                agent="build",
                timeout=60.0
            )
            
            print(f"2. 작업 결과: {'✅ 성공' if response.success else '❌ 실패'}")
            if response.output:
                print(f"   출력 길이: {len(response.output)}자")
            if response.error:
                print(f"   에러: {response.error}")
    
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_acp_connection())
