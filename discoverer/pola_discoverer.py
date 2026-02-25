#!/usr/bin/env python3
"""
Pola Discoverer v2 - 폴라(Planner Agent) 주도 아이디어 발굴
GLM-5를 사용하여 상세 스펙 작성 (고도화 버전)
"""
import os
import json
import random
import time
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
import requests
from dotenv import load_dotenv

# Load environment
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))


class PolaDiscoverer:
    """폴라(Planner Agent) 주도 아이디어 발굴기 v2"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.glm_base_url = os.getenv("BASE_URL", "https://api.z.ai/api/coding/paas/v4")
        self.glm_api_key = os.getenv("API_KEY")
        self.github_token = os.getenv("GITHUB_TOKEN")
        
        # 기본 스펙 템플릿
        self.default_spec = {
            "estimated_time": "3-5시간",
            "difficulty": "medium",
            "category": "CLI",
            "tags": ["Python", "CLI", "Security"],
            "file_structure": [],
            "api_design": {"cli_commands": [], "functions": [], "data_models": []},
            "security_considerations": [],
            "testing_strategy": {"unit_tests": "pytest", "coverage_target": "80%"},
            "documentation": {"readme_sections": ["설치", "사용법", "API"], "docstrings": "Google 스타일"},
            "error_handling": [],
            "acceptance_criteria": [],
            "future_enhancements": []
        }
        
    def discover_with_spec(self, limit: int = 3) -> List[Dict[str, Any]]:
        """
        소스 수집 → 폴라 분석 → 상세 스펙 작성
        """
        print("🔍 Step 1: 소스 수집 중...")
        
        # 1. 소스 수집
        sources = self._collect_sources()
        print(f"   수집된 소스: {len(sources)}개")
        
        # 2. 폴라 분석 - 가장 유망한 프로젝트 선별
        print("\n💡 Step 2: 폴라 분석 중 (GLM-5)...")
        ideas = []
        
        for i in range(min(limit * 2, len(sources))):  # 여유 있게 시도
            source = sources[i]
            print(f"   분석 중: {source['name'][:40]}...")
            
            # GLM-5로 상세 스펙 작성 (재시도 로직)
            spec = self._generate_detailed_spec_v2(source)
            
            if spec and self._validate_spec(spec):
                ideas.append({
                    "name": spec.get("project_name", source["name"]),
                    "description": spec.get("description", ""),
                    "source_url": source.get("url"),
                    "category": spec.get("category", "CLI"),
                    "tags": spec.get("tags", ["Python"]),
                    "detailed_spec": spec
                })
                print(f"   ✅ 스펙 작성 완료: {spec.get('project_name', 'Unknown')}")
                
                if len(ideas) >= limit:
                    break
            else:
                print(f"   ⚠️ 스펙 검증 실패, 건너뜀")
        
        return ideas
    
    def _collect_sources(self) -> List[Dict[str, Any]]:
        """다양한 소스에서 프로젝트 아이디어 수집"""
        sources = []
        
        # 1. GitHub Trending
        try:
            github_sources = self._github_trending()
            sources.extend(github_sources)
        except Exception as e:
            print(f"   [WARN] GitHub Trending 실패: {e}")
        
        # 2. Security News 기반 아이디어
        security_ideas = self._security_based_ideas()
        sources.extend(security_ideas)
        
        # 3. predefined ideas (fallback)
        predefined = self._predefined_ideas()
        sources.extend(predefined)
        
        # 섞기
        random.shuffle(sources)
        
        return sources[:15]
    
    def _github_trending(self) -> List[Dict[str, Any]]:
        """GitHub Trending에서 프로젝트 수집"""
        sources = []
        
        headers = {}
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"
        
        # Python security 관련 저장소 검색
        url = "https://api.github.com/search/repositories"
        queries = [
            "language:python security stars:>50 pushed:>2024-06-01",
            "language:python cli tool stars:>100 pushed:>2024-01-01",
            "language:python scanner stars:>30 pushed:>2024-06-01"
        ]
        
        for query in queries:
            try:
                params = {
                    "q": query,
                    "sort": "stars",
                    "order": "desc",
                    "per_page": 3
                }
                response = requests.get(url, headers=headers, params=params, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    for item in data.get("items", []):
                        sources.append({
                            "name": item["name"],
                            "description": item.get("description", ""),
                            "url": item["html_url"],
                            "stars": item["stargazers_count"],
                            "language": item.get("language", "Python"),
                            "source": "github_trending"
                        })
            except Exception as e:
                print(f"   GitHub 검색 에러: {e}")
        
        return sources
    
    def _security_based_ideas(self) -> List[Dict[str, Any]]:
        """보안 트렌드 기반 아이디어"""
        ideas = [
            {
                "name": "secrets-leak-scanner",
                "description": "Git 저장소에서 실수로 커밋된 API 키, 토큰, 비밀번호 스캔",
                "url": None,
                "source": "security_trend"
            },
            {
                "name": "sbom-generator",
                "description": "프로젝트 의존성에서 SBOM(Software Bill of Materials) 생성",
                "url": None,
                "source": "security_trend"
            },
            {
                "name": "container-vuln-scanner",
                "description": "Docker 이미지의 알려진 취약점 스캔 및 보고서 생성",
                "url": None,
                "source": "security_trend"
            },
            {
                "name": "api-security-tester",
                "description": "REST API 엔드포인트 보안 테스트 자동화",
                "url": None,
                "source": "security_trend"
            },
            {
                "name": "log-anomaly-detector",
                "description": "로그 파일에서 이상 패턴 자동 감지",
                "url": None,
                "source": "security_trend"
            }
        ]
        return ideas
    
    def _predefined_ideas(self) -> List[Dict[str, Any]]:
        """사전 정의된 아이디어 풀"""
        ideas = [
            {
                "name": "k8s-security-auditor",
                "description": "Kubernetes 클러스터 보안 설정 감사",
                "url": None,
                "source": "devops_need"
            },
            {
                "name": "terraform-security-checker",
                "description": "Terraform 코드의 보안 문제점 정적 분석",
                "url": None,
                "source": "devops_need"
            },
            {
                "name": "certificate-monitor",
                "description": "SSL/TLS 인증서 만료 모니터링 및 알림",
                "url": None,
                "source": "devops_need"
            }
        ]
        return ideas
    
    def _generate_detailed_spec_v2(self, source: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """GLM-5를 사용하여 상세 스펙 작성 (v2 - 단계별 생성)"""
        
        # Step 1: 기본 정보 생성
        basic_spec = self._generate_basic_spec(source)
        if not basic_spec:
            return None
        
        # Step 2: 상세 설계 생성
        detailed_spec = self._generate_detailed_design(source, basic_spec)
        if not detailed_spec:
            return basic_spec  # 기본이라도 반환
        
        # 병합
        spec = {**self.default_spec, **basic_spec, **detailed_spec}
        
        return spec
    
    def _generate_basic_spec(self, source: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """기본 스펙 생성 (프로젝트 개요, 기능, 기술 스택)"""
        
        prompt = f"""당신은 시니어 소프트웨어 아키텍트입니다. 다음 프로젝트의 기본 명세를 작성하세요.

