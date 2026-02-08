"""
LLM Writer - 다중 페르소나 블로그 글 작성 시스템 (Async + Pydantic)
"""

import os
import re
import json
import asyncio
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum
from modules.intelligence.config import GLM_API_KEY, GLM_BASE_URL, GLM_MODEL
from modules.intelligence.llm_client_async import AsyncLLMClient
from modules.intelligence.utils import setup_logger
from modules.intelligence.prompt_manager import PromptManager
from modules.intelligence.models import BlogPost

logger = setup_logger(__name__, "writer.log")

class Persona(Enum):
    SECURITY = "security"
    AI_ML = "ai_ml"
    DEVOPS = "devops"
    CVE_ANALYST = "cve_analyst"

class PersonaConfig:
    NOTION_CATEGORIES = ["보안", "AI", "DevOps", "CVE", "IT"]
    PERSONAS = {
        Persona.SECURITY: {
            "name": "보안 전문가",
            "expertise": "사이버 보안, 취약점 분석, 웹 해킹, 침투 테스트",
            "tone": "전문적이지만 실용적이고 현장 감각 있게",
            "category": "보안",
            "default_tags": ["Security", "Cybersecurity", "보안", "취약점"],
            "tag_keywords": ["XSS", "CSRF", "RCE", "Exploit", "Vulnerability", "Zero-day"],
            "structure_guide": """
## 보안 블로그 글 구조 가이드

### 필수 섹션
1. **헤딩**: 매력적인 제목
2. **서론 (10%)**: 실제 보안 사고 사례나 시나리오로 흥미 유발
3. **기술적 분석 (40%)**:
   - 취약점 메커니즘 상세 설명
   - 공격 벡터 다이어그램 (Mermaid)
   - PoC 코드 또는 공격 시나리오
4. **완화 조치 (30%)**:
   - 즉시 적용 가능한 방어 가이드
   - 코드 예시 (설정, 파라미터)
5. **실무 팁 (15%)**: 모니터링, 탐지 방법
6. **결론 (5%)**: 전문가의 인사이트

### 필수 요소
- ✅ Mermaid 공격 흐름도
- ✅ PoC 코드 또는 설정 예시
- ✅ CVE 번호가 있으면 CVSS 벡터 분석
- ✅ 참고 링크 (공식 advisories, writeups)
- ✅ 실무 적용 체크리스트
""",
            "specific_prompt": """
### 보안 분야 작성 특이사항

1. **공격 시나리오 중심**: 단순 기술 설명보다 "어떻게 악용되는지" 실제 시나리오 작성
2. **PoC 코드 필수**: 개념 증명 코드 포함 (학습용, ethical hacking 강조)
3. **시각화 필수**: Mermaid로 공격 흐름도, 네트워크 topology 작성
4. **완화 조치 구체화**: "업데이트하세요" 대신 구체 설정값, 코드 스니펫 제공
5. **윤리적 경고**: 모든 공격 기술 설명 앞에 "방어 목적"임 명시

### 예시 시나리오 구조
```markdown
## 공격 시나리오: OWASP Top 10 활용

공격자는 다음과 같은 단계로 침투를 시도합니다...

mermaid
graph LR
    A[Recon] --> B[Exploit]
    B --> C[Privilege Escalation]
    C --> D[Persistence]

## 방어 가이드
### 1. 즉시 조치
- [ ] WAF 규칙 업데이트: `Rule ID: 1001`
- [ ] 입력 검증 강화

### 2. 장기 대책
```
"""
        },
        Persona.AI_ML: {
            "name": "AI/ML 연구자",
            "expertise": "딥러닝, NLP, LLM, MLOps, Transformer, 생성형 AI",
            "tone": "학술적이지만 이해하기 쉽고, 최신 논문 기반",
            "category": "AI",
            "default_tags": ["AI", "LLM", "Deep Learning", "Machine Learning"],
            "tag_keywords": ["Transformer", "GPT", "Fine-tuning", "RAG", "Diffusion", "Prompt Engineering"],
            "structure_guide": """
## AI/ML 블로그 글 구조 가이드

### 필수 섹션
1. **헤딩**: 논문 제목 스타일
2. **서론 (10%)**: 최신 트렌드나 실제 문제로 motivation
3. **기술적 배경 (20%)**:
   - 관련 연구/논문 인용 (arXiv 링크)
   - 기존 방법론과의 차이점
4. **핵심 아이디어 (30%)**:
   - 알고리즘/아키텍처 설명
   - 수식이 필요하면 간단히 (복잡한 건 생략)
   - Mermaid로 모델 architecture 시각화
5. **구현 및 실험 (25%)**:
   - 코드 예시 (PyTorch/TensorFlow)
   - 실험 결과, 성능 비교
6. **실무 적용 (10%)**: MLOps 관점, 서빙 팁
7. **결론 및 참고자료 (5%)**

### 필수 요소
- ✅ Mermaid architecture diagram
- ✅ 핵심 코드 예시 (실행 가능한)
- ✅ 논문 링크 (arXiv, GitHub repo)
- ✅ 성능 비교표 또는 결과
- ✅ 한계점 및 향후 연구 방향
""",
            "specific_prompt": """
### AI/ML 분야 작성 특이사항

1. **최신 논문 기반**: arXiv, top conference 논문 인용
2. **기술적 깊이**: 단순 뉴스가 아닌 원리, 알고리즘 설명
3. **코드 중심**: PyTorch/TensorFlow 스크립트로 실제 구현 보여주기
4. **시각화**:
   - Mermaid로 모델 architecture
   - 표로 성능 비교
   - 그래프 설명 (텍스트로 대체)
5. **실무 관점**: MLOps, 서빙, 최적화 팁 포함

### 예시 구조
```markdown
## 배경: Transformer의 등장

기존 RNN 계열 모델의 한계를 극복하기 위해...

## 핵심 아이디어: Self-Attention

mermaid
graph LR
    Input[Input Sequence] --> Embed[Embedding]
    Embed --> Attention[Multi-Head Attention]
    Attention --> FFN[Feed Forward]

## 구현: PyTorch로 구현해보기

```python
import torch.nn as nn

class SimpleAttention(nn.Module):
    ...
```

## 성능 비교
| 모델 | BLEU | inference time |
|------|------|----------------|
| RNN | 0.24 | 120ms |
```
"""
        },
        Persona.DEVOPS: {
            "name": "DevOps/SRE 엔지니어",
            "expertise": "CI/CD, Kubernetes, Docker, Cloud, IaC, 모니터링",
            "tone": "실무 중심, 실행 가능한 가이드, 트러블슈팅 관점",
            "category": "DevOps",
            "default_tags": ["DevOps", "K8s", "Docker", "Kubernetes", "CI/CD"],
            "tag_keywords": ["Kubernetes", "Helm", "Terraform", "ArgoCD", "Prometheus", "Grafana"],
            "structure_guide": """
## DevOps 블로그 글 구조 가이드

### 필수 섹션
1. **헤딩**: 문제 해결 중심
2. **서론 (10%)**: 실제 운영 이슈나 pain point 소개
3. **문제 분석 (20%)**:
   - 원인 규명 과정
   - 로그, 메트릭 분석
4. **솔루션 (35%)**:
   - 아키텍처 다이어그램 (Mermaid)
   - 단계별 구현 가이드
   - YAML/코드 예시 (복붙 가능)
5. **베스트 프랙티스 (20%)**:
   - 모니터링 설정
   - 알람 기준
   - 운영 팁
6. **트러블슈팅 (10%)**: 흔한 실수, 디버깅 팁
7. **참고자료 (5%)**

### 필수 요소
- ✅ Mermaid architecture diagram
- ✅ 실행 가능한 YAML/HCL 코드
- ✅ Before/After 비교
- ✅ 모니터링/알람 설정 예시
- ✅ 테스트/검증 방법
""",
            "specific_prompt": """
### DevOps 분야 작성 특이사항

1. **실행 가능성**: 모든 코드는 복붙해서 바로 실행 가능해야 함
2. **단계별 가이드**: Step 1, 2, 3...으로 명확히
3. **실제 운영 관점**: Production에서의 고려사항
4. **YAML 중심**: Kubernetes, Helm, Terraform 코드 필수
5. **모니터링**: Prometheus/Grafana 대시보드 설정 포함

### 예시 구조
```markdown
## 문제: Kubernetes 클러스터 장애 발생

### 현상
- Pod가 계속 CrashLoopBackOff...
- 로그: `OOMKilled`

### 원인 분석

```bash
kubectl describe pod ...
```

메모리 제한이 너무 보수적...

## 솔루션: HPA + VPA 적용

mermaid
graph LR
    A[Metrics Server] --> B[HPA]
    B --> C[Pod Scale]

### Step 1: Metrics Server 설치

```yaml
apiVersion: v1
kind: ConfigMap
...
```

### 모니터링 설정

```yaml
# PrometheusRule
```
```
"""
        },
        Persona.CVE_ANALYST: {
            "name": "CVE 취약점 분석가",
            "expertise": "CVE 분석, 제로데이 공격, 패치 관리, 익스플로잇",
            "tone": "분석적, 신속하고 정확한 정보 전달",
            "category": "CVE",
            "default_tags": ["CVE", "Vulnerability", "Patch", "Zero-day"],
            "tag_keywords": ["CVE", "CVSS", "PoC", "Exploit", "Patch"],
            "structure_guide": """
## CVE 분석 블로그 글 구조 가이드

### 필수 섹션
1. **헤딩**: CVE 번호 + 심각도
2. **개요 (10%)**:
   - CVE 번호, CVSS 점수, 영향 제품
   - 심각도 배지 (Critical/High/Medium)
3. **취약점 상세 (25%)**:
   - 기술적 원인
   - 영향 범위 (제품, 버전)
4. **공격 시나리오 (25%)**:
   - 익스플로잇 조건
   - PoC 설명 (코드는 ethical guidelines)
   - Mermaid로 공격 경로
5. **패치 및 완화 (30%)**:
   - 공식 패치 버전
   - 임시 완화 조치
   - 적용 가이드
6. **탐지 방법 (5%)**:
   - IOC (Indicators of Compromise)
   - 탐지 규칙 (YARA/Sigma)
7. **타임라인 & 참고자료 (5%)**

### 필수 요소
- ✅ CVE ID, CVSS 벡터, 점수
- ✅ 영향 제품/버전 표
- ✅ 패치 diff 분석 (가능하면)
- ✅ IOC, 탐지 규칙
- ✅ 공식 advisories 링크
""",
            "specific_prompt": """
### CVE 분석 작성 특이사항

1. **정확성 최우선**: 잘못된 정보는 실무 혼란 초래
2. **신속성**: 최신 CVE는 빠른 분석 필수
3. **구체성**: "영향 받는 버전" 정확히 명시
4. **윤리적 경고**: PoC는 방어 목적임 강조
5. **실행 가능한 완화**: 당장 적용 가능한 조치

### 예시 구조
```markdown
## CVE-2024-XXXXXX: [Product] Critical RCE Vulnerability

### 개요
- **CVE ID**: CVE-2024-XXXXXX
- **CVSS**: 9.8 (Critical)
- **영향 제품**: Product X v1.0 - v2.5

### CVSS 벡터 분석
```
CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H
```

### 취약점 상세
원인: 잘못된 입력 검증...

### 익스플로잇 조건
- 인증 불필요
- 네트워크 접근 가능

### 패치 적용 가이드

#### Step 1: 영향 받는지 확인

```bash
# Product check script
```

#### Step 2: 패치 적용

### 탐지 규칙 (Sigma)

```yaml
detection:
    ...
```
```
"""
        },
    }

    @classmethod
    def get(cls, persona: Persona) -> Dict:
        return cls.PERSONAS[persona]

