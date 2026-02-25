#!/usr/bin/env python3
"""
Pola Discoverer - 폴라(Planner Agent) 주도 아이디어 발굴
GLM-5를 사용하여 상세 스펙 작성
"""
import os
import json
import random
from typing import List, Dict, Any, Optional
from datetime import datetime
import requests
from dotenv import load_dotenv

# Load environment
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))


class PolaDiscoverer:
    """폴라(Planner Agent) 주도 아이디어 발굴기"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.glm_base_url = os.getenv("BASE_URL", "https://api.z.ai/api/coding/paas/v4")
        self.glm_api_key = os.getenv("API_KEY")
        self.github_token = os.getenv("GITHUB_TOKEN")
        
    def discover_with_spec(self, limit: int = 3) -> List[Dict[str, Any]]:
        """
        소스 수집 → 폴라 분석 → 상세 스펙 작성
        
        Returns:
            List of project ideas with detailed specs
        """
        print("🔍 Step 1: 소스 수집 중...")
        
        # 1. 소스 수집
        sources = self._collect_sources()
        print(f"   수집된 소스: {len(sources)}개")
        
        # 2. 폴라 분석 - 가장 유망한 프로젝트 선별
        print("\n💡 Step 2: 폴라 분석 중 (GLM-5)...")
        ideas = []
        
        for i in range(min(limit, len(sources))):
            source = sources[i]
            print(f"   분석 중: {source['name'][:50]}...")
            
            # GLM-5로 상세 스펙 작성
            spec = self._generate_detailed_spec(source)
            
            if spec:
                ideas.append({
                    "name": spec.get("project_name", source["name"]),
                    "description": spec.get("description", ""),
                    "source_url": source.get("url"),
                    "category": spec.get("category", "기타"),
                    "tags": spec.get("tags", []),
                    "detailed_spec": spec  # 상세 스펙 전체 저장
                })
                print(f"   ✅ 스펙 작성 완료: {spec.get('project_name', 'Unknown')}")
        
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
        
        # 2. predefined ideas (fallback)
        predefined = self._predefined_ideas()
        sources.extend(predefined)
        
        # 섞기
        random.shuffle(sources)
        
        return sources[:10]  # 최대 10개
    
    def _github_trending(self) -> List[Dict[str, Any]]:
        """GitHub Trending에서 프로젝트 수집"""
        sources = []
        
        headers = {}
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"
        
        # Python trending
        url = "https://api.github.com/search/repositories"
        params = {
            "q": "language:python stars:>100 pushed:>2024-01-01",
            "sort": "stars",
            "order": "desc",
            "per_page": 5
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                for item in data.get("items", []):
                    sources.append({
                        "name": item["name"],
                        "description": item.get("description", ""),
                        "url": item["html_url"],
                        "stars": item["stargazers_count"],
                        "language": item.get("language", "Unknown"),
                        "source": "github_trending"
                    })
        except Exception as e:
            print(f"   GitHub API 에러: {e}")
        
        return sources
    
    def _predefined_ideas(self) -> List[Dict[str, Any]]:
        """사전 정의된 아이디어 풀"""
        ideas = [
            {
                "name": "secrets-leak-scanner",
                "description": "Git 저장소에서 실수로 커밋된 시크릿과 API 키 스캔",
                "url": "https://github.com/features/security",
                "source": "security_need"
            },
            {
                "name": "api-rate-limiter",
                "description": "다양한 백엔드에 적용 가능한 유연한 API 속도 제한 라이브러리",
                "url": None,
                "source": "devops_need"
            },
            {
                "name": "log-anomaly-detector",
                "description": "로그 파일에서 이상 패턴을 자동으로 감지하는 도구",
                "url": None,
                "source": "security_need"
            },
            {
                "name": "docker-security-scanner",
                "description": "Docker 이미지의 취약점을 스캔하고 보고서 생성",
                "url": None,
                "source": "security_need"
            },
            {
                "name": "k8s-resource-monitor",
                "description": "Kubernetes 클러스터 리소스 사용량 모니터링 및 알림",
                "url": None,
                "source": "devops_need"
            }
        ]
        return ideas
    
    def _generate_detailed_spec(self, source: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """GLM-5를 사용하여 상세 스펙 작성"""
        
        # 정교한 프롬프트
        prompt = f"""당신은 시니어 소프트웨어 아키텍트입니다. 다음 프로젝트에 대한 **매우 상세한** 기술 명세서를 작성하세요.

