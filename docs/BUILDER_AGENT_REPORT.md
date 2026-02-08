# OpenClaw Builder Agent 프로젝트 보고서

**작성일**: 2026-02-07
**버전**: 1.0.0
**작성자**: Builder Agent Team

---

## 1. 프로젝트 개요

### 1.1 목적

Builder Agent는 **DevOps/보안/유틸리티 분야의 프로젝트를 자동으로 생성하는 AI 기반 시스템**입니다. 주제 선정부터 코드 생성, 테스트, GitHub 배포까지 전체 파이프라인을 자동화합니다.

### 1.1 핵심 기능

| 기능 | 설명 | 기술 |
|------|------|------|
| **AI 주제 생성** | GLM-4.7이 창의적인 프로젝트 아이디어 생성 | GLM-4.7 LLM |
| **주제 관리** | SQLite + Notion Database 연동 | Python, Notion API |
| **코드 생성** | 구조화된 Python 프로젝트 자동 생성 | GLM-4.7, 템플릿 |
| **자가 테스트** | pytest로 버그 자동 수정 | pytest, retry 로직 |
| **Git 배포** | GitHub 자동 커밋/배포 | GitPython, GitHub API |

---

## 2. 최신 변경사항 (2026-02-07)

### 2.1 AI 주제 생성 기능 추가 ✨ NEW

**변경 내용**:
- 기존 점수 기반 주제 선정 방식에서 **AI가 주제를 생성**하는 방식으로 확장
- `ai_topic_generator.py` 모듈 추가
- 카테고리별(DevOps/Security/Utility) 맞춤 주제 생성

**추가된 파일**:
```
modules/builder/
├── ai_topic_generator.py       # AI 주제 생성기 (NEW)
├── import_existing_projects.py  # 기존 프로젝트 DB 등록 (NEW)
├── import_to_notion.py          # Notion 일괄 등록 (NEW)
└── generate_file_converter.py  # 프로젝트 생성 스크립트 (NEW)
```

### 2.2 다중 데이터베이스 지원

| 데이터베이스 | 용도 | 상태 |
|-------------|------|------|
| **SQLite** (local) | 로컬 프로젝트 관리, 빠른 조회 | ✅ 활성 |
| **Notion** (cloud) | 팀协作, 워크플로우 통합 | ✅ 활성 |

### 2.3 프로젝트 자동 생성 개선

**개선 전**:
- 수동으로 프로젝트 구조 생성
- 일관되지 않은 파일 구조

**개선 후**:
- 표준화된 프로젝트 템플릿
- `Project/{프로젝트명}/` 경로 자동 생성
- README, requirements.txt, .gitignore 자동 생성

---

## 3. 시스템 아키텍처

### 3.1 전체 파이프라인

```
┌─────────────────────────────────────────────────────────────┐
│                    Builder Agent Pipeline                    │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  🤖 AI 주제  │    │ ⚙️ 점수 기반  │    │  📝 수동    │
│   생성기     │    │   주제 선택  │    │   추가       │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │
       └───────────────────┴───────────────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │  📊 주제 DB     │
                  │ (SQLite+Notion)│
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │  🔨 코드 생성   │
                  │  (GLM-4.7)      │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │  🧪 테스트      │
                  │  (pytest x3)    │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │  🚀 Git 배포    │
                  │  (GitHub)       │
                  └─────────────────┘
```

### 3.2 핵심 모듈 구조

```
modules/builder/
├── main.py                    # 전체 파이프라인 오케스트레이터
├── planner.py                 # SQLite DB 기반 주제 관리
├── planner_notion.py          # Notion DB 기반 주제 관리
├── ai_topic_generator.py      # AI 주제 생성 (GLM-4.7)
├── coder.py                   # 코드 생성기 (GLM-4.7)
├── tester.py                  # 자가 수정 테스트 시스템
├── git_manager.py             # Git 자동화 (Commit, Push)
└── Project/                   # 생성된 프로젝트 저장소
    ├── encoder/               # Text Encoder (완료)
    ├── Google Search/         # 검색 자동화 (완료)
    ├── port_security/         # 포트 스캐너 (완료)
    ├── robots.txt Search/     # robots.txt 분석기 (완료)
    ├── KISA-CIIP-2026/        # 취약점 진단 시스템 (진행중)
    ├── File Converter/        # 파일 변환기 (NEW)
    └── {AI 생성 프로젝트들}  # AI로 생성된 프로젝트들
```

