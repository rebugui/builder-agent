#!/usr/bin/env python3
"""
ISMS-P 자료실 새 글 알림 프로그램
주기적으로 첫 번째 게시글 번호를 확인하고 새 글이 있으면 알림을 표시합니다.
"""

import logging
import argparse
import json
import time
from pathlib import Path
from datetime import datetime

from isms_p_crawler import SyncISMPCrawler
from notifier import Notifier
from storage import PostStorage


def setup_logging(log_file: str = "isms_p_notifier.log", level: int = logging.INFO) -> None:
    """로깅 설정"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


def load_config(config_file: str = "config.json") -> dict:
    """설정 파일 로드"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.warning(f"설정 파일 없음: {config_file}, 기본 설정 사용")
        return {
            "target_urls": {
                "list_page": "https://isms-p.or.kr/ntcn/rcsrm/selectGnrlVrtlRcsrmList.do"
            },
            "check_interval_minutes": 30,
            "notification": {
                "enabled": True,
                "sound": True,
                "timeout_seconds": 10
            },
            "storage": {
                "seen_posts_file": "last_post.json",
                "log_file": "isms_p_notifier.log"
            }
        }


def run_once(config: dict) -> None:
    """한 번만 실행하여 새 게시글 확인"""
    logger = logging.getLogger(__name__)

    # 컴포넌트 초기화
    crawler = SyncISMPCrawler(config['target_urls']['list_page'])
    notifier = Notifier()

    storage_file = config['storage'].get('seen_posts_file', 'last_post.json')
    storage = PostStorage(storage_file)

    # 첫 번째 게시글 가져오기
    logger.info("게시글 확인 중...")
    post_info = crawler.get_first_post_info()

    if not post_info:
        logger.warning("게시글을 가져오지 못했습니다.")
        return

    post_number = post_info['number']
    logger.info(f"현재 첫 번째 게시글 번호: {post_number}")

    # 새 게시글 확인
    if storage.is_new_post(post_number):
        logger.info(f"새 게시글 발견! #{post_number}")

        # 알림 표시
        title = f"새 글 알림 (#{post_number})"
        message = f"{post_info['title']}\n{post_info['date']}\n\n{post_info.get('link', '')}"

        notifier.show_notification(title, message, timeout=10)

        if config['notification'].get('sound', True):
            notifier.play_sound()

        # 저장소 업데이트
        storage.update_last_post(post_number)
        storage.save()

        logger.info("새 게시글 알림 완료")
    else:
        logger.info("새 게시글 없음")


def run_scheduled(config: dict) -> None:
    """주기적으로 실행"""
    logger = logging.getLogger(__name__)

    interval = config.get('check_interval_minutes', 30)
    logger.info(f"주기적 모드 시작 - 확인 간격: {interval}분")

    # 컴포넌트 초기화
    notifier = Notifier()

    storage_file = config['storage'].get('seen_posts_file', 'last_post.json')
    storage = PostStorage(storage_file)

    try:
        while True:
            try:
                logger.info(f"=== {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 게시글 확인 시작 ===")

                # 크롤러는 매번 새로 생성
                crawler = SyncISMPCrawler(config['target_urls']['list_page'])

                # 첫 번째 게시글 가져오기
                post_info = crawler.get_first_post_info()

                if post_info:
                    post_number = post_info['number']
                    logger.info(f"현재 첫 번째 게시글 번호: {post_number}")

                    # 새 게시글 확인
                    if storage.is_new_post(post_number):
                        logger.info(f"새 게시글 발견! #{post_number}")

                        # 알림 표시
                        title = f"새 글 알림 (#{post_number})"
                        message = f"{post_info['title']}\n{post_info['date']}\n\n{post_info.get('link', '')}"

                        notifier.show_notification(title, message, timeout=10)

                        if config['notification'].get('sound', True):
                            notifier.play_sound()

                        # 저장소 업데이트
                        storage.update_last_post(post_number)
                        storage.save()
                    else:
                        logger.info("새 게시글 없음")
                else:
                    logger.warning("게시글을 가져오지 못함")

                logger.info(f"다음 확인까지 {interval}분 대기...")
                time.sleep(interval * 60)

            except KeyboardInterrupt:
                logger.info("사용자 중지")
                break
            except Exception as e:
                logger.error(f"실행 중 오류: {e}", exc_info=True)
                time.sleep(60)  # 오류 발생 시 1분 후 재시도

    finally:
        storage.save()
        logger.info("프로그램 종료")


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='ISMS-P 자료실 새 글 알림 프로그램')
    parser.add_argument('--config', '-c', default='config.json', help='설정 파일 경로')
    parser.add_argument('--once', '-o', action='store_true', help='한 번만 실행')
    parser.add_argument('--debug', '-d', action='store_true', help='디버그 모드')
    parser.add_argument('--interval', '-i', type=int, help='확인 간격 (분)')

    args = parser.parse_args()

    # 설정 로드
    config = load_config(args.config)

    # 명령줄 인자로 설정 덮어쓰기
    if args.interval:
        config['check_interval_minutes'] = args.interval

    # 로깅 설정
    log_level = logging.DEBUG if args.debug else logging.INFO
    log_file = config['storage'].get('log_file', 'isms_p_notifier.log')
    setup_logging(log_file, log_level)

    logger = logging.getLogger(__name__)
    logger.info("ISMS-P 알림 프로그램 시작")
    logger.info(f"목표 URL: {config['target_urls']['list_page']}")

    # 실행 모드
    if args.once:
        run_once(config)
    else:
        run_scheduled(config)


if __name__ == '__main__':
    main()
