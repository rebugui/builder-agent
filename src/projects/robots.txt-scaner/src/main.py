#!/usr/bin/env python3
"""
robots.txt Scanner - Main Entry Point

A high-performance CLI tool to scan robots.txt files for multiple domains.
"""
import sys
import argparse
import json
import asyncio
import signal
from typing import Set, List, Dict, Any

# Check for aiohttp availability at the global scope to avoid NameError in async functions
try:
    import aiohttp
except ImportError:
    sys.exit("[ERROR] 'aiohttp' is not installed. Please run 'pip install aiohttp'")

# Try to import local scanner module. 
# Changed from relative import (.scanner) to absolute import (scanner) 
# to allow the script to run standalone.
try:
    from scanner import RobotsFetcher, normalize_url
except ImportError:
    # If running as part of a package, you might need to adjust this back to from .scanner import ...
    sys.exit("[ERROR] 'scanner.py' module not found. Please ensure scanner.py is in the same directory.")


# Graceful shutdown handling
shutdown_event = asyncio.Event()


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    print("\n[INFO] Shutdown signal received. Finishing pending tasks...")
    shutdown_event.set()


async def worker(
    queue: asyncio.Queue,
    results: List[Dict[str, Any]],
    fetcher: RobotsFetcher,
    semaphore: asyncio.Semaphore,
    verbose: bool = False
):
    """
    Async worker that processes domains from the queue.
    """
    while True:
        # Wait for a domain or shutdown signal
        try:
            domain = queue.get_nowait()
        except asyncio.QueueEmpty:
            break

        if shutdown_event.is_set():
            queue.task_done()
            break

        async with semaphore:
            try:
                result = await fetcher.fetch(domain)
                results.append(result)
                if verbose:
                    print(f"[OK] {domain}")
            except Exception as e:
                error_msg = f"Failed to process {domain}: {e}"
                if verbose:
                    print(f"[ERROR] {error_msg}")
                # Append error information to results to maintain list integrity
                results.append({
                    "domain": domain,
                    "status": "error",
                    "error": str(e)
                })
            finally:
                queue.task_done()
            
            # Optional: Simple progress indicator
            # print(f".", end="", flush=True) 


async def process_domains(
    domains: Set[str],
    workers: int,
    timeout: int,
    verbose: bool
) -> List[Dict[str, Any]]:
    """
    Orchestrates the scanning process.
    """
    queue = asyncio.Queue()
    for domain in domains:
        await queue.put(domain)

    results = []
    semaphore = asyncio.Semaphore(workers)
    
    # aiohttp is imported at the top level now, so it is accessible here
    async with aiohttp.ClientSession() as session:
        fetcher = RobotsFetcher(session, timeout=timeout)
        
        # Create worker tasks
        tasks = []
        for _ in range(workers):
            task = asyncio.create_task(worker(queue, results, fetcher, semaphore, verbose))
            tasks.append(task)

        # Wait for all tasks to complete
        await asyncio.gather(*tasks)
    
    return results


def parse_args():
    """Parses command line arguments."""
    parser = argparse.ArgumentParser(
        description="robots.txt Scanner: Audit web scraping permissions at scale."
    )
    parser.add_argument(
        "-i", "--input", 
        required=True, 
        help="Path to file containing URLs (one per line) or '-' for STDIN."
    )
    parser.add_argument(
        "-o", "--output", 
        default="results.json", 
        help="Path to output JSON file (default: results.json)."
    )
    parser.add_argument(
        "-w", "--workers", 
        type=int, 
        default=50, 
        help="Number of concurrent async workers (default: 50)."
    )
    parser.add_argument(
        "-t", "--timeout", 
        type=int, 
        default=10, 
        help="HTTP request timeout in seconds (default: 10)."
    )
    parser.add_argument(
        "-v", "--verbose", 
        action="store_true", 
        help="Enable verbose logging."
    )
    return parser.parse_args()


def main():
    """Main execution function."""
    args = parse_args()
    
    # Setup signal handling
    signal.signal(signal.SIGINT, signal_handler)

    domains = set()
    
    # Input Handling
    try:
        if args.input == '-':
            # Read from STDIN
            print("[INFO] Reading URLs from STDIN...")
            for line in sys.stdin:
                line = line.strip()
                if line:
                    domain = normalize_url(line)
                    if domain:
                        domains.add(domain)
        else:
            # Read from file
            print(f"[INFO] Reading URLs from {args.input}...")
            with open(args.input, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        domain = normalize_url(line)
                        if domain:
                            domains.add(domain)
    except FileNotFoundError:
        print(f"[ERROR] File not found: {args.input}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Failed to read input: {e}")
        sys.exit(1)

    if not domains:
        print("[ERROR] No valid domains found in input.")
        sys.exit(0)

    print(f"[INFO] Starting scan for {len(domains)} unique domains with {args.workers} workers...")

    # Run Async Scan
    try:
        # aiohttp import and check is handled at module level
        results = asyncio.run(process_domains(domains, args.workers, args.timeout, args.verbose))
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred during scan: {e}")
        # For debugging purposes, it is often helpful to print the traceback
        # import traceback
        # traceback.print_exc()
        sys.exit(1)

    # Save results
    print(f"[INFO] Scan complete. Writing results to {args.output}...")
    try:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"[SUCCESS] Successfully processed {len(results)} domains.")
    except IOError as e:
        print(f"[ERROR] Failed to write output file: {e}")


if __name__ == "__main__":
    main()