프로젝트: {source.get('name', 'Unknown')}
설명: {source.get('description', 'N/A')}

다음 JSON 형식으로만 응답하세요:

{{
  "project_name": "kebab-case-영문명",
  "description": "한 줄 설명 (50자 이내)",
  "category": "CLI",
  "tags": ["Python", "CLI", "Security"],
  "difficulty": "easy",
  "overview": "프로젝트 목적과 해결하는 문제를 3-5문장으로 설명",
  "core_features": [
    "기능1: 구체적 설명",
    "기능2: 구체적 설명",
    "기능3: 구체적 설명"
  ],
  "tech_stack": {{
    "language": "Python 3.9+",
    "libraries": ["click", "rich", "requests"],
    "testing": "pytest"
  }}
}}

JSON만 출력하세요:"""

        try:
            response = requests.post(
                f"{self.glm_base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.glm_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "glm-5",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 3000
                },
                timeout=120
            )
            
            if response.status_code == 200:
                data = response.json()
                message = data["choices"][0]["message"]
                # content 또는 reasoning_content에서 JSON 추출
                content = message.get("content", "") or message.get("reasoning_content", "")
                json_str = self._extract_json(content)
                if json_str:
                    return json.loads(json_str)
                    
        except requests.Timeout:
            print(f"   타임아웃")
        except Exception as e:
            print(f"   기본 스펙 생성 실패: {e}")
        
        return None
    
    def _generate_detailed_design(self, source: Dict[str, Any], basic_spec: Dict) -> Optional[Dict[str, Any]]:
        """상세 설계 생성 (API, 파일 구조, 코드 예시)"""
        
        project_name = basic_spec.get("project_name", source.get("name", "project"))
        core_features = basic_spec.get("core_features", [])
        
        prompt = f"""당신은 시니어 소프트웨어 아키텍트입니다. '{project_name}' 프로젝트의 상세 설계를 작성하세요.

