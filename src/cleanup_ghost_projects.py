#!/usr/bin/env python3
"""
Builder Agent - Cleanup Ghost Projects

로컬 폴더(GitHub Clone)에 존재하지 않는 Notion 프로젝트를 정리(Archive)합니다.
단, '백로그' 상태인 프로젝트는 아이디어이므로 유지합니다.
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

def normalize_name(name):
    """이름 정규화"""
    return "".join(c for c in name.lower() if c.isalnum())

def archive_page(planner, page_id, name):
    """페이지 아카이브"""
    url = f"{planner.base_url}/pages/{page_id}"
    try:
        planner._make_request("PATCH", url, data={"archived": True})
        print(f"🗑️  Archived (Deleted): {name}")
        return True
    except Exception as e:
        print(f"❌ Failed to archive {name}: {e}")
        return False

def main():
    print("=" * 80)
    print("👻 Notion Ghost Project Cleanup")
    print("=" * 80)

    try:
        planner = NotionPlanner()
        print("✅ Notion Connected")
    except Exception as e:
        print(f"❌ Notion Connection Failed: {e}")
        return

    # 1. 로컬 프로젝트 목록 (Source of Truth)
    projects_dir = config.PROJECTS_DIR
    local_folders = set()
    if projects_dir.exists():
        for d in projects_dir.iterdir():
            if d.is_dir() and not d.name.startswith('.'):
                local_folders.add(normalize_name(d.name))
    
    print(f"📂 Local Projects (GitHub Clones): {len(local_folders)}")
    
    # 2. Notion 프로젝트 조회
    notion_projects = planner.get_all_projects()
    print(f"📋 Notion Projects: {len(notion_projects)}")
    
    deleted_count = 0
    
    # 매뉴얼 매핑 (Notion 이름 -> 폴더 이름)
    # 예: 'Text Encoder' -> 'textencoder' (normalized)
    # 이미 normalized 비교를 하므로 대부분 커버됨.
    
    for p in notion_projects:
        norm_name = normalize_name(p.name)
        status = p.status
        
        # 1. 백로그는 건드리지 않음 (아이디어 단계)
        if status == "백로그":
            # print(f"🛡️  Kept (Backlog): {p.name}")
            continue
            
        # 2. 로컬에 존재하는지 확인
        if norm_name in local_folders:
            # print(f"✅ Verified: {p.name}")
            continue
            
        # 3. 로컬에 없음 -> 삭제 대상
        # 예외: 만약 GitHub URL이 있는데 로컬에만 없는거라면?
        # -> 사용자가 "프로젝트 폴더 초기화 했어... 거기에 맞춰서 정리해줘"라고 했으므로
        #    폴더에 없는 건 지우는게 맞음. (GitHub에 있어도 clone이 안 된거면 관리 대상 아님)
        #    하지만 GitHub에 있는데 지우는 건 좀 위험할 수 있음.
        #    -> 안전장치: URL이 내 GitHub(rebugui)라면 유지할까?
        #    아니, 아까 clone_all_repos 했으므로 내 GitHub에 있으면 로컬에도 있어야 정상임.
        #    따라서 로컬에 없으면 내 GitHub에도 없는 것(혹은 이름이 다른 것).
        
        print(f"⚠️  Ghost Project Found: {p.name} (Status: {status})")
        print(f"   Reason: Not found in local folder '{projects_dir}'")
        
        if archive_page(planner, p.id, p.name):
            deleted_count += 1

    print("-" * 80)
    print(f"✅ Cleanup Completed. Removed {deleted_count} ghost projects.")
    print("=" * 80)

if __name__ == "__main__":
    main()
