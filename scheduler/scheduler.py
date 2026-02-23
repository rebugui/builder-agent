"""
Scheduler - Builder Agent v3 스케줄링
"""
import os
import sys
import json
import asyncio
from datetime import datetime
from typing import List, Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from discoverer.topic_discoverer import TopicDiscoverer
from orchestrator.chatdev_client import ChatDevClient
from publisher.github_publisher import GitHubPublisher
from models.idea import ProjectIdea, DevelopmentResult, PublishedProject


class BuilderScheduler:
    """Builder Agent v3 스케줄러"""
    
    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        
        # 컴포넌트 초기화
        self.discoverer = TopicDiscoverer(config)
        self.chatdev_client = ChatDevClient(
            base_url=config.get("chatdev_url", "http://localhost:6400")
        )
        self.publisher = GitHubPublisher(config)
        
        # 스케줄러
        self.scheduler = AsyncIOScheduler(timezone="Asia/Seoul")
        
        # 로그 디렉토리
        self.log_dir = "logs"
        os.makedirs(self.log_dir, exist_ok=True)
        
        # 프로젝트 이력
        self.history_file = os.path.join(self.log_dir, "project_history.json")
        self._load_history()
    
    def _load_history(self):
        """프로젝트 이력 로드"""
        if os.path.exists(self.history_file):
            with open(self.history_file, 'r') as f:
                self.history = json.load(f)
        else:
            self.history = {"projects": [], "last_run": None}
    
    def _save_history(self):
        """프로젝트 이력 저장"""
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=2)
    
    def setup_jobs(self):
        """스케줄 작업 설정"""
        # 매일 오전 9시 - 주제 발굴 및 개발
        self.scheduler.add_job(
            self.run_daily_development,
            CronTrigger(hour=9, minute=0, timezone="Asia/Seoul"),
            id="daily_development",
            name="Daily Development",
            replace_existing=True
        )
        
        # 평일 오전 10시 - 평일만 실행
        self.scheduler.add_job(
            self.run_weekday_development,
            CronTrigger(
                day_of_week="mon-fri",
                hour=10,
                minute=0,
                timezone="Asia/Seoul"
            ),
            id="weekday_development",
            name="Weekday Development",
            replace_existing=True
        )
        
        # 매시간 상태 체크
        self.scheduler.add_job(
            self.health_check,
            CronTrigger(hour="*", minute=0, timezone="Asia/Seoul"),
            id="health_check",
            name="Health Check",
            replace_existing=True
        )
        
        print("✅ Scheduler jobs configured:")
        for job in self.scheduler.get_jobs():
            print(f"   - {job.name}: {job.next_run_time}")
    
    async def run_daily_development(self):
        """매일 개발 작업 실행"""
        print(f"\n{'='*60}")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🚀 Daily Development Started")
        print(f"{'='*60}\n")
        
        try:
            # 1. 아이디어 발굴
            print("📌 Step 1: Discovering project ideas...")
            ideas = self.discoverer.discover(limit=1)
            
            if not ideas:
                print("⚠️ No project ideas found")
                return
            
            idea = ideas[0]
            print(f"   Selected: {idea.name}")
            print(f"   Type: {idea.project_type.value}")
            print(f"   Priority: {idea.priority.name}\n")
            
            # 2. 개발 진행
            print(f"📌 Step 2: Developing {idea.name}...")
            result = await self.chatdev_client.develop_project(idea)
            
            if not result.success:
                print(f"❌ Development failed: {result.error}")
                return
            
            print(f"✅ Development completed in {result.execution_time:.1f}s")
            print(f"   Files: {len(result.files)}\n")
            
            # 3. GitHub 게시
            print(f"📌 Step 3: Publishing to GitHub...")
            published = self.publisher.publish(result)
            
            print(f"✅ Published successfully!")
            print(f"   URL: {published.github_url}\n")
            
            # 4. 이력 저장
            self.history["projects"].append({
                "name": idea.name,
                "github_url": published.github_url,
                "created_at": datetime.now().isoformat(),
                "success": True
            })
            self.history["last_run"] = datetime.now().isoformat()
            self._save_history()
            
            print(f"{'='*60}")
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✅ Daily Development Completed")
            print(f"{'='*60}\n")
            
            # TODO: 텔레그램 알림
            # await self.send_telegram_notification(published)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    async def run_weekday_development(self):
        """평일 개발 작업 실행"""
        print(f"\n{'='*60}")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🚀 Weekday Development Started")
        print(f"{'='*60}\n")
        
        await self.run_daily_development()
    
    async def health_check(self):
        """시스템 상태 체크"""
        chatdev_healthy = self.chatdev_client.health_check()
        github_configured = self.publisher.github_token is not None
        
        status = {
            "timestamp": datetime.now().isoformat(),
            "chatdev": "✅" if chatdev_healthy else "❌",
            "github": "✅" if github_configured else "❌"
        }
        
        # 로그 저장
        log_file = os.path.join(self.log_dir, "health_check.log")
        with open(log_file, 'a') as f:
            f.write(json.dumps(status) + "\n")
        
        if not chatdev_healthy or not github_configured:
            print(f"⚠️ Health check failed: {status}")
    
    def start(self):
        """스케줄러 시작"""
        print("\n" + "="*60)
        print("🏗️ Builder Agent v3 - Scheduler")
        print("="*60 + "\n")
        
        # 작업 설정
        self.setup_jobs()
        
        # 스케줄러 시작
        self.scheduler.start()
        
        print("\n✅ Scheduler started")
        print("   Press Ctrl+C to stop\n")
        
        try:
            # 메인 이벤트 루프 유지
            asyncio.get_event_loop().run_forever()
        except (KeyboardInterrupt, SystemExit):
            self.stop()
    
    def stop(self):
        """스케줄러 중지"""
        print("\n⏹️ Stopping scheduler...")
        self.scheduler.shutdown()
        print("✅ Scheduler stopped")


async def run_once():
    """한 번만 실행 (테스트용)"""
    scheduler = BuilderScheduler()
    
    # ChatDev 2.0 상태 확인
    if not scheduler.chatdev_client.health_check():
        print("❌ ChatDev 2.0 server is not running")
        print("   Start it first: cd chatdev-v2 && python server_main.py --port 6400")
        return
    
    # GitHub 토큰 확인
    if not scheduler.publisher.github_token:
        print("❌ GITHUB_TOKEN not set")
        print("   export GITHUB_TOKEN=your_token_here")
        return
    
    print("✅ All checks passed\n")
    await scheduler.run_daily_development()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Builder Agent v3 Scheduler")
    parser.add_argument("--once", action="store_true", help="Run once (for testing)")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    
    args = parser.parse_args()
    
    if args.once:
        asyncio.run(run_once())
    else:
        scheduler = BuilderScheduler()
        scheduler.start()