class CategoryClassifier:
    KEYWORDS = {
        Persona.SECURITY: ["취약점", "해킹", "보안", "exploit", "security"],
        Persona.AI_ML: ["ai", "ml", "딥러닝", "llm", "gpt", "model"],
        Persona.DEVOPS: ["devops", "ci/cd", "k8s", "docker", "cloud"],
        Persona.CVE_ANALYST: ["cve", "cvss", "poc", "패치"],
    }

    @classmethod
    def classify(cls, article_data: Dict) -> Persona:
        text = (article_data.get("title", "") + " " + article_data.get("summary", "")).lower()
        scores = {p: sum(1 for kw in kws if kw in text) for p, kws in cls.KEYWORDS.items()}
        if not scores or max(scores.values()) == 0:
            return Persona.SECURITY
        return max(scores, key=scores.get)

class TagExtractor:
    @classmethod
    def extract_tags(cls, article_data: Dict, persona: Persona, max_tags: int = 5) -> List[str]:
        config = PersonaConfig.get(persona)
        text = (article_data.get("title", "") + " " + article_data.get("summary", "")).lower()
        tags = []
        for kw in config.get("tag_keywords", []):
            if kw.lower() in text:
                tags.append(kw)
        tags.extend(re.findall(r'CVE-\d{4}-\d{4,7}', text, re.IGNORECASE))
        if len(tags) < max_tags:
            for t in config.get("default_tags", []):
                if t not in tags:
                    tags.append(t)
        return list(dict.fromkeys(tags))[:max_tags]

    @classmethod
    def get_category(cls, persona: Persona) -> str:
        return PersonaConfig.get(persona).get("category", "IT")

