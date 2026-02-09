# robots.txt Scanner

A high-performance, asynchronous CLI tool designed to audit web scraping permissions at scale. It fetches and parses `robots.txt` files for thousands of domains simultaneously and exports the results to JSON.

## Features

*   **High Concurrency:** Utilizes Python's `asyncio` and `aiohttp` to handle thousands of checks efficiently.
*   **Flexible Input:** Accepts URLs from text files or standard input (STDIN).
*   **Detailed Parsing:** Extracts User-agent groups, Allow/Disallow rules, Crawl-delay, and Sitemap directives.
*   **Structured Output:** Generates detailed JSON reports including HTTP status codes, fetch times, and parsed rules.
*   **Resilient:** Built-in retry logic handling, timeout configuration, and error reporting for missing or unreachable files.

## Installation

### Prerequisites

*   Python 3.9 or higher

### Setup

1.  Clone the repository or copy the source code.
2.  Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Command Syntax

```bash
python -m src.main scan -i <input_file> -o <output_file> [OPTIONS]
```

### Options

| Option | Short | Description | Default |
| :--- | :--- | :--- | :--- |
| `--input` | `-i` | Path to file containing URLs (one per line). Use `-` for STDIN. | Required |
| `--output` | `-o` | Path to the output JSON file. | `results.json` |
| `--workers` | `-w` | Number of concurrent async workers. | `50` |
| `--timeout` | `-t` | HTTP request timeout in seconds. | `10` |
| `--verbose` | `-v` | Enable detailed logging to stdout. | `False` |

### Examples

1.  **Scan from a file:**
    Scan a list of URLs in `urls.txt` and save results to `report.json`.

    ```bash
    python -m src.main scan -i urls.txt -o report.json
    ```

2.  **High concurrency scan:**
    Process a large list with 200 workers and a 5-second timeout.

    ```bash
    python -m src.main scan -i massive_list.txt -o report.json -w 200 -t 5
    ```

3.  **Using Standard Input (Pipe):**
    Use another command to generate URLs and pipe them into the scanner.

    ```bash
    echo "https://google.com\nhttps://example.com" | python -m src.main scan -i - -o report.json
    ```

    Or from a file using cat:
    ```bash
    cat my_urls.txt | python -m src.main scan -i - -o report.json
    ```

## Input Format

The input file (or STDIN) should contain one URL per line.

```text
https://example.com/page1
https://subdomain.example.com/images
https://another-site.com
```

The tool automatically normalizes these URLs to their root domain to fetch the correct `robots.txt` (e.g., `https://example.com/robots.txt`).

## Output Format

The tool generates a JSON file containing an array of result objects.

```json
[
  {
    "domain": "example.com",
    "robots_url": "https://example.com/robots.txt",
    "status": 200,
    "fetch_time_ms": 145,
    "content_found": true,
    "parsed_rules": {
      "user_agents": ["*"],
      "disallows": ["/admin", "/login"],
      "allows": ["/public"],
      "crawl_delay": null,
      "sitemap": "https://example.com/sitemap.xml"
    },
    "error": null
  },
  {
    "domain": "missing-site.com",
    "robots_url": "https://missing-site.com/robots.txt",
    "status": 404,
    "fetch_time_ms": 52,
    "content_found": false,
    "parsed_rules": null,
    "error": "HTTP 404 Not Found"
  }
]
```

## Testing

Run the unit tests using `pytest`:

```bash
pytest tests/
```

## Security & Best Practices

*   **Input Validation:** All URLs are normalized and validated before processing to prevent injection attacks.
*   **Concurrency Control:** Built-in semaphores prevent overwhelming target servers (DoS protection).
*   **Error Handling:** Network errors and timeouts are caught gracefully, ensuring the scan continues for other targets.

## License

MIT License