핵심 기능:
{chr(10).join([f'- {f}' for f in core_features[:3]])}

다음 JSON 형식으로만 응답하세요:

{{
  "file_structure": [
    "{project_name}/",
    "├── src/{project_name}/",
    "│   ├── __init__.py",
    "│   ├── cli.py",
    "│   └── core.py",
    "├── tests/",
    "├── pyproject.toml",
    "└── README.md"
  ],
  "api_design": {{
    "cli_commands": [
      "{project_name.replace('-', ' ')} scan <path>",
      "{project_name.replace('-', ' ')} analyze --output json"
    ],
    "functions": [
      "scan_path(path: Path) -> List[Finding]",
      "analyze_content(content: str) -> Result"
    ],
    "data_models": [
      "class Finding: severity, message, location"
    ]
  }},
  "sample_code": "핵심 로직 15-20줄의 Python 코드",
  "security_considerations": [
    "입력 검증 필요",
    "파일 접근 권한 확인"
  ],
  "error_handling": [
    "FileNotFoundError: 명확한 안내",
    "PermissionError: 권한 문제 해결"
  ],
  "acceptance_criteria": [
    "모든 CLI 명령어 정상 동작",
    "테스트 커버리지 80% 이상"
  ],
  "estimated_time": "3-4시간"
}}

