#!/usr/bin/env python3
"""
프로젝트 추가 후 전체 파이프라인 실행
"""

import os
import sys

# 프로젝트 루트 경로 추가
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from modules.builder.main import BuilderAgentMain

# 프로젝트 정보
project_name = "File Converter"
project_description = """이미지, 문서 파일 형식 변환 도구.

주요 기능:
- 이미지 변환: PNG ↔ JPEG ↔ WEBP ↔ GIF
- 문서 변환: PDF ↔ Word ↔ Markdown ↔ HTML
- 대용량 파일 배치 처리
- 변환 품질/해상도 설정
- 변환 내역 저장 및 관리
- 드래그앤드롭 GUI 지원

기술 스택:
- Python 3.11+
- Pillow (이미지 처리)
- pdf2docx (PDF 변환)
- pandoc (문서 변환)
- CustomTkinter (GUI)
"""

print("=" * 80)
print("🚀 File Converter 프로젝트 생성 시작")
print("=" * 80)
print()

# Builder Agent 초기화
builder = BuilderAgentMain()

# 1. 프로젝트 추가
print("📋 Step 1: 프로젝트 데이터베이스에 추가")
print("-" * 80)
project_id = builder.add_new_project(
    name=project_name,
    description=project_description,
    status="Planning"
)
print(f"✅ 프로젝트 추가 완료 (ID: {project_id})")
print()

# 2. 전체 파이프라인 실행
print("🔨 Step 2: 전체 파이프라인 실행 (코드 생성 → 테스트 → 배포)")
print("-" * 80)
repo_url = builder.run_full_pipeline()

if repo_url:
    print()
    print("=" * 80)
    print("🎉 File Converter 프로젝트 생성 완료!")
    print(f"📦 GitHub: {repo_url}")
    print("=" * 80)
else:
    print()
    print("=" * 80)
    print("⚠️ 파이프라인 실행 중 문제가 발생했습니다.")
    print("=" * 80)
