# Oracle Documentation Scraper

This Python script is designed to scrape Oracle documentation pages, specifically for Oracle Fusion Cloud Financials 25C What's New documentation.

## Features

- Sequential page-by-page processing
- Content extraction with preserved formatting
- Table data extraction
- Image URL extraction
- Link extraction
- Progress tracking
- Error handling

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the scraper:
```bash
python oracle_scraper.py
```

The script will:
1. Start from the initial URL
2. Process each page sequentially
3. Save results to `oracle_docs.json`
4. Print a summary of the scraping session

## Output

The script generates a JSON file containing:
- Page content with preserved formatting
- Table data
- Image URLs
- Links
- Timestamps
- Processing metadata

## Notes

- The script includes built-in delays between requests to be polite to the server
- All content is extracted in UTF-8 encoding to preserve special characters
- The script handles various forms of pagination (Next buttons, arrows, etc.)
