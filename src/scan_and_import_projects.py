#!/usr/bin/env python3
"""
Builder Agent - Import Local Projects to Notion

'builder/projects/' 폴더에 있는 기존 프로젝트들을 스캔하여
Notion 데이터베이스에 자동으로 등록합니다.
"""

import os
import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parents[1]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from modules.builder.planner_notion import NotionPlanner
from modules.builder.builder_config import config

def get_project_description(project_path: Path) -> str:
    """README.md 등에서 프로젝트 설명을 추출합니다."""
    readme_path = project_path / 'README.md'
    if readme_path.exists():
        try:
            with open(readme_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # 첫 번째 # 헤더 건너뛰고 본문 내용 찾기 (간단히)
                lines = content.split('\n')
                desc_lines = []
                for line in lines:
                    line = line.strip()
                    if not line: continue
                    if line.startswith('#'): continue # 헤더 스킵
                    desc_lines.append(line)
                    if len(desc_lines) >= 3: break # 3줄 정도만 읽음
                
                if desc_lines:
                    return ' '.join(desc_lines)[:200] # 200자 제한
        except Exception:
            pass
    
    return f"Imported from local folder: {project_path.name}"

def main():
    print("=" * 80)
    print("📂 Local Projects Importer")
    print("=" * 80)

    # 1. Notion Planner 초기화
    try:
        planner = NotionPlanner()
        print("✅ Notion Connected")
    except Exception as e:
        print(f"❌ Notion Connection Failed: {e}")
        return

    # 2. 로컬 프로젝트 스캔
    projects_dir = config.PROJECTS_DIR
    if not projects_dir.exists():
        print(f"❌ Projects directory not found: {projects_dir}")
        return

    local_projects = [d for d in projects_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
    print(f"🔍 Found {len(local_projects)} local folders in {projects_dir}")

    # 3. Notion 기존 프로젝트 조회
    notion_projects = planner.get_all_projects()
    existing_names = {p.name.lower(): p for p in notion_projects}
    
    # 4. 동기화
    for local_p in local_projects:
        name = local_p.name
        # 이름 정규화 (폴더명이 소문자/케밥케이스일 수 있으므로 유연하게 비교하고 싶지만, 일단 정확한 매칭 시도)
        # 단, 기존 'import_to_notion.py'에서 등록한 이름과 폴더명이 다를 수 있음.
        # 예: 폴더 'encoder' <-> Notion 'Text Encoder'
        # 이를 위해 간단한 매핑이나 검색을 할 수도 있지만, 여기서는 폴더명 기반으로 신규 등록 시도.
        
        if name.lower() in existing_names:
            print(f"⏭️  Skipped (Already exists): {name}")
            continue
            
        # 설명 추출
        description = get_project_description(local_p)
        
        # Notion에 추가
        print(f"➕ Adding project: {name}...")
        try:
            planner.add_project(
                name=name,
                description=description,
                status="게시 완료"  # 이미 로컬에 있으므로 완료된 것으로 간주
            )
        except Exception as e:
            print(f"   ❌ Failed: {e}")

    print("\\n✅ Import process completed.")

if __name__ == "__main__":
    main()
