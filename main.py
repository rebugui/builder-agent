#!/usr/bin/env python3
"""
Builder Agent v3 - Main Entry Point
Automated software development with ChatDev 2.0 and GLM-5
"""
import os
import sys
import asyncio
import argparse
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

# 현재 디렉토리를 sys.path에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# .env 파일 로드
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

from discoverer.topic_discoverer import TopicDiscoverer
from orchestrator.chatdev_client import ChatDevClient
from publisher.github_publisher import GitHubPublisher
from models.idea import ProjectIdea, IdeaSource, ProjectType, Priority
from scheduler.scheduler import BuilderScheduler


def print_banner():
    """배너 출력"""
    print("\n" + "="*60)
    print("🏗️  Builder Agent v3 - Automated Software Development")
    print("="*60)
    print("   Powered by ChatDev 2.0 + GLM-5")
    print("   Repository: github.com/rebugui")
    print("="*60 + "\n")


def check_environment():
    """환경 변수 확인"""
    print("🔍 Checking environment...\n")
    
    issues = []
    
    # ChatDev 2.0
    chatdev_client = ChatDevClient()
    if chatdev_client.health_check():
        print("   ✅ ChatDev 2.0: Running")
    else:
        print("   ❌ ChatDev 2.0: Not running")
        print("      Start: cd chatdev-v2 && python server_main.py --port 6400")
        issues.append("chatdev")
    
    # GitHub Token
    github_token = os.getenv("GITHUB_TOKEN")
    if github_token:
        print("   ✅ GITHUB_TOKEN: Configured")
    else:
        print("   ❌ GITHUB_TOKEN: Not set")
        print("      Set: export GITHUB_TOKEN=your_token_here")
        issues.append("github_token")
    
    # GLM API
    glm_api_key = os.getenv("API_KEY")
    if glm_api_key:
        print("   ✅ GLM API: Configured")
    else:
        print("   ❌ GLM API: Not set")
        print("      Set: export API_KEY=your_glm_key")
        issues.append("glm_api")
    
    print()
    
    return len(issues) == 0, issues


def discover_ideas(limit: int = 10):
    """아이디어 발굴"""
    print_banner()
    print(f"📌 Discovering {limit} project ideas...\n")
    
    discoverer = TopicDiscoverer()
    ideas = discoverer.discover(limit=limit)
    
    for i, idea in enumerate(ideas, 1):
        print(f"{i}. {idea.name}")
        print(f"   Type: {idea.project_type.value}")
        print(f"   Source: {idea.source.value}")
        print(f"   Priority: {idea.priority.name}")
        print(f"   Description: {idea.description}")
        print()


async def develop_idea(name: str, description: str, project_type: str = "cli_app"):
    """아이디어 개발"""
    print_banner()
    
    # 환경 확인
    ok, issues = check_environment()
    if not ok:
        print(f"❌ Environment check failed: {', '.join(issues)}")
        return
    
    # 아이디어 생성
    idea = ProjectIdea(
        name=name,
        description=description,
        source=IdeaSource.MANUAL,
        project_type=ProjectType(project_type),
        priority=Priority.MEDIUM,
        requirements=["Clean code", "Documentation", "Error handling"],
        technical_stack=["Python", "Click", "Rich"]
    )
    
    print(f"📌 Developing: {idea.name}")
    print(f"   Description: {idea.description}\n")
    
    # 개발 진행
    client = ChatDevClient()
    result = await client.develop_project(idea)
    
    if not result.success:
        print(f"❌ Development failed: {result.error}")
        return
    
    print(f"✅ Development completed!")
    print(f"   Files: {len(result.files)}")
    print(f"   Time: {result.execution_time:.1f}s\n")
    
    # GitHub 게시
    print("📌 Publishing to GitHub...")
    publisher = GitHubPublisher()
    published = publisher.publish(result)
    
    print(f"✅ Published successfully!")
    print(f"   URL: {published.github_url}\n")


def start_scheduler():
    """스케줄러 시작"""
    print_banner()
    
    # 환경 확인
    ok, issues = check_environment()
    if not ok:
        print(f"⚠️ Environment issues: {', '.join(issues)}")
        print("   Some features may not work\n")
    
    scheduler = BuilderScheduler()
    scheduler.start()


def main():
    """메인 진입점"""
    parser = argparse.ArgumentParser(
        description="Builder Agent v3 - Automated Software Development",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Discover project ideas
  python main.py discover --limit 10

  # Develop a specific project
  python main.py develop --name my-tool --description "A useful tool"

  # Start scheduler (automated daily development)
  python main.py scheduler

  # Run once (for testing)
  python main.py scheduler --once

  # Check environment
  python main.py check
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # discover 명령
    discover_parser = subparsers.add_parser("discover", help="Discover project ideas")
    discover_parser.add_argument("--limit", type=int, default=10, help="Number of ideas to discover")
    
    # develop 명령
    develop_parser = subparsers.add_parser("develop", help="Develop a project")
    develop_parser.add_argument("--name", required=True, help="Project name")
    develop_parser.add_argument("--description", required=True, help="Project description")
    develop_parser.add_argument("--type", default="cli_app", help="Project type")
    
    # scheduler 명령
    scheduler_parser = subparsers.add_parser("scheduler", help="Start scheduler")
    scheduler_parser.add_argument("--once", action="store_true", help="Run once (for testing)")
    scheduler_parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    
    # check 명령
    check_parser = subparsers.add_parser("check", help="Check environment")
    
    args = parser.parse_args()
    
    if args.command == "discover":
        discover_ideas(limit=args.limit)
    
    elif args.command == "develop":
        asyncio.run(develop_idea(
            name=args.name,
            description=args.description,
            project_type=args.type
        ))
    
    elif args.command == "scheduler":
        if args.once:
            from scheduler.scheduler import run_once
            asyncio.run(run_once())
        else:
            start_scheduler()
    
    elif args.command == "check":
        print_banner()
        check_environment()
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