JSON만 출력하세요:"""

        try:
            response = requests.post(
                f"{self.glm_base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.glm_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "glm-5",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 4000
                },
                timeout=120
            )
            
            if response.status_code == 200:
                data = response.json()
                message = data["choices"][0]["message"]
                # content 또는 reasoning_content에서 JSON 추출
                content = message.get("content", "") or message.get("reasoning_content", "")
                json_str = self._extract_json(content)
                if json_str:
                    return json.loads(json_str)
                    
        except requests.Timeout:
            print(f"   상세 설계 타임아웃")
        except Exception as e:
            print(f"   상세 설계 실패: {e}")
        
        return None
    
    def _validate_spec(self, spec: Dict[str, Any]) -> bool:
        """스펙 유효성 검증"""
        required_fields = ["project_name", "description", "core_features"]
        
        for field in required_fields:
            if not spec.get(field):
                return False
        
        # project_name이 kebab-case인지 확인
        name = spec.get("project_name", "")
        if not re.match(r'^[a-z][a-z0-9-]*$', name):
            return False
        
        # core_features가 최소 2개 이상인지 확인
        if len(spec.get("core_features", [])) < 2:
            return False
        
        return True
    
    def _extract_json(self, content: str) -> Optional[str]:
        """응답에서 JSON 추출 (개선된 버전)"""
        
        # 1. ```json ... ``` 블록 찾기
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1).strip()
            try:
                json.loads(json_str)
                return json_str
            except json.JSONDecodeError:
                pass
        
        # 2. 중첩 중괄호 매칭
        brace_start = content.find('{')
        if brace_start != -1:
            depth = 0
            brace_end = -1
            for i in range(brace_start, len(content)):
                if content[i] == '{':
                    depth += 1
                elif content[i] == '}':
                    depth -= 1
                    if depth == 0:
                        brace_end = i
                        break
            
            if brace_end != -1:
                json_str = content[brace_start:brace_end+1]
                try:
                    json.loads(json_str)
                    return json_str
                except json.JSONDecodeError:
                    # 후행 쉼표 제거 시도
                    fixed = re.sub(r',\s*}', '}', json_str)
                    fixed = re.sub(r',\s*]', ']', fixed)
                    try:
                        json.loads(fixed)
                        return fixed
                    except:
                        pass
        
        return None
    
    def format_spec_for_notion(self, spec: Dict[str, Any]) -> str:
        """상세 스펙을 Notion 본문 형식으로 변환 (개선된 버전)"""
        
        sections = []
        
        # 1. 프로젝트 개요
        overview = spec.get('overview', spec.get('description', 'N/A'))
        sections.append(f"## 📋 프로젝트 개요\n\n{overview}")
        
        # 2. 기본 정보
        info_items = [
            f"- **카테고리**: {spec.get('category', 'CLI')}",
            f"- **난이도**: {spec.get('difficulty', 'medium')}",
            f"- **예상 소요 시간**: {spec.get('estimated_time', '3-5시간')}",
            f"- **태그**: {', '.join(spec.get('tags', ['Python']))}",
        ]
        sections.append("## ℹ️ 기본 정보\n\n" + "\n".join(info_items))
        
        # 3. 핵심 기능
        features = spec.get('core_features', [])
        if features:
            sections.append("## 🎯 핵심 기능\n\n" + "\n".join([f"- {f}" for f in features]))
        
        # 4. 기술 스택
        tech = spec.get('tech_stack', {})
        if tech:
            tech_items = [
                f"- **언어**: {tech.get('language', 'Python 3.9+')}",
                f"- **라이브러리**: {', '.join(tech.get('libraries', ['click', 'rich']))}",
                f"- **테스트**: {tech.get('testing', 'pytest')}",
            ]
            sections.append("## 🔧 기술 스택\n\n" + "\n".join(tech_items))
        
        # 5. 파일 구조
        file_struct = spec.get('file_structure', [])
        if file_struct:
            sections.append("## 📁 파일 구조\n\n```\n" + "\n".join(file_struct) + "\n```")
        
        # 6. API 설계
        api = spec.get('api_design', {})
        if api:
            api_parts = ["## 🔌 API 설계\n"]
            
            cli_cmds = api.get('cli_commands', [])
            if cli_cmds:
                api_parts.append("\n### CLI 명령어\n\n```\n" + "\n".join(cli_cmds) + "\n```")
            
            functions = api.get('functions', [])
            if functions:
                api_parts.append("\n### 핵심 함수\n\n" + "\n".join([f"- `{f}`" for f in functions]))
            
            data_models = api.get('data_models', [])
            if data_models:
                api_parts.append("\n### 데이터 모델\n\n" + "\n".join([f"- {m}" for m in data_models]))
            
            sections.append("\n".join(api_parts))
        
        # 7. 샘플 코드
        sample = spec.get('sample_code', '')
        if sample:
            sections.append(f"## 💻 샘플 코드\n\n```python\n{sample}\n```")
        
        # 8. 에러 처리
        error_handling = spec.get('error_handling', [])
        if error_handling:
            sections.append("## ⚠️ 에러 처리\n\n" + "\n".join([f"- {e}" for e in error_handling]))
        
        # 9. 보안 고려사항
        security = spec.get('security_considerations', [])
        if security:
            sections.append("## 🔒 보안 고려사항\n\n" + "\n".join([f"- {s}" for s in security]))
        
        # 10. 테스트 전략
        testing = spec.get('testing_strategy', {})
        if testing:
            test_items = [
                f"- **단위 테스트**: {testing.get('unit_tests', 'pytest')}",
                f"- **커버리지 목표**: {testing.get('coverage_target', '80%')}",
            ]
            sections.append("## 🧪 테스트 전략\n\n" + "\n".join(test_items))
        
        # 11. 완료 기준
        criteria = spec.get('acceptance_criteria', [])
        if criteria:
            sections.append("## ✅ 완료 기준\n\n" + "\n".join([f"- [ ] {c}" for c in criteria]))
        
        # 12. 향후 개선 사항
        future = spec.get('future_enhancements', [])
        if future:
            sections.append("## 🚀 향후 개선 사항\n\n" + "\n".join([f"- {f}" for f in future]))
        
        return "\n\n".join(sections)


# 테스트
if __name__ == "__main__":
    discoverer = PolaDiscoverer()
    
    print("="*60)
    print("🔍 폴라 주도 아이디어 발굴 테스트 v2")
    print("="*60)
    
    ideas = discoverer.discover_with_spec(limit=1)
    
    if ideas:
        idea = ideas[0]
        print(f"\n✅ 발굴된 아이디어: {idea['name']}")
        print(f"   카테고리: {idea['category']}")
        print(f"   설명: {idea['description']}")
        
        if idea.get('detailed_spec'):
            notion_content = discoverer.format_spec_for_notion(idea['detailed_spec'])
            print(f"\n📝 Notion 본문 미리보기:\n")
            print(notion_content[:800] + "...")
    else:
        print("\n❌ 발굴 실패")
