import requests
from bs4 import BeautifulSoup
import datetime
import json
import time
from urllib.parse import urljoin
import re
import argparse

class OracleDocumentationScraper:
    """
    A scraper for Oracle Fusion Cloud Financials documentation.
    It navigates through pages, extracts content, and saves it to a JSON file.
    """
    def __init__(self, toc_url):
        """Initialize the scraper with a table of contents URL and a requests session."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.toc_url = toc_url
        self.processed_pages_content = []
        self.failed_pages = []
        self.visited_urls = set()
        self.total_words = 0
        self.start_time = datetime.datetime.now().isoformat()
        print("Scraper initialized.")

    def _get_soup(self, url):
        """Fetches a URL and returns a BeautifulSoup object, with retries."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=15)
                response.raise_for_status()
                return BeautifulSoup(response.text, 'html5lib')
            except requests.exceptions.RequestException as e:
                print(f"Error fetching {url} (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)  # Wait before retrying
                else:
                    self.failed_pages.append({
                        'url': url,
                        'error': str(e),
                        'timestamp': datetime.datetime.now().isoformat()
                    })
        return None

    def get_toc_urls(self):
        """Fetches and parses the table of contents to get a list of all page URLs."""
        print(f"Fetching Table of Contents from: {self.toc_url}")
        soup = self._get_soup(self.toc_url)
        if not soup:
            print("Failed to fetch Table of Contents. Aborting.")
            return []

        urls = []
        unique_clean_urls = set()
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href:
                clean_href = href.split('#')[0]
                if clean_href and clean_href.endswith('.htm') and 'index.html' not in clean_href and 'toc.htm' not in clean_href:
                    full_url = urljoin(self.toc_url, clean_href)
                    if full_url not in unique_clean_urls:
                        urls.append(full_url)
                        unique_clean_urls.add(full_url)
        
        print(f"Found {len(urls)} unique page URLs in the Table of Contents.")
        return urls

    def extract_content(self, soup, url):
        """Extracts structured content from a BeautifulSoup object."""
        if not soup:
            return None

        title = soup.title.string.strip() if soup.title else "Untitled Page"
        
        content_div = soup.find('div', class_='body-container') or soup.body

        content_text = ""
        for element in content_div.find_all(['h1', 'h2', 'h3', 'p', 'ul', 'ol', 'li']):
            if element.name.startswith('h'):
                level = int(element.name[1])
                content_text += f"\n{'#' * level} {element.get_text(strip=True)}\n"
            elif element.name in ['p', 'li']:
                 content_text += f"{element.get_text(strip=True)}\n"

        tables = []
        for table in content_div.find_all('table'):
            table_md = ""
            headers = [th.get_text(strip=True) for th in table.find_all('th')]
            if headers:
                table_md += f"| {' | '.join(headers)} |\n"
                table_md += f"|{'|'.join(['---'] * len(headers))}|\n"
            
            for row in table.find_all('tr'):
                cells = [td.get_text(strip=True) for td in row.find_all('td')]
                if cells:
                    table_md += f"| {' | '.join(cells)} |\n"
            tables.append(table_md)
            content_text += f"\n{table_md}\n"

        images = [{'url': urljoin(url, img['src']), 'alt': img.get('alt', '')} for img in content_div.find_all('img', src=True)]
        links = [{'text': a.get_text(strip=True), 'url': urljoin(url, a['href'])} for a in content_div.find_all('a', href=True)]

        page_data = {
            'url': url,
            'title': title,
            'content': content_text.strip(),
            'tables': tables,
            'images': images,
            'links': links,
            'timestamp': datetime.datetime.now().isoformat()
        }
        self.total_words += len(content_text.split())
        return page_data

    def scrape_all_pages(self, output_file):
        """Scrapes all pages listed in the table of contents and yields progress updates."""
        yield f"Fetching Table of Contents from: {self.toc_url}\n"
        page_urls = self.get_toc_urls()
        if not page_urls:
            yield "Failed to fetch Table of Contents. Aborting.\n"
            return

        total_pages = len(page_urls)
        yield f"Found {total_pages} unique page URLs in the Table of Contents.\n"
        yield f"\nStarting scrape of {total_pages} pages.\n"

        for i, url in enumerate(page_urls):
            if url in self.visited_urls:
                yield f"Skipping already visited URL: {url}\n"
                continue
            
            self.visited_urls.add(url)
            yield f"--- Processing Page {i + 1}/{total_pages}: {url} ---\n"
            
            soup = self._get_soup(url)
            if not soup:
                yield f"Failed to retrieve page content for {url}. Skipping.\n"
                continue

            page_content = self.extract_content(soup, url)
            if page_content:
                self.processed_pages_content.append(page_content)
                yield f"Successfully extracted content from '{page_content['title']}'.\n"
            else:
                yield f"Could not extract content from {url}.\n"

            time.sleep(1) # Be polite

        yield "\nScraping finished.\n"
        self.save_results(output_file)
        yield f"Successfully saved results to {output_file}\n"
        yield "\n--- SCRAPING COMPLETE ---\n"
        yield f"Total pages processed: {len(self.visited_urls)}\n"
        yield f"Total content extracted: ~{self.total_words} words\n"
        if self.failed_pages:
            yield f"Failed pages: {len(self.failed_pages)}\n"
            for page in self.failed_pages:
                yield f"- URL: {page['url']}, Error: {page['error']}\n"
        else:
            yield "No issues encountered during the scraping session.\n"

    def save_results(self, output_file):
        """Saves the scraped results and a summary to a JSON file."""
        results = {
            'session_summary': {
                'toc_url': self.toc_url,
                'start_time': self.start_time,
                'end_time': datetime.datetime.now().isoformat(),
                'total_pages_scraped': len(self.processed_pages_content),
                'total_words_extracted': self.total_words,
                'failed_pages_count': len(self.failed_pages),
            },
            'failed_pages': self.failed_pages,
            'scraped_content': self.processed_pages_content
        }
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=4, ensure_ascii=False)
            print(f"Successfully saved results to {output_file}")
        except IOError as e:
            print(f"Error saving results to {output_file}: {e}")