## 프로젝트 정보
- **이름**: {source.get('name', 'Unknown')}
- **설명**: {source.get('description', 'N/A')}
- **소스**: {source.get('source', 'N/A')}

## 요구사항
다음 JSON 형식으로 **최대한 상세하게** 작성하세요. 각 필드는 구체적이고 실행 가능해야 합니다.

```json
{{
  "project_name": "영문 프로젝트명 (kebab-case, 예: my-cli-tool)",
  "description": "한 줄 설명 (50자 이내)",
  "category": "CLI 또는 Security 또는 DevOps",
  "tags": ["Python", "CLI", "Security"],
  "difficulty": "easy 또는 medium 또는 hard",
  
  "overview": "프로젝트의 목적, 해결하는 문제, 사용 대상을 5-7문장으로 상세히 설명",
  
  "core_features": [
    "기능1: 구체적인 동작 설명",
    "기능2: 구체적인 동작 설명",
    "기능3: 구체적인 동작 설명",
    "기능4: 구체적인 동작 설명",
    "기능5: 구체적인 동작 설명"
  ],
  
  "tech_stack": {{
    "language": "Python 3.9+",
    "libraries": ["click==8.1.0", "rich==13.0.0", "requests==2.31.0"],
    "framework": "None (CLI)",
    "testing": "pytest + pytest-cov",
    "linting": "ruff + mypy"
  }},
  
  "file_structure": [
    "project_name/",
    "├── src/",
    "│   └── project_name/",
    "│       ├── __init__.py",
    "│       ├── cli.py",
    "│       ├── core.py",
    "│       └── utils.py",
    "├── tests/",
    "│   ├── __init__.py",
    "│   └── test_core.py",
    "├── pyproject.toml",
    "├── README.md",
    "└── .gitignore"
  ],
  
  "api_design": {{
    "cli_commands": [
      "project-name scan <path> --output json",
      "project-name analyze <file> --verbose",
      "project-name report --format html"
    ],
    "functions": [
      "scan_directory(path: Path) -> List[Finding]",
      "analyze_content(content: str) -> AnalysisResult",
      "generate_report(findings: List[Finding], format: str) -> str"
    ],
    "data_models": [
      "class Finding: id, severity, description, location, remediation",
      "class AnalysisResult: score, issues, recommendations"
    ]
  }},
  
  "sample_code": "핵심 로직을 보여주는 20-30줄의 실제 동작하는 Python 코드",
  
  "security_considerations": [
    "입력 검증: 모든 사용자 입력은 검증되어야 함",
    "파일 접근: 경로 순회 공격 방지",
    "출력: 민감한 정보 마스킹"
  ],
  
  "testing_strategy": {{
    "unit_tests": "모든 핵심 함수에 대한 단위 테스트",
    "integration_tests": "CLI 명령어 통합 테스트",
    "coverage_target": "80% 이상",
    "test_fixtures": "테스트용 샘플 데이터 파일"
  }},
  
  "error_handling": [
    "FileNotFoundError: 명확한 에러 메시지와 해결 방안",
    "PermissionError: 권한 문제 안내",
    "ValueError: 잘못된 입력에 대한 가이드"
  ],
  
  "documentation": {{
    "readme_sections": ["설치", "사용법", "옵션", "예제", "기여하기"],
    "docstrings": "Google 스타일 docstring",
    "examples": "5개 이상의 실제 사용 예시"
  }},
  
  "estimated_time": "4-6시간",
  
  "acceptance_criteria": [
    "모든 CLI 명령어가 정상 동작함",
    "테스트 커버리지 80% 이상",
    "README에 설치 및 사용법이 명확히 기재됨",
    "에러 메시지가 사용자 친화적임"
  ],
  
  "future_enhancements": [
    "향후 개선 사항 1",
    "향후 개선 사항 2",
    "향후 개선 사항 3"
  ]
}}
```

