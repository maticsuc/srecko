# AGENTS.md - Scraping Project Guidelines

This document provides guidelines for AI coding agents working on the Srečko Kosovel scraping scripts.

## Project Overview

This directory contains Python scripts for scraping, cleaning, and processing literary works from Slovenian Wikisource. The scripts fetch poems and prose from sl.wikisource.org and clean the data for use in the parent RAG database project.

## Running Scripts

### Individual Scripts
```bash
# Run any scraper directly (they are executable)
python3 kosovel_scraper.py
python3 scrape_integrali.py

# Or using shebang
./kosovel_scraper.py
./cleanup_kosovel.py
```

### Dependencies
Install from parent directory:
```bash
cd /home/matic/dev/srecko
source venv/bin/activate
pip install -r requirements.txt
```

Key dependencies for scraping:
- `requests` - HTTP requests
- `beautifulsoup4` - HTML parsing (if used)
- Standard library: `json`, `re`, `urllib`, `time`, `pathlib`

### Testing
No unit tests exist for the scraping directory. Scripts are standalone and run manually.

To verify data integrity after cleaning:
```bash
python3 compare_files.py
```

## Code Style Guidelines

### File Structure
- Shebang: `#!/usr/bin/env python3`
- Module docstring at the top describing purpose
- Imports in standard order: stdlib, third-party, local
- Constants in UPPER_CASE
- Global state variables (with caution): lowercase_with_underscores
- Functions: lowercase_with_underscores
- Main execution: `if __name__ == "__main__":` guard

### Imports
Order (with blank lines between groups):
1. Standard library imports
2. Third-party imports
3. Local application imports

Example:
```python
#!/usr/bin/env python3
"""Module description."""

import json
import re
import time
from pathlib import Path
from urllib.parse import urlencode, unquote

import requests
from bs4 import BeautifulSoup

# Constants follow
BASE_URL = "https://example.com"
```

### Naming Conventions
- **Files**: `lowercase_with_underscores.py`
- **Functions**: `lowercase_with_underscores()`
- **Variables**: `lowercase_with_underscores`
- **Constants**: `UPPER_CASE_WITH_UNDERSCORES`
- **Classes**: `PascalCase` (if needed, though this project uses mostly functional code)

### String Handling
- **UTF-8 encoding**: Always specify `encoding='utf-8'` when reading/writing files
- **f-strings** preferred for formatting: `f"Fetching: {page_title}"`
- **Single quotes** for simple strings, **double quotes** for human-readable messages
- **Raw strings** for regex patterns: `r'\{\{[^}]+\}\}'`

### Data Structures
- Use dictionaries for structured data
- Return `None` for failures, not empty strings or False
- Use `get()` with defaults for optional keys: `data.get('works', [])`

### Error Handling
- **Retries**: Implement exponential backoff for network requests
- **Specific exceptions**: Catch specific exceptions (e.g., `urllib.error.HTTPError`) before generic `Exception`
- **Logging**: Use `print()` with descriptive prefixes for progress tracking
  - `[SAVE]` - File save operations
  - `[ERR]` - Errors
  - `[RETRY]` - Retry attempts
  - `    >>` - Progress indicators
  - `✓`, `✗` - Success/failure indicators (in compare scripts)

Example error handling:
```python
for attempt in range(max_retries):
    try:
        response = make_request(url)
        return response
    except urllib.error.HTTPError as e:
        if e.code == 429:
            wait_time = 60 * (2 ** attempt)  # Exponential backoff
            print(f"    [429] Rate limited! Waiting {wait_time}s...")
            time.sleep(wait_time)
        elif attempt < max_retries - 1:
            time.sleep(10 * (attempt + 1))
        else:
            raise e
```

### JSON Operations
- **Indentation**: Always use `indent=2`
- **UTF-8**: Always use `ensure_ascii=False` to preserve Slovenian characters
- **File context managers**: Always use `with open()` for safety

