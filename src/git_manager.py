#!/usr/bin/env python3
"""
Builder Agent - Git Manager (GitHub API 통합)

GitHub API를 사용하여 저장소를 생성하고 코드를 push합니다.
"""

import os
import subprocess
import tempfile
import shutil
import sys
from typing import Optional, Dict, List
from dataclasses import dataclass
from pathlib import Path

# Add project root to sys.path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parents[1]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from modules.builder.builder_config import config
from modules.builder.utils.logger import setup_logger

logger = setup_logger("GitManager")

try:
    from github import Github
    from github.Repository import Repository
except ImportError:
    logger.error("PyGithub가 설치되지 않았습니다.")
    logger.error("설치 명령: pip3 install PyGithub")
    Github = None
    Repository = None


@dataclass
class RepoInfo:
    """저장소 정보 데이터 클래스"""
    name: str
    url: str
    clone_url: str
    description: str
    created: bool


class GitManager:
    """Git Manager (GitHub 통합)"""

    def __init__(self, github_token: str = None):
        """초기화"""
        # GitHub 토큰 로드
        if github_token is None:
            github_token = config.GITHUB_TOKEN

        if not github_token:
            logger.error("GITHUB_TOKEN 환경변수가 설정되지 않았습니다.")
            raise ValueError("GITHUB_TOKEN required.")

        self.github_token = github_token

        if not Github:
            raise ImportError("PyGithub not installed.")

        # GitHub API 클라이언트 초기화
        self.github = Github(github_token)

        # GitHub 사용자 정보 확인
        try:
            self.user = self.github.get_user()
            logger.info(f"GitHub 인증 완료: {self.user.login}")
        except Exception as e:
            logger.error(f"GitHub 인증 실패: {str(e)}")
            raise ValueError(f"GitHub authentication failed: {str(e)}")

        self.default_org = None  # 기본 조직 (선택사항)

    def create_repo(
        self,
        repo_name: str,
        description: str = "",
        private: bool = False,
        auto_init: bool = False
    ) -> RepoInfo:
        """GitHub 저장소 생성"""
        logger.info(f"Creating GitHub repository: {repo_name}")

        try:
            # 저장소 생성
            repo = self.user.create_repo(
                name=repo_name,
                description=description,
                private=private,
                auto_init=auto_init
            )

            repo_info = RepoInfo(
                name=repo_name,
                url=repo.html_url,
                clone_url=repo.clone_url,
                description=description,
                created=True
            )

            logger.info(f"Repository created! URL: {repo_info.url}")
            return repo_info

        except Exception as e:
            logger.error(f"Failed to create repository: {str(e)}")
            return RepoInfo(
                name=repo_name,
                url="",
                clone_url="",
                description=description,
                created=False
            )

    def push_code(
        self,
        project_dir: str,
        repo_url: str,
        commit_message: str = "Initial commit",
        branch: str = "main"
    ) -> bool:
        """로컬 프로젝트를 GitHub 저장소로 push"""
        logger.info(f"Pushing code to GitHub...")

        try:
            # 1. Git 초기화
            subprocess.run(['git', 'init'], cwd=project_dir, capture_output=True, check=True)

            # 2. Remote 추가
            auth_url = repo_url.replace('https://github.com/', f'https://{self.github_token}@github.com/')
            
            # Check if remote exists
            remotes = subprocess.run(['git', 'remote'], cwd=project_dir, capture_output=True, text=True).stdout
            if 'origin' in remotes:
                 subprocess.run(['git', 'remote', 'set-url', 'origin', auth_url], cwd=project_dir, capture_output=True, check=True)
            else:
                 subprocess.run(['git', 'remote', 'add', 'origin', auth_url], cwd=project_dir, capture_output=True, check=True)

            # 3. 모든 파일 추가
            subprocess.run(['git', 'add', '-A'], cwd=project_dir, capture_output=True, check=True)

            # 4. 커밋
            subprocess.run(['git', 'commit', '-m', commit_message], cwd=project_dir, capture_output=True, check=True)

            # 5. 브랜치 이름 변경 (main)
            subprocess.run(['git', 'branch', '-M', branch], cwd=project_dir, capture_output=True, check=True)

            # 6. Push
            subprocess.run(['git', 'push', '-u', 'origin', branch], cwd=project_dir, capture_output=True, check=True)

            logger.info(f"Code pushed successfully! URL: {repo_url}")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Git command failed: {' '.join(e.cmd)}")
            logger.error(f"Error: {e.stderr.decode('utf-8') if e.stderr else 'Unknown error'}")
            return False
        except Exception as e:
            logger.error(f"Push failed: {str(e)}")
            return False

    def create_release(
        self,
        repo_name: str,
        tag_name: str,
        title: str,
        description: str = ""
    ) -> bool:
        """GitHub 릴리즈 생성"""
        logger.info(f"Creating GitHub release: {tag_name}")

        try:
            repo = self.user.get_repo(repo_name)
            repo.create_git_release(
                tag=tag_name,
                name=title,
                message=description,
                draft=False,
                prerelease=False
            )
            logger.info(f"Release created! Tag: {tag_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to create release: {str(e)}")
            return False

    def list_repos(self) -> List[str]:
        """사용자의 모든 저장소 목록 반환"""
        repos = []
        try:
            for repo in self.user.get_repos():
                repos.append(repo.name)
        except Exception as e:
            logger.error(f"Failed to list repositories: {str(e)}")
        return repos

    def delete_repo(self, repo_name: str) -> bool:
        """저장소 삭제"""
        logger.info(f"Deleting repository: {repo_name}")

        try:
            repo = self.user.get_repo(repo_name)
            repo.delete()
            logger.info(f"Repository deleted!")
            return True
        except Exception as e:
            logger.error(f"Failed to delete repository: {str(e)}")
            return False

if __name__ == "__main__":
    pass