---

## 4. 데이터베이스 현황

### 4.1 프로젝트 통계

| 항목 | SQLite (local) | Notion (cloud) |
|------|----------------|----------------|
| 총 프로젝트 | **25개** | **12개** |
| 완료 (Done/게시 완료) | 6개 | 0개 |
| 진행중 (In Progress/검토중) | 2개 | 2개 |
| 대기중 (Planning/백로그) | **17개** | **10개** |

### 4.2 최근 추가된 AI 생성 프로젝트

| ID | 이름 | 카테고리 | 상태 |
|----|------|----------|------|
| 21 | IaC Policy Guard | Security | Planning |
| 22 | K8s Capacity Planner | DevOps | Planning |
| 23 | Log Masker Agent | Security | Planning |
| 24 | K8s Resource Rightsizer | DevOps | Planning |
| 25 | Container Log Secret Guard | Security | Planning |
| 20 | File Converter | Utility | Planning |

### 4.3 기존 등록된 프로젝트

| ID | 이름 | 상태 | 비고 |
|----|------|------|------|
| 13 | Text Encoder | ✅ Done | GitHub Actions 배포 완료 |
| 14 | Google Search Automation | ✅ Completed | reCAPTCHA 우회 |
| 15 | Port Security Scanner | ✅ Completed | 45개 사이트 스캔 |
| 16 | robots.txt Analyzer | ✅ Completed | 자동 설치 지원 |
| 17 | KISA-CIIP-2026 | 🔄 In Progress | 201개 진단 항목 |
| 18 | OpenClaw Builder Agent | 🔄 In Progress | 본 시스템 |

---

## 5. AI 주제 생성 상세

### 5.1 생성된 주제 예시

**DevOps 카테고리**:
1. **K8s Capacity Planner**
   - Prometheus 메트릭 기반 리소스 최적화
   - P90/P95 백분위수 분석
   - 비용 절감 리포트

2. **K8s Resource Rightsizer**
   - 파드 리소스 사용량 히스토그램
   - YAML 패치 자동 생성
   - 7일/30일 기간 분석

**Security 카테고리**:
1. **IaC Policy Guard**
   - Terraform 보안 스캔
   - 하드코딩된 시크릿 탐지
   - SARIF 포맷 지원

2. **Log Masker Agent**
   - 실시간 로그 감시
   - 민감 정보 마스킹
   - Slack/Webhook 알림

3. **Container Log Secret Guard**
   - Docker 로그 스트리밍
   - API 키/비밀번호/JWT 탐지
   - 보안 사이드카

### 5.2 AI 주제 생성 사용법

```bash
# AI 주제 생성기 실행
python3 ai_topic_generator.py

# 카테고리 선택
1. DevOps (Docker, K8s, CI/CD)
2. Security (취약점, 스캐너)
3. Utility (유틸리티, 변환기)
4. 전체

# 생성할 개수 입력 (기본값: 3)

# 데이터베이스에 자동 추가 (SQLite + Notion)
```

---

## 6. 사용 방법

### 6.1 새 프로젝트 추가

```bash
# 방법 1: AI가 주제 생성
python3 ai_topic_generator.py

# 방법 2: 수동 주제 추가
python3 -m modules.builder.main --action add \
  --name "프로젝트명" \
  --description "설명"
```

### 6.2 전체 파이프라인 실행

```bash
# Planning 상태 프로젝트 자동 생성
python3 -m modules.builder.main --action run

# 키워드 필터링
python3 -m modules.builder.main --action run --keywords docker security
```

### 6.3 프로젝트 목록 조회

```bash
# 전체 목록
python3 -m modules.builder.main --action list

# 상태 필터링
python3 -m modules.builder.main --action list --status "Planning"
```

### 6.4 프로젝트 생성 예시 (File Converter)

```bash
# 1. 프로젝트 생성 스크립트 실행
python3 generate_file_converter.py

# 2. 생성된 프로젝트 경로
cd "Project/File Converter"

# 3. 가상 환경 설정
python3 -m venv venv
source venv/bin/activate

# 4. 의존성 설치
pip install -r requirements.txt

# 5. 실행
python src/main.py
```

---

## 7. 기술 스택

### 7.1 백엔드

