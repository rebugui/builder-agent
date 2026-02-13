#!/usr/bin/env python3
"""
Builder Agent - Import GitHub Repositories

GitHub 사용자(rebugui)의 모든 리포지토리를 조회하여
Notion 데이터베이스에 동기화합니다.
"""

import os
import sys
import requests
from pathlib import Path
from collections import defaultdict

# 프로젝트 루트 경로 추가
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parents[1]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from planner_notion import NotionPlanner

GITHUB_USERNAME = "rebugui"

def get_all_github_repos(username):
    """GitHub 유저의 모든 리포지토리 조회 (Pagination 지원)"""
    repos = []
    page = 1
    base_url = f"https://api.github.com/users/{username}/repos"
    
    print(f"📡 Fetching repositories for user: {username}...")
    
    while True:
        try:
            # per_page=100 (최대)
            url = f"{base_url}?page={page}&per_page=100"
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            
            data = resp.json()
            if not data:
                break
                
            repos.extend(data)
            print(f"   - Page {page}: Found {len(data)} repos")
            page += 1
            
        except Exception as e:
            print(f"❌ GitHub API Error: {e}")
            break
            
    return repos

def normalize_name(name):
    """이름 정규화"""
    return "".join(c for c in name.lower() if c.isalnum())

def main():
    print("=" * 80)
    print("🐙 GitHub Repository Syncer")
    print("=" * 80)

    # 1. Notion 연결
    try:
        planner = NotionPlanner()
        print("✅ Notion Connected")
    except Exception as e:
        print(f"❌ Notion Connection Failed: {e}")
        return

    # 2. Notion 프로젝트 로드
    notion_projects = planner.get_all_projects()
    notion_map = {normalize_name(p.name): p for p in notion_projects}
    print(f"📋 Existing Notion Projects: {len(notion_projects)}")

    # 3. GitHub 리포지토리 로드
    github_repos = get_all_github_repos(GITHUB_USERNAME)
    print(f"📦 Total GitHub Repos: {len(github_repos)}")
    print("-" * 80)

    added_count = 0
    updated_count = 0
    skipped_count = 0

    for repo in github_repos:
        repo_name = repo['name']
        repo_url = repo['html_url']
        repo_desc = repo['description'] or f"Imported from GitHub: {repo_name}"
        
        # 정규화된 이름으로 비교
        norm_name = normalize_name(repo_name)
        
        if norm_name in notion_map:
            # 이미 존재함 -> URL 체크
            project = notion_map[norm_name]
            if not project.deployed_url:
                print(f"🔄 Updating URL for '{project.name}': {repo_url}")
                planner.update_project_url(project.id, repo_url)
                # 상태가 '게시 완료'가 아니면 업데이트
                if project.status != "게시 완료":
                     planner.update_project_status(project.id, "게시 완료")
                updated_count += 1
            else:
                # URL도 있고 존재도 함 -> 스킵
                # print(f"⏭️  Skipped: {repo_name} (Already synced)")
                skipped_count += 1
        else:
            # 존재하지 않음 -> 추가
            print(f"➕ Adding new project: {repo_name}")
            try:
                # add_project에는 URL 인자가 따로 없으므로(이전 수정본 기준),
                # 추가 후 update_project_url을 호출해야 함.
                # 또는 description이 URL 역할을 하기도 했음.
                
                # 1. 프로젝트 생성 (설명은 description에)
                page_id = planner.add_project(
                    name=repo_name,
                    description=repo_desc,
                    status="게시 완료"
                )
                
                # 2. URL 필드 업데이트 (명시적)
                planner.update_project_url(page_id, repo_url)
                added_count += 1
                
            except Exception as e:
                print(f"❌ Failed to add {repo_name}: {e}")

    print("=" * 80)
    print(f"✅ Sync Completed!")
    print(f"   ➕ Added: {added_count}")
    print(f"   🔄 Updated: {updated_count}")
    print(f"   ⏭️  Skipped: {skipped_count}")
    print("=" * 80)

if __name__ == "__main__":
    main()
