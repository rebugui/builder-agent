#!/usr/bin/env python3
"""
Builder Agent - Deduplicate Notion Projects

Notion 데이터베이스에서 중복된 프로젝트를 찾아 정리(Archive)합니다.
"""

import os
import sys
from pathlib import Path
from collections import defaultdict

# 프로젝트 루트 경로 추가
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parents[1]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from modules.builder.planner_notion import NotionPlanner

def normalize_name(name):
    """이름 정규화 (소문자, 공백/특수문자 제거)"""
    return "".join(c for c in name.lower() if c.isalnum())

def archive_page(planner, page_id, name):
    """페이지 아카이브(삭제)"""
    url = f"{planner.base_url}/pages/{page_id}"
    try:
        planner._make_request("PATCH", url, data={"archived": True})
        print(f"🗑️  Archived (Deleted): {name} ({page_id})")
    except Exception as e:
        print(f"❌ Failed to archive {name}: {e}")

def main():
    print("=" * 80)
    print("🧹 Notion Project Deduplicator")
    print("=" * 80)

    try:
        planner = NotionPlanner()
    except Exception:
        print("❌ Notion connection failed.")
        return

    projects = planner.get_all_projects()
    print(f"📋 Total projects: {len(projects)}")

    # 그룹화 (Normalized Name 기준)
    grouped = defaultdict(list)
    for p in projects:
        norm = normalize_name(p.name)
        grouped[norm].append(p)

    # 중복 처리
    deleted_count = 0
    
    for norm_name, p_list in grouped.items():
        if len(p_list) > 1:
            print(f"\\n🔍 Found duplicates for '{norm_name}':")
            # 정렬: 생성 시간 역순 (최신이 먼저 옴) -> 보통 오래된 것(먼저 만든 것)을 원본으로 침?
            # 아니면 설명이 더 긴 것을 원본으로?
            
            # 전략: 설명이 가장 긴 것을 유지 (정보가 많으므로)
            p_list.sort(key=lambda x: len(x.description or ""), reverse=True)
            
            keeper = p_list[0]
            duplicates = p_list[1:]
            
            print(f"   ✅ Keeping: {keeper.name} (Desc len: {len(keeper.description or '')})")
            
            for dup in duplicates:
                print(f"   ❌ Deleting duplicate: {dup.name} (Desc len: {len(dup.description or '')})")
                archive_page(planner, dup.id, dup.name)
                deleted_count += 1
    
    # 유사 이름 처리 (예: "Google Search" vs "Google Search Automation")
    # 이건 너무 위험할 수 있으니 위 단계(완전/정규화 일치)만 수행합니다.
    # 사용자가 언급한 'encoder' vs 'Text Encoder'는 normalize해도 다름 ('encoder' vs 'textencoder').
    # 따라서 수동 매핑 리스트를 추가합니다.
    
    manual_duplicates = [
        ("textencoder", "encoder"),
        ("googlesearchautomation", "googlesearch"),
        ("robots.txtanalyzer", "robots.txtsearch"),
        ("portsecurityscanner", "portsecurity")
    ]
    
    # 다시 목록 갱신 (삭제된 것 제외해야 하지만, 일단 단순화를 위해 기존 목록에서 찾음 - 이미 삭제된건 에러나거나 무시됨)
    # 하지만 위에서 archived된건 planner 객체 상엔 남아있으니 주의.
    
    projects_map = {normalize_name(p.name): p for p in projects} # 덮어써짐 주의.
    # 안전하게 다시 조회하는게 나을 수도 있지만 API 호출 줄이기 위해.
    
    print("\\n🔍 Checking for similar names...")
    
    for long_name, short_name in manual_duplicates:
        # 둘 다 존재해야 비교 가능
        # projects 리스트를 순회하며 찾기
        long_p = next((p for p in projects if normalize_name(p.name) == long_name), None)
        short_p = next((p for p in projects if normalize_name(p.name) == short_name), None)
        
        if long_p and short_p:
            # 둘 다 살아있다면 (위에서 삭제 안됐다면)
            # 보통 긴 이름이 더 멋진 이름이고, 짧은건 폴더명.
            # 하지만 짧은게 방금 폴더에서 가져온거라 '연동' 측면에서 더 나을 수도?
            # 아니, 사용자는 "도구들을 옮겨뒀다" 했으니 폴더명(짧은거)이 현재 실체임.
            # 그러나 Notion에는 'Text Encoder'처럼 예쁜 이름으로 관리하고 싶을 것.
            # -> 긴 이름을 남기고, 짧은(폴더명) 프로젝트는 삭제하되,
            # (중요) 긴 이름 프로젝트의 URL/설명에 폴더 정보를 업데이트해주는게 베스트.
            # 여기선 단순 삭제 요청이므로 삭제만 합니다.
            
            print(f"   Found pair: '{long_p.name}' vs '{short_p.name}'")
            print(f"   ❌ Deleting shorter/folder name: {short_p.name}")
            archive_page(planner, short_p.id, short_p.name)
            deleted_count += 1

    print(f"\\n✅ Cleanup completed. Deleted {deleted_count} projects.")

if __name__ == "__main__":
    main()
