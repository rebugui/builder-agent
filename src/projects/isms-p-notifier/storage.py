"""
스토리지 모듈
마지막으로 확인한 게시글 번호를 저장합니다.
"""

import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class PostStorage:
    """게시글 저장소 클래스"""

    def __init__(self, storage_file: str = "last_post.json"):
        self.storage_file = Path(storage_file)
        self.last_post_number: Optional[str] = None
        self.load()

    def load(self) -> None:
        """저장된 게시글 번호 로드"""
        try:
            if self.storage_file.exists():
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.last_post_number = data.get('last_post_number')
                logger.info(f"저장된 게시글 번호: {self.last_post_number}")
            else:
                self.last_post_number = None
                logger.info("저장 파일 없음, 새로 시작")
        except Exception as e:
            logger.error(f"저장 파일 로드 실패: {e}")
            self.last_post_number = None

    def save(self) -> None:
        """현재 상태 저장"""
        try:
            self.storage_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'last_post_number': self.last_post_number,
                    'last_updated': str(Path(__file__).stat().st_mtime)
                }, f, ensure_ascii=False, indent=2)
            logger.debug(f"저장 완료: {self.last_post_number}")
        except Exception as e:
            logger.error(f"저장 실패: {e}")

    def is_new_post(self, post_number: str) -> bool:
        """새 게시글인지 확인"""
        if self.last_post_number is None:
            return True  # 첫 실행은 알림

        # 번호 비교 (숫자로 변환)
        try:
            current = int(post_number)
            last = int(self.last_post_number)
            return current > last
        except:
            return post_number != self.last_post_number

    def update_last_post(self, post_number: str) -> None:
        """마지막 게시글 번호 업데이트"""
        self.last_post_number = post_number