class BlogWriter:
    """다중 페르소나 블로그 작성기 (Async)"""

    def __init__(self, client: AsyncLLMClient = None):
        self.client = client or AsyncLLMClient()

    async def generate_article(self, article_data: Dict, persona: Optional[Persona] = None) -> Dict:
        """단일 기사 생성 (비동기) - 2단계 분리 방식"""
        persona = persona or CategoryClassifier.classify(article_data)
        config = PersonaConfig.get(persona)

        category = TagExtractor.get_category(persona)

        # ===== 1단계: 메타데이터 생성 (제목 + 요약 + 태그) =====
        logger.info(f"[Step 1/2] Generating metadata for: {article_data.get('title', 'N/A')[:40]}")
        metadata = await self._generate_metadata(article_data, persona, config, category)

        # ===== 2단계: 본문 생성 (순수 Markdown) =====
        logger.info(f"[Step 2/2] Generating content for: {metadata['title'][:40]}")
        content = await self._generate_content(article_data, metadata, persona, config)

        return {
            "title": metadata['title'],
            "summary": metadata['summary'],
            "content": content,
            "tags": metadata['tags'],
            "category": metadata['category'],
            "persona": persona.value,
            "original_url": article_data.get("url"),
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    async def _generate_metadata(self, article_data: Dict, persona: Persona, config: Dict, category: str) -> Dict:
        """1단계: 메타데이터 생성 (제목 + 요약 + 태그)"""
        system_prompt = PromptManager.get("writer_metadata.base_system",
                                        name=config['name'],
                                        expertise=config['expertise'],
                                        tone=config['tone'],
                                        persona_specific=config.get('specific_prompt', ''))

        user_prompt = PromptManager.get("writer_metadata.user",
                                      source=article_data.get('source', 'Unknown'),
                                      title=article_data.get('title', 'N/A'),
                                      url=article_data.get('url', 'N/A'),
                                      summary=article_data.get('summary', 'N/A'),
                                      category=category)

        try:
            response = await self.client.chat(system_prompt, user_prompt)
            return self._parse_metadata_response(response, category)
        except Exception as e:
            logger.error(f"Failed to generate metadata: {e}")
            raise

    async def _generate_content(self, article_data: Dict, metadata: Dict, persona: Persona, config: Dict) -> str:
        """2단계: 본문 생성 (순수 Markdown)"""
        system_prompt = PromptManager.get("writer_content.base_system",
                                        name=config['name'],
                                        expertise=config['expertise'],
                                        tone=config['tone'],
                                        persona_specific=config.get('specific_prompt', ''))

        user_prompt = PromptManager.get("writer_content.user",
                                      title=metadata['title'],
                                      summary=metadata['summary'],
                                      tags=", ".join(metadata['tags']),
                                      source=article_data.get('source', 'Unknown'),
                                      original_title=article_data.get('title', 'N/A'),
                                      url=article_data.get('url', 'N/A'),
                                      original_summary=article_data.get('summary', 'N/A'))

        try:
            response = await self.client.chat(system_prompt, user_prompt)
            # 본문은 순수 마크다운이므로 그대로 사용 (앞뒤 공백 제거)
            content = response.strip()
            # 최소 길이 체크
            if len(content) < 1000:
                logger.warning(f"Generated content too short ({len(content)} chars), may need regeneration")
            return content
        except Exception as e:
            logger.error(f"Failed to generate content: {e}")
            raise

    def _parse_metadata_response(self, response: str, category: str) -> Dict:
        """메타데이터 JSON 응답 파싱"""
        try:
            # JSON 코드 블록 추출
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
            json_str = json_match.group(1) if json_match else response

            # JSON 범위 추출
            if '{' in json_str:
                start = json_str.find('{')
                brace_count = 0
                end = start
                for i in range(start, len(json_str)):
                    if json_str[i] == '{':
                        brace_count += 1
                    elif json_str[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end = i + 1
                            break
                json_str = json_str[start:end]

            # JSON 파싱
            import json as json_lib
            data = json_lib.loads(json_str)

            # 필수 필드 검증
            if not data.get('title'):
                raise ValueError("Missing 'title' field")
            if not data.get('summary'):
                raise ValueError("Missing 'summary' field")
            if not data.get('tags'):
                raise ValueError("Missing 'tags' field")

            return {
                "title": data['title'],
                "summary": data['summary'],
                "tags": data['tags'],
                "category": data.get('category', category)
            }
        except Exception as e:
            logger.error(f"Failed to parse metadata JSON: {e}")
            logger.error(f"Response: {response[:500]}")
            raise

    async def generate_article_batch(self, articles: List[Dict]) -> List[Dict]:
        """여러 기사 병렬 생성"""
        tasks = [self.generate_article(article) for article in articles]
        return await asyncio.gather(*tasks, return_exceptions=True)

    def _parse_result(self, content: str, original: Dict, persona: Persona, category: str, tags: List[str]) -> Dict:
        """Pydantic 모델을 사용한 파싱"""
        # 빈 응답 체크
        if not content or not content.strip():
            logger.error("LLM returned empty response")
            return self._create_fallback(original, persona, category, tags)

        try:
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            json_str = json_match.group(1) if json_match else content

            # JSON 범위 추출 개선
            if '{' in json_str:
                start = json_str.find('{')
                # 중괄호 균형 맞추기
                brace_count = 0
                end = start
                for i in range(start, len(json_str)):
                    if json_str[i] == '{':
                        brace_count += 1
                    elif json_str[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end = i + 1
                            break
                json_str = json_str[start:end]

            # Pydantic 파싱
            blog_post = BlogPost.model_validate_json(json_str)

            return {
                "title": blog_post.title,
                "summary": blog_post.summary,
                "content": blog_post.content,
                "tags": blog_post.tags or tags,
                "category": blog_post.category or category,
                "persona": persona.value,
                "original_url": original.get("url"),
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            logger.warning(f"Pydantic parsing failed ({e}), attempting fallback parsing...")
            return self._create_fallback(original, persona, category, tags, content)

    def _create_fallback(self, original: Dict, persona: Persona, category: str, tags: List[str], llm_response: str = None) -> Dict:
        """Fallback 결과 생성"""
        # LLM 응답에서 JSON 블록 제거 후 content 사용
        content_text = llm_response or ""

        # 디버깅: LLM 원본 응답 로깅
        logger.info(f"[FALLBACK] LLM response length: {len(content_text)}, First 200 chars: {content_text[:200] if content_text else '(EMPTY)'}")

        if content_text:
            # JSON 코드 블록 제거 (전체 JSON 객체 제거, content 필드 추출 아님!)
            # ````json ... ``` 블록 제거 후 그 안의 content만 사용
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', content_text, re.DOTALL)
            if json_match:
                # JSON 문자열에서 content 필드 추출
                json_str = json_match.group(1)
                # 정규식으로 content 필드 값 추출
                content_match = re.search(r'"content"\s*:\s*"((?:[^"\\]|\\.)*)"', json_str, re.DOTALL)
                if content_match:
                    # 이스케이프된 문자를 원래대로 복원 (JSON 표준)
                    import json as json_lib
                    try:
                        # content 필드 값만 파싱
                        content_value = f'"{content_match.group(1)}"'
                        content_text = json_lib.loads(content_value)
                    except:
                        # 파싱 실패하면 그냥 원본 사용
                        content_text = content_match.group(1)
                else:
                    content_text = ""
            else:
                # 코드 블록이 없으면 그냥 사용
                content_text = content_text.strip()

        # 여전히 비어있거나 너무 짧으면 원본 요약 사용
        if not content_text or len(content_text) < 100:
            logger.warning(f"[FALLBACK] Content still too short ({len(content_text)}), using original summary")
            content_text = f"# {original.get('title', '제목 없음')}\n\n{original.get('summary', '요약 없음')}\n\n> 본문 생성 실패: 원본 기사를 참고하세요\n\n원본 URL: {original.get('url', '')}"

        logger.info(f"[FALLBACK] Final content length: {len(content_text)}, First 200 chars: {content_text[:200]}")

        return {
            "title": original.get("title"),
            "summary": original.get("summary"),
            "content": content_text,
            "tags": tags,
            "category": category,
            "persona": persona.value,
            "original_url": original.get("url"),
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }