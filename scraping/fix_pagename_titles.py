#!/usr/bin/env python3
"""
Fix titles that have {{PAGENAME template variable by extracting from URL.
"""

import json
import re
from urllib.parse import unquote

def extract_title_from_url(url):
    """
    Extract the page title from a Wikisource URL.
    
    Example:
    https://sl.wikisource.org/wiki/Ravnodu%C5%A1je -> Ravnodušje
    https://sl.wikisource.org/wiki/Novoletni_sonet_%28Sre%C4%8Dko_Kosovel%29 -> Novoletni sonet
    """
    # Extract the part after /wiki/
    match = re.search(r'/wiki/(.+)$', url)
    if not match:
        return None
    
    page_name = match.group(1)
    
    # URL decode
    page_name = unquote(page_name)
    
    # Replace underscores with spaces
    page_name = page_name.replace('_', ' ')
    
    # Remove author disambiguation if present
    # Pattern: (Srečko Kosovel, N) -> keep number
    pattern1 = r'\s*\(Srečko Kosovel,\s*(\d+)\)'
    match = re.search(pattern1, page_name)
    if match:
        number = match.group(1)
        page_name = re.sub(pattern1, f' {number}', page_name)
    else:
        # Pattern: (Srečko Kosovel) -> remove
        pattern2 = r'\s*\(Srečko Kosovel\)'
        page_name = re.sub(pattern2, '', page_name)
    
    return page_name.strip()

def main():
    input_file = '/home/matic/dev/srecko/kosovel_data_cleaned_final.json'
    output_file = '/home/matic/dev/srecko/kosovel_data_cleaned_final.json'
    
    print(f"Reading {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    fixed_count = 0
    total_works = 0
    
    print("\n=== Fixing {{PAGENAME Titles ===\n")
    
    # Process all categories
    for category_name, category_data in data['categories'].items():
        if 'works' in category_data:
            for work in category_data['works']:
                total_works += 1
                
                title = work.get('title', '')
                
                # Check if title has template variable issue
                if '{{PAGENAME' in title or title.strip() == '{{' or '{{' in title:
                    url = work.get('url', '')
                    if url:
                        new_title = extract_title_from_url(url)
                        if new_title:
                            print(f"  OLD: {title}")
                            print(f"  NEW: {new_title}")
                            print(f"  URL: {url}")
                            print()
                            work['title'] = new_title
                            fixed_count += 1
                        else:
                            print(f"  ERROR: Could not extract title from URL: {url}")
                            print()
                    else:
                        print(f"  ERROR: No URL for work with title: {title}")
                        print()
    
    print(f"=== Summary ===")
    print(f"Processed {total_works} works")
    print(f"Fixed {fixed_count} titles with {{{{PAGENAME}} issues")
    
    print(f"\nWriting to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print("Done!")

if __name__ == '__main__':
    main()
