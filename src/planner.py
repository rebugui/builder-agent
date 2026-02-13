#!/usr/bin/env python3
"""
Builder Agent - Topic Planner

Database에서 미완료 주제를 조회하고 필터링하여 최적의 주제를 추천합니다.
"""

import os
import sqlite3
import sys
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path

# Add project root to sys.path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parents[1]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from builder_config import config
from utils.logger import setup_logger

logger = setup_logger("TopicPlanner")

@dataclass
class Project:
    """프로젝트 데이터 클래스"""
    id: int
    name: str
    description: str
    status: str
    deployed_url: Optional[str]
    created_at: str
    updated_at: str


class TopicPlanner:
    """Topic Planner (주제 선정)"""

    def __init__(self, db_path: str = None):
        """초기화"""
        if db_path is None:
            self.db_path = config.DATABASE_PATH
        else:
            self.db_path = Path(db_path)
            
        self.db_path = str(self.db_path) # sqlite3 needs string

        # Initialize DB if not exists
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """데이터베이스 연결 생성"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as e:
            logger.error(f"Database connection failed: {e}")
            raise

    def _init_db(self):
        """데이터베이스 및 테이블 초기화"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Planning',
                    deployed_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            logger.error(f"Database initialization failed: {e}")

    def get_all_projects(self) -> List[Project]:
        """모든 프로젝트 조회"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, description, status, deployed_url, created_at, updated_at
            FROM projects
            ORDER BY created_at DESC
        """)

        rows = cursor.fetchall()
        conn.close()

        projects = []
        for row in rows:
            projects.append(Project(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                status=row['status'],
                deployed_url=row['deployed_url'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            ))

        return projects

    def get_incomplete_projects(self) -> List[Project]:
        """미완료 프로젝트 조회 (status != 'Done')"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, description, status, deployed_url, created_at, updated_at
            FROM projects
            WHERE status != 'Done'
            ORDER BY created_at ASC
        """)

        rows = cursor.fetchall()
        conn.close()

        projects = []
        for row in rows:
            projects.append(Project(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                status=row['status'],
                deployed_url=row['deployed_url'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            ))

        return projects

    def filter_by_keywords(self, projects: List[Project], keywords: List[str]) -> List[Project]:
        """키워드로 프로젝트 필터링"""
        filtered = []
        keywords_lower = [kw.lower() for kw in keywords]

        for project in projects:
            name_lower = project.name.lower()
            desc_lower = project.description.lower()

            for kw in keywords_lower:
                if kw in name_lower or kw in desc_lower:
                    filtered.append(project)
                    break

        return filtered

    def score_project(self, project: Project) -> float:
        """프로젝트 점수 계산"""
        score = 0.0

        # 1. Usefulness
        vulnerability_keywords = [
            'vulnerability', 'security', 'exploit', 'cve',
            '취약점', '보안', '공격', 'scanner', 'analyzer'
        ]
        name_lower = project.name.lower()
        desc_lower = project.description.lower()

        for kw in vulnerability_keywords:
            if kw in name_lower or kw in desc_lower:
                score += 0.3
                break

        # 2. Implementability
        devops_keywords = [
            'docker', 'kubernetes', 'container', 'k8s',
            'ci/cd', 'pipeline', 'devops', 'deployment'
        ]
        for kw in devops_keywords:
            if kw in name_lower or kw in desc_lower:
                score += 0.2
                break

        # 3. Description length
        desc_len = len(project.description)
        if desc_len > 100: score += 0.3
        elif desc_len > 50: score += 0.2
        elif desc_len > 20: score += 0.1

        # 4. Status (older first)
        if project.status == 'Planning': score += 0.2
        elif project.status == 'In Progress': score += 0.1

        return min(score, 1.0)

    def select_topic(self, keywords: List[str] = None) -> Optional[Project]:
        """최적의 주제 선택"""
        logger.info("Selecting topic...")
        projects = self.get_incomplete_projects()

        if not projects:
            logger.warning("No incomplete projects found.")
            return None

        if keywords:
            projects = self.filter_by_keywords(projects, keywords)
            if not projects:
                logger.warning(f"No projects found matching keywords: {keywords}. Using all incomplete projects.")
                projects = self.get_incomplete_projects()

        scored_projects = []
        for project in projects:
            score = self.score_project(project)
            scored_projects.append((project, score))

        scored_projects.sort(key=lambda x: x[1], reverse=True)
        selected_project = scored_projects[0][0]

        logger.info(f"Selected project: {selected_project.name} (Score: {scored_projects[0][1]:.2f})")
        return selected_project

    def add_project(self, name: str, description: str, status: str = 'Planning') -> int:
        """새 프로젝트 추가"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO projects (name, description, status)
            VALUES (?, ?, ?)
        """, (name, description, status))

        project_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logger.info(f"Project added: {name} (ID: {project_id})")
        return project_id

    def update_project_status(self, project_id: int, status: str) -> bool:
        """프로젝트 상태 업데이트"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE projects
            SET status = ?, updated_at = ?
            WHERE id = ?
        """, (status, datetime.now().isoformat(), project_id))

        success = cursor.rowcount > 0
        conn.commit()
        conn.close()

        if success:
            logger.info(f"Project {project_id} status updated to: {status}")
        else:
            logger.warning(f"Failed to update status for project {project_id}")

        return success

    def update_project_url(self, project_id: int, deployed_url: str) -> bool:
        """프로젝트 배포 URL 업데이트"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE projects
            SET deployed_url = ?, updated_at = ?
            WHERE id = ?
        """, (deployed_url, datetime.now().isoformat(), project_id))

        success = cursor.rowcount > 0
        conn.commit()
        conn.close()

        if success:
            logger.info(f"Project {project_id} URL updated to: {deployed_url}")

        return success

    def list_projects(self, status: str = None) -> List[Project]:
        """프로젝트 리스트 출력"""
        projects = self.get_all_projects()

        if status:
            projects = [p for p in projects if p.status == status]

        print(f"\n📋 Projects List ({len(projects)} total):")
        print("=" * 80)

        for project in projects:
            print(f"ID: {project.id}")
            print(f"Name: {project.name}")
            print(f"Status: {project.status}")
            print("-" * 80)

        return projects

if __name__ == "__main__":
    pass