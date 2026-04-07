#!/usr/bin/env python3
"""
Srečko Kosovel Wikisource Scraper
Scrapes all content from sl.wikisource.org/wiki/Srečko_Kosovel
Saves progress incrementally
"""

import json
import time
import urllib.parse
from pathlib import Path
import re
import sys

BASE_URL = "https://sl.wikisource.org/w/api.php"
OUTPUT_FILE = Path("/home/matic/dev/srecko/kosovel_data.json")

request_count = 0
last_request_time = 0
min_request_interval = 3.0

def make_request(params, max_retries=5):
    global request_count, last_request_time
    
    import urllib.request
    import urllib.error
    
    params['format'] = 'json'
    params['origin'] = '*'
    
    url = f"{BASE_URL}?{urllib.parse.urlencode(params)}"
    
    for attempt in range(max_retries):
        try:
            current_time = time.time()
            elapsed = current_time - last_request_time
            if elapsed < min_request_interval:
                time.sleep(min_request_interval - elapsed)
            
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'KosovelScraper/1.0')
            with urllib.request.urlopen(req, timeout=30) as response:
                last_request_time = time.time()
                request_count += 1
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait_time = 60 * (2 ** attempt)  # Exponential backoff: 60, 120, 240, 480, 960
                print(f"    [429] Rate limited! Waiting {wait_time}s...")
                sys.stdout.flush()
                time.sleep(wait_time)
            elif attempt < max_retries - 1:
                time.sleep(10 * (attempt + 1))
            else:
                raise e
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(10 * (attempt + 1))
            else:
                raise e
    return None

def get_page_html(title):
    params = {
        'action': 'parse',
        'page': title,
        'prop': 'text'
    }
    result = make_request(params)
    if result and 'parse' in result:
        return result['parse']['text']['*']
    return None

def get_page_content(title):
    params = {
        'action': 'query',
        'titles': title,
        'prop': 'revisions',
        'rvprop': 'content'
    }
    result = make_request(params)
    if result and 'query' in result:
        pages = result['query'].get('pages', {})
        for page_id, page_data in pages.items():
            if page_id != '-1':
                return page_data['revisions'][0]['*']
    return None

def get_page_info(title):
    params = {
        'action': 'query',
        'titles': title,
        'prop': 'info'
    }
    result = make_request(params)
    if result and 'query' in result:
        pages = result['query'].get('pages', {})
        for page_id, page_data in pages.items():
            if page_id != '-1':
                return page_data
    return None

def extract_links_from_html(html):
    if not html:
        return []
    links = []
    href_pattern = re.compile(r'href="/wiki/([^"]+)"')
    for match in href_pattern.finditer(html):
        link = urllib.parse.unquote(match.group(1))
        if link and not link.startswith('Special:') and not link.startswith('Help:') and not link.startswith('Wikivir:') and ':' not in link:
            if link not in links:
                links.append(link)
    return links

def load_progress():
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def save_progress(data):
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  [SAVE] Progress saved to {OUTPUT_FILE}")

def scrape_category(page_title, cat_key):
    print(f"  Fetching: {page_title}")
    
    html = get_page_html(page_title)
    if not html:
        print(f"    WARNING: Could not fetch {page_title}")
        return None
    
    links = extract_links_from_html(html)
    print(f"    Found {len(links)} links")
    return links

def scrape_work_page(title):
    content = get_page_content(title)
    info = get_page_info(title)
    
    return {
        'title': title,
        'content': content,
        'url': f"https://sl.wikisource.org/wiki/{urllib.parse.quote(title)}"
    }

