#!/usr/bin/env python3
"""
Builder Agent - Final Sync (Local Folders <-> Notion)

로컬 프로젝트 폴더를 기준으로 Notion 데이터베이스를 완벽하게 동기화합니다.
- 폴더 O, Notion X -> 추가
- 폴더 X, Notion O -> 삭제 (백로그 제외)
- 정보 불일치 -> 업데이트
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

def normalize_name(name):
    return "".join(c for c in name.lower() if c.isalnum())

def get_git_remote_url(project_path: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=project_path,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except Exception:
        return ""

def archive_page(planner, page_id, name):
    try:
        planner._make_request("PATCH", f"{planner.base_url}/pages/{page_id}", data={"archived": True})
        print(f"🗑️  Archived: {name}")
    except Exception as e:
        print(f"❌ Failed to archive {name}: {e}")

def main():
    print("=" * 80)
    print("🔄 Final Synchronization (Local -> Notion)")
    print("=" * 80)

    try:
        planner = NotionPlanner()
        print("✅ Notion Connected")
    except Exception as e:
        print(f"❌ Notion Connection Failed: {e}")
        return

    # 1. 로컬 폴더 스캔
    projects_dir = config.PROJECTS_DIR
    local_projects = {} # {norm_name: path}
    
    if projects_dir.exists():
        for d in projects_dir.iterdir():
            if d.is_dir() and not d.name.startswith('.'):
                norm = normalize_name(d.name)
                local_projects[norm] = d

    print(f"📂 Local Projects: {len(local_projects)}")

    # 2. Notion 스캔
    notion_projects = planner.get_all_projects()
    notion_map = {} # {norm_name: project}
    
    # 중복된 이름이 Notion에 있으면 문제되므로 체크
    for p in notion_projects:
        norm = normalize_name(p.name)
        if norm in notion_map:
            # 중복 발생 시 - 우선 로컬에 있는 것과 매칭되는지 보고, 아니면 아카이브 대상
            pass 
        notion_map[norm] = p

    print(f"📋 Notion Projects: {len(notion_projects)}")
    print("-" * 80)

    # 3. 동기화 로직
    
    # A. Delete (Notion에만 있는 것 삭제)
    for norm, p in notion_map.items():
        if p.status == "백로그": continue # 백로그 유지
        
        if norm not in local_projects:
            print(f"⚠️  Ghost Found in Notion: {p.name}")
            archive_page(planner, p.id, p.name)

    # B. Add & Update (로컬 기준 순회)
    for norm, path in local_projects.items():
        folder_name = path.name
        git_url = get_git_remote_url(path)
        
        if norm in notion_map:
            # Update
            p = notion_map[norm]
            needs_update = False
            
            if p.status != "게시 완료":
                print(f"🔄 Updating Status for {p.name}: {p.status} -> 게시 완료")
                planner.update_project_status(p.id, "게시 완료")
                needs_update = True
                
            if git_url and p.deployed_url != git_url:
                print(f"🔄 Updating URL for {p.name}: {p.deployed_url} -> {git_url}")
                planner.update_project_url(p.id, git_url)
                needs_update = True
                
            if not needs_update:
                # print(f"✅ In Sync: {p.name}")
                pass
        else:
            # Add
            print(f"➕ Adding Missing Project: {folder_name}")
            try:
                page_id = planner.add_project(
                    name=folder_name,
                    description=git_url if git_url else f"Imported from {folder_name}",
                    status="게시 완료"
                )
                if git_url:
                    planner.update_project_url(page_id, git_url)
            except Exception as e:
                print(f"❌ Failed to add {folder_name}: {e}")

    print("=" * 80)
    print("✅ Final Sync Completed.")

if __name__ == "__main__":
    main()
