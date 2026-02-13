#!/usr/bin/env python3
"""
Builder Agent - Git Manager (GitHub API 통합)

GitHub API를 사용하여 저장소를 생성하고 코드를 push합니다.
모든 프로젝트는 OpenClaw 메인 리포지토리의 서브모듈로 관리됩니다.
라이선스: AGPL-3.0
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
project_root = Path(os.getenv("OPENCLAW_ROOT", current_dir.parents[1]))
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from builder_config import config
from utils.logger import setup_logger

logger = setup_logger("GitManager")

# AGPL-3.0 라이선스 텍스트
AGPL_3_0_LICENSE = """GNU AFFERO GENERAL PUBLIC LICENSE
Version 3, 19 November 2007

Copyright (C) 2024 OpenClaw Project

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.

Additional permission under GNU AGPL version 3 section 7:
If you modify this program, or any covered work, by linking or combining
it with other code, the resulting work must be licensed under AGPL-3.0.
"""

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
    submodule_path: Optional[str] = None  # 서브모듈 경로 (메인 리포지토리 내부)


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

    def add_agpl_license(self, project_dir: str) -> bool:
        """프로젝트에 AGPL-3.0 라이선스 파일 추가"""
        logger.info("Adding AGPL-3.0 license...")

        try:
            license_path = Path(project_dir) / 'LICENSE'
            with open(license_path, 'w', encoding='utf-8') as f:
                f.write(AGPL_3_0_LICENSE)

            logger.info(f"✅ AGPL-3.0 license added to {project_dir}")
            return True
        except Exception as e:
            logger.error(f"Failed to add license: {str(e)}")
            return False

    def add_submodule_to_main(
        self,
        submodule_url: str,
        submodule_path: str,
        main_repo_path: Optional[str] = None
    ) -> bool:
        """
        OpenClow 메인 리포지토리에 서브모듈 추가

        Args:
            submodule_url: 서브모듈 GitHub URL
            submodule_path: 메인 리포지토리 내부의 경로 (예: modules/builder/projects/project-name)
            main_repo_path: 메인 리포지토리 경로 (기본값: OPENCLAW_ROOT)
        """
        if main_repo_path is None:
            main_repo_path = str(project_root)

        logger.info(f"Adding submodule to main repository: {submodule_path}")

        try:
            # 메인 리포지토리에 서브모듈 추가
            subprocess.run(
                ['git', 'submodule', 'add', submodule_url, submodule_path],
                cwd=main_repo_path,
                capture_output=True,
                check=True
            )

            logger.info(f"✅ Submodule added: {submodule_path}")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to add submodule: {e.stderr.decode('utf-8')}")
            return False
        except Exception as e:
            logger.error(f"Failed to add submodule: {str(e)}")
            return False

    def create_as_submodule(
        self,
        project_dir: str,
        repo_name: str,
        description: str = "",
        main_repo_projects_dir: str = "modules/builder/projects"
    ) -> RepoInfo:
        """
        프로젝트를 생성하고 OpenClow 메인 리포지토리의 서브모듈로 추가

        Args:
            project_dir: 로컬 프로젝트 경로
            repo_name: 저장소 이름
            description: 저장소 설명
            main_repo_projects_dir: 메인 리포지토리 내 프로젝트 디렉토리 경로

        Returns:
            RepoInfo: 생성된 저장소 정보
        """
        logger.info(f"Creating project as submodule: {repo_name}")

        # 1. GitHub 저장소 생성
        repo_info = self.create_repo(
            repo_name=repo_name,
            description=description,
            private=False,
            auto_init=False
        )

        if not repo_info.created:
            logger.error("Failed to create GitHub repository")
            return repo_info

        # 2. AGPL-3.0 라이선스 추가
        self.add_agpl_license(project_dir)

        # 3. GitHub에 코드 push
        push_success = self.push_code(
            project_dir=project_dir,
            repo_url=repo_info.clone_url,
            commit_message=f"Initial commit: {repo_name}\n\nLicensed under AGPL-3.0"
        )

        if not push_success:
            logger.error("Failed to push code to GitHub")
            return repo_info

        # 4. 메인 리포지토리에 서브모듈로 추가
        # OPENCLAW_ROOT 환경 변수를 사용하여 경로 표준화
        main_repo_path = Path(os.getenv("OPENCLAW_ROOT", project_root))
        submodule_path = f"{main_repo_projects_dir}/{repo_name}"

        logger.info(f"Adding submodule to main repo at: {main_repo_path}")
        logger.info(f"Submodule path: {submodule_path}")

        submodule_success = self.add_submodule_to_main(
            submodule_url=repo_info.clone_url,
            submodule_path=submodule_path,
            main_repo_path=str(main_repo_path)
        )

        if submodule_success:
            repo_info.submodule_path = submodule_path
            logger.info(f"✅ Project created as submodule: {submodule_path}")
        else:
            logger.warning(f"Repository created but submodule addition failed")

        return repo_info

if __name__ == "__main__":
    pass