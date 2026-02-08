#!/usr/bin/env python3
"""
Builder Agent - Check Git Status & Update Notion

로컬 프로젝트 폴더에 .git이 존재하면,
Notion 상태를 '게시 완료'로 변경하고 GitHub URL을 업데이트합니다.
"""

import os
import sys
import subprocess
from pathlib import Path

# 프로젝트 루트 경로 추가
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parents[1]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from modules.builder.planner_notion import NotionPlanner
from modules.builder.builder_config import config

def get_git_remote_url(project_path: Path) -> str:
    """Git Remote Origin URL을 가져옵니다."""
    try:
        # git remote get-url origin
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=project_path,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except Exception:
        return None

def normalize_name(name):
    """이름 정규화 (소문자, 공백제거)"""
    return "".join(c for c in name.lower() if c.isalnum())

def main():
    print("=" * 80)
    print("🔄 Git Status Synchronizer")
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
    print(f"🔍 Found {len(local_projects)} local folders.")

    # 3. Notion 프로젝트 로드
    notion_projects = planner.get_all_projects()
    # 매칭을 위해 {정규화된이름: 프로젝트객체} 맵 생성
    notion_map = {normalize_name(p.name): p for p in notion_projects}
    
    # 추가 매핑 (폴더명 <-> Notion이름)
    manual_map = {
        "encoder": "textencoder",
        # 필요 시 추가
    }

    updated_count = 0

    for local_p in local_projects:
        folder_name = local_p.name
        
        # .git 확인
        if not (local_p / ".git").exists():
            print(f"⚪️ {folder_name}: No .git found. Skipping.")
            continue

        # URL 추출
        remote_url = get_git_remote_url(local_p)
        if not remote_url:
            print(f"⚠️  {folder_name}: Has .git but no remote origin URL.")
            # URL 없어도 '게시 완료'로 바꿀지는 선택 사항. 
            # 보통 로컬 커밋만 있고 푸시 안 된 상태일 수 있음. -> URL 없으면 업데이트 안 함.
            continue

        # Notion 프로젝트 찾기
        norm_name = normalize_name(folder_name)
        # 매뉴얼 매핑 확인
        if norm_name in manual_map:
            norm_name = manual_map[norm_name]
            
        notion_p = notion_map.get(norm_name)
        
        if not notion_p:
            print(f"⚠️  {folder_name}: Not found in Notion (mapped to '{norm_name}').")
            continue

        print(f"✅ {folder_name} (Notion: {notion_p.name})")
        print(f"   - Git Remote: {remote_url}")
        
        # 업데이트 필요 여부 확인
        need_update = False
        
        if notion_p.status != "게시 완료":
            print(f"   - Status: '{notion_p.status}' -> '게시 완료'")
            planner.update_project_status(notion_p.id, "게시 완료")
            need_update = True
            
        if notion_p.deployed_url != remote_url:
            print(f"   - URL: '{notion_p.deployed_url}' -> '{remote_url}'")
            planner.update_project_url(notion_p.id, remote_url)
            need_update = True
            
        if need_update:
            updated_count += 1
        else:
            print("   - Already up to date.")

    print(f"\\n✅ Synchronization completed. Updated {updated_count} projects.")

if __name__ == "__main__":
    main()
