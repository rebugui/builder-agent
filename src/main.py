#!/usr/bin/env python3
"""
Builder Agent - Main Orchestrator

빌더 에이전트의 전체 파이프라인을 조율합니다:
Planner → Coder → Tester → GitManager
"""

import os
import sys
from typing import Optional
from pathlib import Path
import argparse
from datetime import datetime

# Add project root to sys.path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parents[1]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from modules.builder.builder_config import config
from modules.builder.utils.logger import setup_logger
# from modules.builder.planner import TopicPlanner, Project  # Local DB Planner
from modules.builder.planner_notion import NotionPlanner  # Notion Planner
from modules.builder.coder import CodeGenerator
from modules.builder.tester import SelfCorrectionTester, TestResult
from modules.builder.git_manager import GitManager, RepoInfo

logger = setup_logger("BuilderAgentMain")

class BuilderAgentMain:
    """Builder Agent Main Orchestrator"""

    # 파이프라인 재시도 상수
    MAX_PIPELINE_RETRIES = 2
    RETRY_DELAY_SECONDS = 60

    def __init__(self, db_path: str = None, github_token: str = None):
        """초기화"""
        # self.planner = TopicPlanner(db_path=db_path)
        try:
            self.planner = NotionPlanner()
            logger.info("✅ Connected to Notion Planner")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Notion: {e}")
            logger.warning("Falling back to local TopicPlanner")
            from modules.builder.planner import TopicPlanner
            self.planner = TopicPlanner(db_path=db_path)

        self.coder = CodeGenerator()
        self.tester = SelfCorrectionTester(coder=self.coder)

        # Lazy init handled by property or just allow passing token to init
        self._git_manager = None
        self._github_token = github_token

        self.projects_dir = config.PROJECTS_DIR
        # Ensure projects dir exists
        self.projects_dir.mkdir(parents=True, exist_ok=True)

    @property
    def git_manager(self) -> GitManager:
        """GitManager 지연 초기화"""
        if self._git_manager is None:
            self._git_manager = GitManager(github_token=self._github_token)
        return self._git_manager

    def _generate_failure_report(self, project, test_result=None, error: str = None) -> str:
        """실패 분석 리포트 생성"""
        report = f"""
{'='*60}
🔴 BUILDER AGENT FAILURE REPORT
{'='*60}

Project: {project.name}
Description: {project.description[:100]}...
Notion ID: {project.id}
Created: {project.created_at}

{'='*60}
FAILURE DETAILS
{'='*60}
"""

        if test_result:
            report += f"""
Error Type: {test_result.error_type or 'Unknown'}
Error Message: {test_result.error_message or 'N/A'}

Return Code: {test_result.return_code}

STDOUT (last 500 chars):
{test_result.stdout[-500:] if test_result.stdout else 'N/A'}

STDERR (last 500 chars):
{test_result.stderr[-500:] if test_result.stderr else 'N/A'}
"""
        if error:
            report += f"\nAdditional Error: {error}\n"

        report += f"\n{'='*60}\nGenerated at: {datetime.now().isoformat()}\n{'='*60}\n"

        # 로그에 출력
        logger.error(report)

        # 파일로도 저장
        try:
            import os
            log_dir = Path(os.path.dirname(os.path.dirname(__file__))) / 'logs'
            log_dir.mkdir(parents=True, exist_ok=True)
            report_file = log_dir / f"failure_{project.name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            report_file.write_text(report, encoding='utf-8')
            logger.info(f"📄 Failure report saved: {report_file}")
        except Exception as e:
            logger.warning(f"Failed to save failure report: {e}")

        return report

    def run_full_pipeline(self, keywords: list = None) -> Optional[str]:
        """전체 파이프라인 실행 (재시도 정책 포함)"""
        logger.info("=" * 60)
        logger.info("🚀 Starting Full Pipeline")
        logger.info("=" * 60)

        # 파이프라인 레벨 재시도 루프
        for pipeline_attempt in range(1, self.MAX_PIPELINE_RETRIES + 1):
            if pipeline_attempt > 1:
                logger.info(f"🔄 Pipeline Retry {pipeline_attempt}/{self.MAX_PIPELINE_RETRIES}")
                import time
                logger.info(f"⏳ Waiting {self.RETRY_DELAY_SECONDS} seconds before retry...")
                time.sleep(self.RETRY_DELAY_SECONDS)

            try:
                # 1. Topic Selection
                logger.info("Step 1: Topic Selection")
                selected_project = self.planner.select_topic(keywords=keywords)

                if not selected_project:
                    logger.warning("No project selected. Terminating pipeline.")
                    return None

                # 첫 시도일 때만 상태를 In Progress로 변경
                if pipeline_attempt == 1:
                    self.planner.update_project_status(selected_project.id, "In Progress")

                project_name = selected_project.name
                project_description = selected_project.description

                # 2. Spec Generation & Code Generation
                logger.info(f"Step 2: Spec & Code Generation for {project_name}")

                # 2-1. Generate Spec
                try:
                    logger.info("Generating Technical Specification...")
                    spec_content = self.coder.generate_spec(project_name, project_description)

                    # Upload Spec to Notion
                    if hasattr(self.planner, 'append_spec_to_page'):
                        self.planner.append_spec_to_page(selected_project.id, spec_content)
                        logger.info("Technical Spec uploaded to Notion.")

                    # Use Spec for Code Generation (Better context)
                    full_description = f"{project_description}\n\n{spec_content}"
                    generated_code = self.coder.generate_code(project_name, full_description)

                    files = self.coder.parse_generated_code(generated_code, project_name)
                    project_dir = self.coder.save_code_to_files(project_name, files, str(self.projects_dir))
                except Exception as e:
                    logger.error(f"Generation failed: {e}")
                    if pipeline_attempt == self.MAX_PIPELINE_RETRIES:
                        self._generate_failure_report(selected_project, error=f"Code Generation: {str(e)}")
                        self.planner.update_project_status(selected_project.id, "Failed")
                        return None
                    continue  # 재시도

                # 3. Self-Correction Loop
                logger.info("Step 3: Self-Correction Loop")
                success, test_result, attempt = self.tester.test_and_fix(
                    project_dir=project_dir,
                    project_name=project_name,
                    max_retries=3
                )

                if not success:
                    logger.error(f"Testing failed after {attempt} attempts.")
                    if pipeline_attempt == self.MAX_PIPELINE_RETRIES:
                        # 마지막 시에서도 실패하면 리포트 생성
                        self._generate_failure_report(selected_project, test_result)
                        self.planner.update_project_status(selected_project.id, "Failed")
                        return None
                    # 재시도
                    logger.warning(f"🔄 Will retry entire pipeline ({pipeline_attempt}/{self.MAX_PIPELINE_RETRIES})")
                    continue

                # 4. GitOps (서브모듈로 생성)
                logger.info("Step 4: GitOps (Creating as Submodule with AGPL-3.0)")
                repo_name = project_name.lower().replace(' ', '-').replace('_', '-')

                # 서브모듈로 생성 (GitHub 저장소 생성 + AGPL-3.0 라이선스 추가 + Push + 메인 리포지토리에 서브모듈 추가)
                repo_info = self.git_manager.create_as_submodule(
                    project_dir=project_dir,
                    repo_name=repo_name,
                    description=project_description,
                    main_repo_projects_dir="modules/builder/projects"
                )

                if not repo_info.created:
                    logger.error("Repository creation failed.")
                    if pipeline_attempt == self.MAX_PIPELINE_RETRIES:
                        self._generate_failure_report(selected_project, error="Git Repository Creation Failed")
                        self.planner.update_project_status(selected_project.id, "Failed")
                        return None
                    continue  # 재시도

                # 릴리즈 생성
                self.git_manager.create_release(
                    repo_name=repo_name,
                    tag_name="v1.0.0",
                    title=f"{project_name} v1.0.0",
                    description=f"{project_name}\n\n{project_description}\n\nLicensed under AGPL-3.0"
                )

                # 5. Status Update
                logger.info("Step 5: Status Update")
                self.planner.update_project_url(selected_project.id, repo_info.url)
                self.planner.update_project_status(selected_project.id, "게시 완료")

                logger.info("=" * 60)
                logger.info("✅ Pipeline Complete!")
                logger.info("=" * 60)
                logger.info(f"Project ID: {selected_project.id}")
                logger.info(f"Project Name: {project_name}")
                logger.info(f"GitHub URL: {repo_info.url}")
                if repo_info.submodule_path:
                    logger.info(f"Submodule Path: {repo_info.submodule_path}")
                logger.info(f"Pipeline Attempts: {pipeline_attempt}/{self.MAX_PIPELINE_RETRIES}")
                logger.info("=" * 60)

                return repo_info.url

            except Exception as e:
                logger.error(f"❌ Pipeline error on attempt {pipeline_attempt}: {str(e)}")
                if pipeline_attempt == self.MAX_PIPELINE_RETRIES:
                    self._generate_failure_report(selected_project, error=f"Pipeline Exception: {str(e)}")
                    self.planner.update_project_status(selected_project.id, "Failed")
                    return None
                # 재시도
                continue

        return None  # 모든 재시도 실패

    def add_new_project(self, name: str, description: str, status: str = '백로그') -> int:
        """새 프로젝트 추가"""
        return self.planner.add_project(name, description, status)

    def list_projects(self, status: str = None):
        """프로젝트 리스트 출력"""
        self.planner.list_projects(status=status)


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="Builder Agent - DevOps Project Generator")
    parser.add_argument('action', choices=['run', 'list', 'add'], default='run', nargs='?', help='Action to perform')
    parser.add_argument('--name', help='Project name (for add)')
    parser.add_argument('--description', help='Project description (for add)')
    parser.add_argument('--status', help='Project status filter (for list)')
    parser.add_argument('--keywords', nargs='+', help='Topic keywords (for run)')

    args = parser.parse_args()

    builder = BuilderAgentMain()

    if args.action == 'run':
        builder.run_full_pipeline(keywords=args.keywords)
    elif args.action == 'list':
        builder.list_projects(status=args.status)
    elif args.action == 'add':
        if not args.name or not args.description:
            print("Error: --name and --description are required for 'add'")
            return
        builder.add_new_project(args.name, args.description)
        
if __name__ == "__main__":
    main()