Example:
```python
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
```

### Regular Expressions
- Compile patterns for reuse if used multiple times
- Use raw strings: `r'pattern'`
- Name groups for clarity: `r'\{\{naslov[^{}]*naslov\s*=\s*(?P<title>[^\n|}]+)'`
- Use `re.IGNORECASE` flag when case doesn't matter

### Rate Limiting & Politeness
- **Minimum request interval**: 3-5 seconds between requests
- **User-Agent**: Always set a descriptive User-Agent header
- **Exponential backoff**: For 429 rate limit responses
- **Progress saving**: Save after every N items to enable resume

Example:
```python
request_count = 0
last_request_time = 0
min_request_interval = 3.0

def make_request(params):
    global request_count, last_request_time
    current_time = time.time()
    elapsed = current_time - last_request_time
    if elapsed < min_request_interval:
        time.sleep(min_request_interval - elapsed)
    # ... make request
    last_request_time = time.time()
```

### Path Handling
- Use `pathlib.Path` for file paths when possible
- Absolute paths for output files in this project: `/home/matic/dev/srecko/...`
- Check file existence with `Path.exists()` before loading

### Comments & Documentation
- **Module docstrings**: Brief description of script purpose
- **Function docstrings**: For non-obvious functions, describe parameters and return values
- **Inline comments**: Explain "why" not "what" for complex logic
- **TODO comments**: Use `# TODO:` for future improvements

### Data Cleaning Patterns
Common cleaning operations in this project:
1. Remove Wikisource markup: `{{templates}}`, `[[links]]`
2. Remove HTML tags: `<poem>`, `<p>`, `<br>`
3. Strip formatting: `'''bold'''`, `''italic''`
4. Remove metadata lines (table syntax, headings)
5. Remove author disambiguation from titles: `(Srečko Kosovel)` → empty or number
6. Remove leading colons from poem lines
7. Normalize whitespace: max 2 consecutive newlines

### Progress Reporting
- Show progress every N items (e.g., every 3)
- Include: current/total, cumulative count, rate
- Flush stdout for real-time updates: `sys.stdout.flush()`

Example:
```python
if (i + 1) % 3 == 0:
    elapsed = time.time() - start_time
    rate = items_processed / elapsed if elapsed > 0 else 0
    print(f"    >> {i+1}/{total} | Total: {items_processed} | {rate:.2f}/s")
    sys.stdout.flush()
```

## Common Tasks

### Adding a New Scraper
1. Copy structure from `kosovel_scraper.py` or `scrape_integrali.py`
2. Implement rate limiting with proper delays
3. Add incremental saving for resume capability
4. Include User-Agent header
5. Handle errors with retries

### Adding a Data Cleaning Script
1. Follow pattern from `clean_data_comprehensive.py`
2. Load JSON with UTF-8 encoding
3. Show changes with before/after examples
4. Save cleaned data to new file (don't overwrite original)
5. Print summary statistics

### Modifying Existing Scripts
- Test with small datasets first (modify limits)
- Preserve existing data structure unless necessary
- Update progress messages to reflect changes
- Run `compare_files.py` after data modifications

## File Locations

Input/output files use absolute paths:
- `/home/matic/dev/srecko/kosovel_data.json` - Original scraped data
- `/home/matic/dev/srecko/kosovel_data_cleaned.json` - Intermediate cleaned data
- `/home/matic/dev/srecko/kosovel_data_cleaned_final.json` - Final cleaned data

## Notes for Agents

- **No type hints**: This project doesn't use type annotations
- **Global state**: Used sparingly for request tracking (see rate limiting pattern)
- **No classes**: Scripts are functional, not object-oriented
- **No logging module**: Uses simple `print()` statements
- **Manual execution**: Scripts are run manually, not via test framework
- **Slovenian text**: Always use UTF-8 encoding and preserve special characters (č, š, ž)
- **Data preservation**: When cleaning, verify no content is lost (word/URL count should match)
