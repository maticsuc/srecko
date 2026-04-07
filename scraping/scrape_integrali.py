#!/usr/bin/env python3
"""
Scrape works from Integrali '26 and add to kosovel_data_cleaned_final.json
"""
import json
import re
import time
from urllib.parse import urljoin, unquote
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://sl.wikisource.org"
INDEX_URL = "https://sl.wikisource.org/wiki/Integrali_%2726"
JSON_FILE = "/home/matic/dev/srecko/kosovel_data_cleaned_final.json"

# Headers to avoid 403 errors
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def get_work_urls(index_url):
    """Extract all work URLs from the index page."""
    print(f"Fetching index page: {index_url}")
    response = requests.get(index_url, headers=HEADERS)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find all links in the content area
    content = soup.find('div', class_='mw-parser-output')
    if not content:
        print("Could not find content area")
        return []
    
    # Find all links within the list
    links = content.find_all('a', href=True)
    
    work_urls = []
    for link in links:
        href = link.get('href', '')
        # Skip special pages, categories, and navigation links
        if href.startswith('/wiki/') and not any(skip in href for skip in ['Posebno:', 'Kategorija:', 'Wikivir:', 'Predloga:', 'Pogovor:']):
            full_url = urljoin(BASE_URL, href)
            title = link.text.strip()
            if title and 'action=edit' not in href:
                work_urls.append((title, full_url))
    
    print(f"Found {len(work_urls)} works")
    return work_urls

def scrape_work(url):
    """Scrape a single work from its URL."""
    print(f"  Scraping: {url}")
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the title
        title_elem = soup.find('h1', class_='firstHeading')
        title = title_elem.text.strip() if title_elem else ""
        
        # Find the content
        content_div = soup.find('div', class_='mw-parser-output')
        if not content_div:
            print(f"    Warning: No content found for {url}")
            return None
        
        # Extract poem text (skip navigation elements)
        # Remove tables, navigation elements
        for elem in content_div.find_all(['table', 'style']):
            elem.decompose()
        
        # Get all paragraphs and poem text
        content_parts = []
        for elem in content_div.find_all(['p', 'div'], recursive=False):
            text = elem.get_text(separator='\n', strip=True)
            if text and len(text) > 10:  # Skip very short snippets
                content_parts.append(text)
        
        content = '\n'.join(content_parts)
        
        # Clean up excessive whitespace
        content = re.sub(r'\n{3,}', '\n\n', content)
        content = content.strip()
        
        if not content or len(content) < 20:
            print(f"    Warning: Content too short for {url}")
            return None
        
        return {
            "title": title,
            "content": content,
            "url": url
        }
    except Exception as e:
        print(f"    Error scraping {url}: {e}")
        return None

def main():
    # Load existing JSON
    print(f"Loading {JSON_FILE}")
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Get all work URLs from index page
    work_urls = get_work_urls(INDEX_URL)
    
    if not work_urls:
        print("No works found!")
        return
    
    # Scrape each work
    works = []
    for i, (title, url) in enumerate(work_urls, 1):
        print(f"[{i}/{len(work_urls)}] {title}")
        work = scrape_work(url)
        if work:
            works.append(work)
        time.sleep(0.5)  # Be polite to the server
    
    print(f"\nSuccessfully scraped {len(works)} works")
    
    # Add new category to JSON
    if "categories" not in data:
        data["categories"] = {}
    
    data["categories"]["integrali_26"] = {
        "index_page": "Integrali '26 (Srečko Kosovel)",
        "works": works
    }
    
    # Save updated JSON
    print(f"Saving to {JSON_FILE}")
    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Done! Added {len(works)} works to category 'integrali_26'")

if __name__ == "__main__":
    main()
