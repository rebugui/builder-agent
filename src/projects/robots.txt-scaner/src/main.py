"""
robots.txt scanner - 보안 스캐너 CLI
"""
import argparse
import sys


def create_parser():
    """
    ArgumentParser 생성 함수
    테스트 시 서브파서나 추가 설정을 위해 분리
    """
    parser = argparse.ArgumentParser(
        description="robots.txt scanner - 다량의 URL을 수집하고 robots.txt 스캔 후 JSON 형식으로 결과 출력"
    )
    parser.add_argument("target", help="스캔 대상 (URL, IP, 도메인)")
    parser.add_argument("-f", "--format", choices=["json", "text"], default="text")
    parser.add_argument("-o", "--output", help="결과 파일")
    parser.add_argument("-v", "--verbose", action="store_true")
    return parser


def _get_scanner_and_reporter():
    """
    Scanner와 Reporter 모듈을 안전하게 import하는 헬퍼 함수
    
    Returns:
        tuple: (Scanner, Reporter) 클래스 또는 (None, None) if import 실패
    """
    try:
        from .scanner import Scanner
        from .reporter import Reporter
    except ImportError:
        try:
            from scanner import Scanner
            from reporter import Reporter
        except ImportError as e:
            return None, None, str(e)
    return Scanner, Reporter, None


def main(argv=None):
    """
    메인 진입점 함수
    Lazy import를 사용하여 테스트 수집 시 import 에러 방지
    
    Args:
        argv: 커맨드라인 인자 (테스트용, None이면 sys.argv 사용)
    
    Returns:
        int: 종료 코드 (0: 성공, 1: 에러)
    """
    # 함수 내부에서 import하여 pytest 수집 시 에러 방지
    Scanner, Reporter, import_error = _get_scanner_and_reporter()
    
    if Scanner is None or Reporter is None:
        print(f"Error: Required modules not found - {import_error}", file=sys.stderr)
        return 1
    
    parser = create_parser()
    args = parser.parse_args(argv)
    
    scanner = Scanner(verbose=args.verbose)
    results = scanner.scan(args.target)
    
    reporter = Reporter()
    output = reporter.format(results, args.format)
    
    if args.output:
        # 보안: encoding 지정 및 안전한 파일 쓰기
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
        except OSError as e:
            print(f"Error writing to file: {e}", file=sys.stderr)
            return 1
    else:
        print(output)
    
    return 0


# 모듈 레벨에서는 아무것도 실행하지 않음 (pytest 수집 안전)
if __name__ == "__main__":
    sys.exit(main())