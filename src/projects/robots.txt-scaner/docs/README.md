# Robots.txt Scanner

A high-performance, asynchronous command-line tool designed to audit `robots.txt` files for a large volume of target domains. It efficiently fetches, parses, and analyzes robots.txt files, exporting detailed results in JSON format.

## Features

- **High Throughput:** Uses asynchronous I/O (`asyncio`, `aiohttp`) to process thousands of URLs concurrently.
- **Smart Caching:** Built-in SQLite caching to avoid re-scanning domains within 24 hours.
- **Standard Compliance:** Parses rules according to Robots Exclusion Protocol (REP).
- **Detailed Reporting:** Provides JSON output including HTTP status, parsed rules (Allow/Disallow), and Sitemap URLs.
- **Resilient:** Handles network timeouts and redirects gracefully.

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd robots-txt-scanner
   ```

2. **Install Dependencies**
   Create a virtual environment (recommended) and install required packages:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   pip install -r requirements.txt
   ```

## Usage

### Basic Syntax

```bash
python -m src.main [OPTIONS] INPUT_SOURCE
```

### Arguments

- `INPUT_SOURCE`: Path to a text file containing URLs (one per line) or `-` to read from stdin.

### Options

| Option | Short | Default | Description |
| :--- | :--- | :--- | :--- |
| `--output` | `-o` | `results.json` | Path to the output JSON file. |
| `--concurrency` | `-c` | `50` | Number of concurrent async requests. |
| `--timeout` | `-t` | `10` | Request timeout in seconds. |
| `--user-agent` | | `RobotsTxtScanner/1.0` | Custom User-Agent string. |
| `--verbose` | `-v` | `False` | Enable verbose logging. |

### Examples

1. **Scan URLs from a file**
   ```bash
   python -m src.main input/urls.txt --output report.json --concurrency 100
   ```

2. **Scan URLs via stdin (pipe)**
   ```bash
   cat input/urls.txt | python -m src.main - -output report.json
   ```

3. **Custom User-Agent and Timeout**
   ```bash
   python -m src.main urls.txt --user-agent "MyBot/2.0" --timeout 15
   ```

## Output Format

The tool generates a JSON file containing an array of result objects.

```json
[
  {
    "target_url": "https://example.com/some/page",
    "robots_url": "https://example.com/robots.txt",
    "status_code": 200,
    "content_length": 1024,
    "crawl_delay": null,
    "sitemap_urls": [
      "https://example.com/sitemap.xml"
    ],
    "rules": [
      {
        "user_agent": "*",
        "allow": ["/", "/public"],
        "disallow": ["/admin", "/private"]
      }
    ],
    "raw_content": "User-agent: * ...\n...",
    "error": null
  },
  {
    "target_url": "https://missing-site.com",
    "robots_url": "https://missing-site.com/robots.txt",
    "status_code": 404,
    "error": "Not Found",
    "rules": [],
    "sitemap_urls": []
  }
]
```

## Running Tests

To run the unit tests, ensure `pytest` is installed:

```bash
pip install pytest
pytest tests/
```

## Project Structure

```
robots-txt-scanner/
├── src/
│   ├── __init__.py
│   ├── main.py              # CLI entry point
│   └── scanner.py          # Core logic (Fetcher, Parser, Cache)
├── tests/
│   └── test_main.py         # Unit tests
├── docs/
│   └── README.md            # This file
├── requirements.txt          # Python dependencies
└── input/
    └── urls.txt             # Example input file
```

## License

MIT License