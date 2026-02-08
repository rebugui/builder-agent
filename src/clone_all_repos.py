#!/usr/bin/env python3
"""
Builder Agent - Clone All GitHub Repos

GitHub 사용자(rebugui)의 모든 리포지토리를
'builder/projects/' 폴더에 클론하거나 업데이트합니다.
"""

import os
import sys
import subprocess
import requests
from pathlib import Path

# 프로젝트 루트 경로 추가
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parents[1]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from modules.builder.builder_config import config

GITHUB_USERNAME = "rebugui"

def get_all_github_repos(username):
    """GitHub 유저의 모든 리포지토리 조회"""
    repos = []
    page = 1
    base_url = f"https://api.github.com/users/{username}/repos"
    
    print(f"📡 Fetching repositories for user: {username}...")
    
    while True:
        try:
            url = f"{base_url}?page={page}&per_page=100"
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            
            data = resp.json()
            if not data:
                break
                
            repos.extend(data)
            page += 1
            
        except Exception as e:
            print(f"❌ GitHub API Error: {e}")
            break
            
    return repos

def git_clone_or_pull(repo_url, target_dir):
    """Git Clone 또는 Pull 수행"""
    repo_name = target_dir.name
    
    if target_dir.exists():
        if (target_dir / ".git").exists():
            print(f"🔄 Updating {repo_name}...")
            try:
                subprocess.run(["git", "pull"], cwd=target_dir, check=True, capture_output=True)
                print(f"   ✅ Pulled successfully.")
            except subprocess.CalledProcessError as e:
                print(f"   ❌ Pull failed: {e}")
        else:
            print(f"⚠️  Directory {repo_name} exists but is not a git repo. Skipping.")
    else:
        print(f"⬇️  Cloning {repo_name}...")
        try:
            subprocess.run(["git", "clone", repo_url, str(target_dir)], check=True, capture_output=True)
            print(f"   ✅ Cloned successfully.")
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Clone failed: {e}")

def main():
    print("=" * 80)
    print("📥 GitHub Clone/Pull All")
    print("=" * 80)

    # 1. 프로젝트 디렉토리 확인
    projects_root = config.PROJECTS_DIR
    if not projects_root.exists():
        projects_root.mkdir(parents=True, exist_ok=True)
    
    print(f"📂 Target Directory: {projects_root}")

    # 2. 리포지토리 목록 조회
    repos = get_all_github_repos(GITHUB_USERNAME)
    print(f"📦 Total Repos: {len(repos)}")
    print("-" * 80)

    # 3. 클론/풀 실행
    for repo in repos:
        repo_name = repo['name']
        clone_url = repo['clone_url']
        target_dir = projects_root / repo_name
        
        git_clone_or_pull(clone_url, target_dir)

    print("=" * 80)
    print("✅ All operations completed.")

if __name__ == "__main__":
    main()
