#!/usr/bin/env python3
"""
Builder Agent - Import Existing Projects to Notion

Project 폴더의 기존 프로젝트들을 Notion Database로 가져옵니다.
"""

import os
import sys

# 프로젝트 루트 경로 추가
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from planner_notion import NotionPlanner


def import_to_notion():
    """기존 프로젝트들을 Notion Database로 가져옵니다."""

    try:
        planner = NotionPlanner()
    except Exception as e:
        print(f"❌ Notion Planner 초기화 실패: {e}")
        print("   .env 파일에 NOTION_API_KEY와 PROJECT_DATABASE_ID를 확인해주세요.")
        return

    # 기존 프로젝트 목록
    projects = [
        {
            "name": "Text Encoder",
            "description": "81개 변환 알고리즘을 제공하는 확장형 GUI 텍스트 유틸리티 툴. Base64, URL, Hex 인코딩, SHA 해시, 텍스트 처리, Morse/Braille 변환, JWT, 클래식 암호(ROT13, Caesar, Vigenère, Atbash) 등 지원. CustomTkinter 기반 다크 모드 UI, 시스템 트레이, 글로벌 핫키 지원. Python 3.11+, pytest, PyInstaller, GitHub Actions CI/CD 완료.",
            "status": "게시 완료",
            "url": "https://github.com/yourusername/encoder"  # 실제 URL로 변경 필요
        },
        {
            "name": "Google Search Automation",
            "description": "Selenium을 사용한 Google 자동 검색 도구. reCAPTCHA 우회(Buster 확장프로그램), 검색어 목록 자동 처리, 상위 5개 결과 추출 및 저장. Chrome WebDriver 자동화, 쿠키/캐시 삭제, 봇 탐지 회피 기능 포함. Python, Selenium, ChromeDriver 의존.",
            "status": "초안 작성중",
            "url": None
        },
        {
            "name": "Port Security Scanner",
            "description": "다수 웹사이트의 보안 헤더 분석 및 포트 상태 확인 도구. 405 Method Not Allowed 예외 처리, HEAD/GET 요청 자동 전환, CSV 형식 보안 리포트 출력. 45개 국회 관련 웹사이트 대상 HTTPS 리다이렉션 보안 스캔. Python, requests 의존.",
            "status": "초안 작성중",
            "url": None
        },
        {
            "name": "robots.txt Analyzer",
            "description": "robots.txt 파일 자동 분석 및 정보 추출 도구. 로컬 패키지 자동 설치 메커니즘(package-requests/), robots.txt 내용 CSV 형식 저장, URL 리스트 일괄 처리. Python, requests 의존.",
            "status": "초안 작성중",
            "url": None
        },
        {
            "name": "KISA-CIIP-2026",
            "description": "KISA CIIP 가이드라인 기반 취약점 자동 진단 도구. Unix 서버(67개 항목), Windows 서버(64개 항목), 웹서버(26개 항목), DBMS(26개 항목), PC(18개 항목) 총 201개 진단 항목. 플랫폼 자동 감지, JSON+텍스트 이중 결과 출력, 화이트리스트 기반 명령어 검증, 30초 타임아웃, 3회 재시도 로직. TypeScript, Node.js, Bun 기술 스택.",
            "status": "검토중",
            "url": None
        },
        {
            "name": "OpenClaw Builder Agent",
            "description": "자동화된 DevOps 프로젝트 생성 시스템. 주제 선정(Planner) → GLM-4.7 코드 생성(Coder) → 자가 수정 테스트(Tester) → GitHub 배포(GitManager) 파이프라인. SQLite 데이터베이스 기반 주제 관리, 점수 기반 프로젝트 우선순위 선정, Python 구조화된 코드 생성, pytest 단위 테스트, GitHub Actions 자동화.",
            "status": "검토중",
            "url": None
        }
    ]

    print("=" * 80)
    print("📋 Notion Database로 프로젝트 가져오기")
    print("=" * 80)
    print()

    # 이미 등록된 프로젝트 확인
    existing_projects = planner.get_all_projects()
    existing_names = {p.name.lower() for p in existing_projects}

    print(f"이미 등록된 프로젝트: {len(existing_projects)}개")
    for p in existing_projects:
        print(f"  - {p.name} ({p.status})")
    print()

    # 프로젝트 추가
    added_count = 0
    skipped_count = 0
    failed_count = 0

    for project in projects:
        name = project["name"]

        # 중복 체크
        if name.lower() in existing_names:
            print(f"⏭️  건너뜀: {name} (이미 등록됨)")
            skipped_count += 1
            continue

        # 프로젝트 추가
        try:
            # URL이 있으면 URL 필드에, 없으면 description을 URL 필드에
            url_value = project.get("url") or project["description"]

            page_id = planner.add_project(
                name=name,
                description=url_value,
                status=project["status"]
            )

            print(f"✅ 추가 완료: {name} (Page ID: {page_id})")
            added_count += 1

        except Exception as e:
            print(f"❌ 추가 실패: {name} - {e}")
            failed_count += 1

    print()
    print("=" * 80)
    print(f"✅ Notion 가져오기 완료!")
    print(f"   추가: {added_count}개")
    print(f"   건너뜀: {skipped_count}개")
    print(f"   실패: {failed_count}개")
    print(f"   총: {len(projects)}개")
    print("=" * 80)

    # 최종 프로젝트 목록 출력
    print()
    print("📋 Notion 전체 프로젝트 목록:")
    print("-" * 80)
    planner.list_projects()


if __name__ == "__main__":
    import_to_notion()
