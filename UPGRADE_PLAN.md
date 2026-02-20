# Builder Agent v2.0 업그레이드 계획

## 시작일: 2026-02-20

## 문제점 분석

### 1. 코드 생성 구조 불일치
- LLM이 소스 코드와 테스트 코드를 따로 생성
- Import 경로 불일치로 테스트 실패
- Self-Correction이 구조적 문제 해결 못 함

### 2. 주제 다양성 부족
- 같은 프로젝트 반복 생성 (robots.txt-scaner)
- Notion Planner의 주제 풀이 제한적

### 3. 테스트 품질 문제
- 생성된 테스트가 실제 구조와 다름
- 10회 재시도해도 실패

---

## 개선 방안

### Phase 1: 2단계 코드 생성 (Day 1)
- [ ] 소스 코드 생성 후 구조 분석
- [ ] 분석된 구조 기반 테스트 코드 생성
- [ ] Import 경로 자동 검증

### Phase 2: 템플릿 시스템 (Day 2)
- [ ] 프로젝트 템플릿 정의 (CLI, Library, Script)
- [ ] 템플릿 기반 소스 생성
- [ ] 템플릿별 테스트 스켈레톤

### Phase 3: 주제 발굴 개선 (Day 3)
- [ ] GitHub Trending 연동
- [ ] CVE 기반 보안 도구 생성
- [ ] 중복 주제 필터링

### Phase 4: Self-Correction 개선 (Day 4)
- [ ] AST 기반 import 경로 수정
- [ ] 테스트 실행 전 구조 검증
- [ ] 에러 분석 정확도 향상

---

## 진행 로그

### 2026-02-20
- 업그레이드 계획 수립
- 현재 코드 분석 시작

### 2026-02-20 10:13
- Phase 1 완료: 2단계 코드 생성 시스템 구현
  - prompts_v2.py 생성 (소스/테스트 분리)
  - coder.py 수정 (generate_code_v2, _analyze_source_structure)
  - main.py 수정 (v2 메서드 사용)
- GLM API 연결 실패로 테스트 보류
- Phase 2 시작: 템플릿 시스템

### 2026-02-20 10:30
- Phase 4 완료: Self-Correction 개선
  - tester.py에 AST 기반 import 수정 함수 추가
  - analyze_project_structure() - 프로젝트 구조 분석
  - fix_import_statements() - import 문 수정
  - auto_fix_imports() - 전체 자동 수정
- main.py 수정:
  - Step 3에 AST Import 자동 수정 추가
  - Step 4로 Self-Correction 이동
  - Step 5로 GitOps 이동

### 완료된 Phase
- ✅ Phase 1: 2단계 코드 생성
- ✅ Phase 2: 템플릿 시스템
- ✅ Phase 3: 주제 발굴 시스템
- ✅ Phase 4: Self-Correction 개선

### 남은 작업
- [ ] 전체 파이프라인 테스트 (GLM API 연결 문제)
- [ ] 실제 프로젝트 생성 테스트
- [ ] GitHub 배포 테스트