| 기술 | 용도 | 버전 |
|------|------|------|
| Python | 주요 언어 | 3.11+ |
| GLM-4.7 | LLM 코드/주제 생성 | - |
| SQLite | 로컬 DB | 3.x |
| Notion API | 클라우드 DB | 2022-06-28 |

### 7.2 도구 라이브러리

| 라이브러리 | 용도 |
|-----------|------|
| pytest | 단위 테스트 |
| GitPython | Git 자동화 |
| requests | HTTP 요청 |
| CustomTkinter | GUI (프로젝트용) |

---

## 8. 환경 설정

### 8.1 필수 환경 변수

```bash
# .env 파일
GLM_API_KEY=<your-glm-api-key>
GLM_BASE_URL=https://api.z.ai/api/coding/paas/v4/
GLM_MODEL=glm-4.7

NOTION_API_KEY=<your-notion-api-key>
PROJECT_DATABASE_ID=<your-notion-db-id>

GITHUB_TOKEN=<your-github-token>
```

### 8.2 데이터베이스 경로

```
OpenClaw/
├── .env                              # 환경 변수
├── database/
│   └── history.db                    # SQLite DB
└── modules/builder/
    ├── planner.py                    # SQLite 관리
    └── planner_notion.py             # Notion 관리
```

---

## 9. 향후 계획

### 9.1 단기 계획 (1-2주)

- [ ] **주기적 실행 기능**: cron/데몬으로 자동화
- [ ] **웹 대시보드**: 프로젝트 현황 시각화
- [ ] **Slack 알림**: 생성 완료 시 알림 발송

### 9.2 중기 계획 (1-2개월)

- [ ] **CI/CD 통합**: Jenkins/GitLab CI 지원
- [ ] **다중 LLM 지원**: GPT-4, Claude 추가
- [ ] **프로젝트 템플릿 다양화**: FastAPI, Streamlit 등

### 9.3 장기 계획 (3-6개월)

- [ ] **AI 에이전트 간 협업**: Intelligence Agent와 연동
- [ ] **프로젝트 추천 시스템**: 사용자 패턴 학습
- [ ] **자동 문서화**: API 문서, 아키텍처 다이어그램 생성

---

## 10. 이슈 및 해결 방안

### 10.1 현재 이슈

| 이슈 | 영향 | 해결 방안 |
|------|------|-----------|
| Notion URL 필드 제한 | 설명이 200자로 제한됨 | 별도 description 필드 활용 |
| GLM API Timeout | 대량 생성 시 지연 | 재시도 로직 강화 |
| GitHub Token 만료 | 배포 실패 | Token 갱신 알림 |

### 10.2 개선 필요 사항

1. **에러 처리**: 각 단계별 롤백 메커니즘
2. **로그 시스템**: 상세한 실행 로그 저장
3. **테스트 커버리지**: 현재 60% → 90% 목표

---

## 11. 연락처

- **프로젝트 위치**: `/Users/nabang/Documents/OpenClaw/modules/builder/`
- **데이터베이스**:
  - SQLite: `database/history.db`
  - Notion: [Database Link](https://notion.so/{database-id})
- **이메일**: uhyang03@gmail.com

---

## 부록

### A. 파일 구조

```
modules/builder/
├── main.py                        # 파이프라인 오케스트레이터
├── planner.py                     # SQLite 주제 관리
├── planner_notion.py              # Notion 주제 관리
├── ai_topic_generator.py          # AI 주제 생성기
├── coder.py                       # 코드 생성기
├── tester.py                      # 자가 수정 테스트
├── git_manager.py                 # Git 자동화
├── import_existing_projects.py    # 기존 프로젝트 DB 등록
├── import_to_notion.py            # Notion 일괄 등록
├── generate_file_converter.py    # 프로젝트 생성 스크립트
├── add_project.py                 # 프로젝트 추가 후 파이프라인
├── docs/
│   └── BUILDER_AGENT_REPORT.md    # 본 보고서
└── Project/                       # 생성된 프로젝트들
```

### B. 실행 예시

```bash
# 전체 파이프라인 실행
cd /Users/nabang/Documents/OpenClaw/modules/builder
python3 -m modules.builder.main --action run

# AI 주제 생성 (DevOps, 3개)
echo -e "1\n3\ny" | python3 ai_topic_generator.py

# 프로젝트 조회
python3 -m modules.builder.main --action list --status "Planning"
```

---

**보고서 끝**