**중요**: 
1. JSON만 출력하세요 (설명 없이)
2. 모든 필드를 채우세요
3. 구체적이고 실행 가능한 내용을 작성하세요
4. sample_code는 실제 동작하는 코드여야 합니다"""

        try:
            response = requests.post(
                f"{self.glm_base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.glm_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "glm-5",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 4000
                },
                timeout=180
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                
                # JSON 추출
                json_str = self._extract_json(content)
                if json_str:
                    spec = json.loads(json_str)
                    # 기본값 보완
                    spec.setdefault('estimated_time', '2-4시간')
                    spec.setdefault('file_structure', [])
                    spec.setdefault('api_design', {})
                    spec.setdefault('security_considerations', [])
                    spec.setdefault('testing_strategy', 'pytest')
                    spec.setdefault('future_enhancements', [])
                    return spec
            else:
                print(f"   GLM API 에러: {response.status_code}")
                
        except requests.Timeout:
            print(f"   GLM API 타임아웃")
        except Exception as e:
            print(f"   스펙 생성 실패: {e}")
        
        return None
    
    def _extract_json(self, content: str) -> Optional[str]:
        """응답에서 JSON 추출"""
        import re
        
        # ```json ... ``` 블록 찾기
        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        if json_match:
            return json_match.group(1)
        
        # { ... } 블록 찾기
        brace_start = content.find('{')
        brace_end = content.rfind('}')
        if brace_start != -1 and brace_end != -1:
            return content[brace_start:brace_end+1]
        
        return None
    
    def format_spec_for_notion(self, spec: Dict[str, Any]) -> str:
        """상세 스펙을 Notion 본문 형식으로 변환 (개선된 버전)"""
        
        sections = []
        
        # 1. 프로젝트 개요
        overview = spec.get('overview', 'N/A')
        sections.append(f"## 📋 프로젝트 개요\n\n{overview}")
        
        # 2. 기본 정보 테이블
        info_items = [
            ("카테고리", spec.get('category', 'N/A')),
            ("난이도", spec.get('difficulty', 'N/A')),
            ("예상 소요 시간", spec.get('estimated_time', 'N/A')),
            ("태그", ', '.join(spec.get('tags', []))),
        ]
        info_table = "## ℹ️ 기본 정보\n\n" + "\n".join([f"- **{k}**: {v}" for k, v in info_items])
        sections.append(info_table)
        
        # 3. 핵심 기능
        features = spec.get('core_features', [])
        if features:
            features_md = "## 🎯 핵심 기능\n\n" + "\n".join([f"- {f}" for f in features])
            sections.append(features_md)
        
        # 4. 기술 스택
        tech = spec.get('tech_stack', {})
        if tech:
            tech_items = [
                f"- **언어**: {tech.get('language', 'N/A')}",
                f"- **라이브러리**: {', '.join(tech.get('libraries', []))}",
                f"- **프레임워크**: {tech.get('framework', 'None')}",
                f"- **테스트**: {tech.get('testing', 'N/A')}",
                f"- **린팅**: {tech.get('linting', 'N/A')}",
            ]
            sections.append("## 🔧 기술 스택\n\n" + "\n".join(tech_items))
        
        # 5. 파일 구조
        file_struct = spec.get('file_structure', [])
        if file_struct:
            struct_md = "## 📁 파일 구조\n\n```\n" + "\n".join(file_struct) + "\n```"
            sections.append(struct_md)
        
        # 6. API 설계
        api = spec.get('api_design', {})
        if api:
            api_parts = ["## 🔌 API 설계\n"]
            
            # CLI 명령어
            cli_cmds = api.get('cli_commands', [])
            if cli_cmds:
                api_parts.append("\n### CLI 명령어\n\n```\n" + "\n".join(cli_cmds) + "\n```")
            
            # 핵심 함수
            functions = api.get('functions', [])
            if functions:
                api_parts.append("\n### 핵심 함수\n\n" + "\n".join([f"- `{f}`" for f in functions]))
            
            # 데이터 모델
            data_models = api.get('data_models', [])
            if data_models:
                api_parts.append("\n### 데이터 모델\n\n" + "\n".join([f"- {m}" for m in data_models]))
            
            sections.append("\n".join(api_parts))
        
        # 7. 샘플 코드
        sample = spec.get('sample_code', '')
        if sample:
            sample_md = f"## 💻 샘플 코드\n\n```python\n{sample}\n```"
            sections.append(sample_md)
        
        # 8. 에러 처리
        error_handling = spec.get('error_handling', [])
        if error_handling:
            err_md = "## ⚠️ 에러 처리\n\n" + "\n".join([f"- {e}" for e in error_handling])
            sections.append(err_md)
        
        # 9. 보안 고려사항
        security = spec.get('security_considerations', [])
        if security:
            sec_md = "## 🔒 보안 고려사항\n\n" + "\n".join([f"- {s}" for s in security])
            sections.append(sec_md)
        
        # 10. 테스트 전략
        testing = spec.get('testing_strategy', {})
        if testing:
            test_items = [
                f"- **단위 테스트**: {testing.get('unit_tests', 'N/A')}",
                f"- **통합 테스트**: {testing.get('integration_tests', 'N/A')}",
                f"- **커버리지 목표**: {testing.get('coverage_target', 'N/A')}",
                f"- **테스트 픽스처**: {testing.get('test_fixtures', 'N/A')}",
            ]
            sections.append("## 🧪 테스트 전략\n\n" + "\n".join(test_items))
        
        # 11. 문서화
        docs = spec.get('documentation', {})
        if docs:
            doc_items = [
                f"- **README 섹션**: {', '.join(docs.get('readme_sections', []))}",
                f"- **Docstring 스타일**: {docs.get('docstrings', 'N/A')}",
                f"- **사용 예제**: {docs.get('examples', 'N/A')}",
            ]
            sections.append("## 📚 문서화 요구사항\n\n" + "\n".join(doc_items))
        
        # 12. 완료 기준
        criteria = spec.get('acceptance_criteria', [])
        if criteria:
            crit_md = "## ✅ 완료 기준 (Acceptance Criteria)\n\n" + "\n".join([f"- [ ] {c}" for c in criteria])
            sections.append(crit_md)
        
        # 13. 향후 개선 사항
        future = spec.get('future_enhancements', [])
        if future:
            future_md = "## 🚀 향후 개선 사항\n\n" + "\n".join([f"- {f}" for f in future])
            sections.append(future_md)
        
        return "\n\n".join(sections)


# 테스트
if __name__ == "__main__":
    discoverer = PolaDiscoverer()
    
    print("="*60)
    print("🔍 폴라 주도 아이디어 발굴 테스트")
    print("="*60)
    
    ideas = discoverer.discover_with_spec(limit=1)
    
    if ideas:
        idea = ideas[0]
        print(f"\n✅ 발굴된 아이디어: {idea['name']}")
        print(f"   카테고리: {idea['category']}")
        print(f"   설명: {idea['description']}")
        
        # Notion용 포맷
        if idea.get('detailed_spec'):
            notion_content = discoverer.format_spec_for_notion(idea['detailed_spec'])
            print(f"\n📝 Notion 본문 미리보기:\n")
            print(notion_content[:500] + "...")
    else:
        print("\n❌ 발굴 실패")