def main():
    print("=" * 60)
    print("Srečko Kosovel Wikisource Scraper")
    print("=" * 60)
    
    existing = load_progress()
    if existing:
        print(f"\nResuming from previous session...")
        data = existing
        start_category = data.get('current_category', 0)
    else:
        print(f"\nStarting fresh session...")
        data = {
            'metadata': {
                'source': 'https://sl.wikisource.org/wiki/Sre%C4%8Dko_Kosovel',
                'scraped_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'author': 'Srečko Kosovel'
            },
            'author_info': {},
            'categories': {},
            'statistics': {
                'pages_scraped': 0,
                'failed_pages': [],
                'start_time': time.time()
            },
            'current_category': 0
        }
        save_progress(data)
    
    categories = [
        ("Srečko Kosovel", "author_info"),
        ("Lirika (Srečko Kosovel)", "lirika"),
        ("Avantgardistična poezija (Srečko Kosovel)", "avantgardisticna_poezija"),
        ("Pesmi v prozi", "pesmi_v_prozi"),
        ("Črtice (Srečko Kosovel)", "crtice"),
        ("Članki (Srečko Kosovel)", "clanki"),
        ("Eseji o umetnosti (Srečko Kosovel)", "eseji_o_umetnosti"),
        ("Literarne kritike in recenzije (Srečko Kosovel)", "literarne_kritike"),
        ("Pismo Antonije Kosovel Mariji Skrinjar", "precevanja"),
    ]
    
    # Retry failed pages
    if 'retry_failed' in data and data['retry_failed'].get('status') == 'pending':
        failed_pages = data['retry_failed'].get('pages', [])
        print(f"\n[RETRY] Attempting {len(failed_pages)} failed pages...")
        for link in failed_pages:
            try:
                print(f"    Retrying: {link}")
                work = scrape_work_page(link)
                data['categories']['lirika']['works'].append(work)
                data['statistics']['pages_scraped'] += 1
                print(f"    SUCCESS: {link}")
                time.sleep(5)
            except Exception as e:
                print(f"    FAILED: {link} - {e}")
        data['retry_failed']['status'] = 'completed'
        save_progress(data)
    
    cat_idx = data.get('current_category', 0)
    
    for idx, (page_title, cat_key) in enumerate(categories):
        if idx < cat_idx:
            continue
            
        print(f"\n[{idx+1}/{len(categories)}] Category: {cat_key}")
        
        if cat_key == "author_info":
            html = get_page_html(page_title)
            if html:
                data['author_info']['html'] = html
                print(f"  Author page fetched")
            data['current_category'] = idx + 1
            save_progress(data)
            continue
        
        links = scrape_category(page_title, cat_key)
        
        if cat_key not in data['categories']:
            data['categories'][cat_key] = {
                'index_page': page_title,
                'works': [],
                'completed': False
            }
        
        if not links:
            data['categories'][cat_key]['completed'] = True
            data['current_category'] = idx + 1
            save_progress(data)
            continue
        
        existing_titles = {w['title'] for w in data['categories'].get(cat_key, {}).get('works', [])}
        filtered_links = [l for l in links if l not in existing_titles]
        
        total = len(filtered_links)
        print(f"    Already have: {len(links) - len(filtered_links)} | To scrape: {total}")
        
        for i, link in enumerate(filtered_links):
            try:
                work = scrape_work_page(link)
                data['categories'][cat_key]['works'].append(work)
                data['statistics']['pages_scraped'] += 1
                
                if (i + 1) % 3 == 0:
                    elapsed = time.time() - data['statistics']['start_time']
                    rate = data['statistics']['pages_scraped'] / elapsed if elapsed > 0 else 0
                    print(f"    >> {i+1}/{total} | Total: {data['statistics']['pages_scraped']} | {rate:.2f}/s | {cat_key}")
                    sys.stdout.flush()
                    save_progress(data)
                    
            except Exception as e:
                print(f"    [ERR] {link}: {e}")
                data['statistics']['failed_pages'].append({'page': link, 'error': str(e)})
            
            time.sleep(4.0)
        
        data['categories'][cat_key]['completed'] = True
        data['current_category'] = idx + 1
        save_progress(data)
        print(f"  Category complete: {len(data['categories'][cat_key]['works'])} works")
    
    elapsed = time.time() - data['statistics']['start_time']
    print(f"\n{'=' * 60}")
    print(f"SCRAPING COMPLETE")
    print(f"{'=' * 60}")
    print(f"Total pages scraped: {data['statistics']['pages_scraped']}")
    print(f"Failed pages: {len(data['statistics']['failed_pages'])}")
    print(f"Time elapsed: {elapsed/60:.1f} minutes")
    print(f"Output: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()