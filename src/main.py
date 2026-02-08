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

    def run_full_pipeline(self, keywords: list = None) -> Optional[str]:
        """전체 파이프라인 실행"""
        logger.info("Starting Full Pipeline")

        # 1. Topic Selection
        logger.info("Step 1: Topic Selection")
        selected_project = self.planner.select_topic(keywords=keywords)

        if not selected_project:
            logger.warning("No project selected. Terminating pipeline.")
            return None

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
            self.planner.update_project_status(selected_project.id, "Failed")
            return None

        # 3. Self-Correction Loop
        logger.info("Step 3: Self-Correction Loop")
        success, test_result, attempt = self.tester.test_and_fix(
            project_dir=project_dir,
            project_name=project_name,
            max_retries=3
        )

        if not success:
            logger.error("Testing failed. Terminating pipeline.")
            self.planner.update_project_status(selected_project.id, "Failed")
            return None

        # 4. GitOps
        logger.info("Step 4: GitOps")
        repo_name = project_name.lower().replace(' ', '-').replace('_', '-')
        
        repo_info = self.git_manager.create_repo(
            repo_name=repo_name,
            description=project_description
        )

        if not repo_info.created:
            logger.error("Repository creation failed. Terminating pipeline.")
            self.planner.update_project_status(selected_project.id, "Failed")
            return None

        success = self.git_manager.push_code(
            project_dir=project_dir,
            repo_url=repo_info.clone_url,
            commit_message=f"Initial commit: {project_name}"
        )

        if not success:
            logger.error("Code push failed. Terminating pipeline.")
            self.planner.update_project_status(selected_project.id, "Failed")
            return None

        self.git_manager.create_release(
            repo_name=repo_name,
            tag_name="v1.0.0",
            title=f"{project_name} v1.0.0",
            description=f"Initial release of {project_name}\n\n{project_description}"
        )

        # 5. Status Update
        logger.info("Step 5: Status Update")
        self.planner.update_project_url(selected_project.id, repo_info.url)
        self.planner.update_project_status(selected_project.id, "Done")

        logger.info("Pipeline Complete!")
        logger.info(f"Project ID: {selected_project.id}")
        logger.info(f"GitHub URL: {repo_info.url}")
        
        return repo_info.url

    def add_new_project(self, name: str, description: str, status: str = 'Planning') -> int:
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