import argparse
import sys
import json
import logging
import asyncio
from typing import List, IO
from .scanner import RobotsScanner, logger

def read_urls(source) -> List[str]:
    """Read URLs from a file path or stdin."""
    urls = []
    try:
        if isinstance(source, str):
            # File path
            with open(source, 'r', encoding='utf-8') as f:
                for line in f:
                    url = line.strip()
                    if url and not url.startswith('#'):
                        urls.append(url)
        else:
            # stdin
            for line in source:
                url = line.strip()
                if url and not url.startswith('#'):
                    urls.append(url)
    except FileNotFoundError:
        logger.error(f"File not found: {source}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error reading input: {e}")
        sys.exit(1)
        
    return urls

def write_results(results: List[dict], output_path: str):
    """Write scan results to JSON file."""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info(f"Results successfully saved to {output_path}")
    except IOError as e:
        logger.error(f"Failed to write output file: {e}")
        sys.exit(1)

async def main():
    parser = argparse.ArgumentParser(
        description="Robots.txt Scanner - A high-performance bulk auditor.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "input_source",
        nargs="?",
        default="-",
        help="Path to a text file containing URLs or '-' for stdin."
    )
    parser.add_argument(
        "--output", "-o",
        default="results.json",
        help="Path to the output JSON file."
    )
    parser.add_argument(
        "--concurrency", "-c",
        type=int,
        default=50,
        help="Number of concurrent async requests."
    )
    parser.add_argument(
        "--timeout", "-t",
        type=int,
        default=10,
        help="Request timeout in seconds."
    )
    parser.add_argument(
        "--user-agent",
        default="RobotsTxtScanner/1.0",
        help="Custom User-Agent string."
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging."
    )

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    # Input Handling
    if args.input_source == "-":
        logger.info("Reading URLs from stdin...")
        urls = read_urls(sys.stdin)
    else:
        logger.info(f"Reading URLs from file: {args.input_source}")
        urls = read_urls(args.input_source)

    if not urls:
        logger.warning("No URLs found to scan. Exiting.")
        sys.exit(0)

    logger.info(f"Starting scan for {len(urls)} URLs with concurrency {args.concurrency}...")

    # Initialize Scanner
    scanner = RobotsScanner(
        concurrency=args.concurrency,
        timeout=args.timeout,
        user_agent=args.user_agent
    )

    try:
        # Run Scan
        results = await scanner.run(urls)
        
        # Output Results
        success_count = sum(1 for r in results if r.get('error') is None and 200 <= r.get('status_code', 0) < 300)
        error_count = len(results) - success_count
        
        logger.info(f"Scan completed. Success: {success_count}, Errors: {error_count}")
        write_results(results, args.output)
        
    finally:
        await scanner.close()

if __name__ == "__main__":
    # Note: Windows proactor event loop policy is often required for high concurrency subprocesses,
    # but for aiohttp standard policy is usually fine. 
    # Using asyncio.run handles loop creation.
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Process interrupted by user.")
        sys.exit(1)