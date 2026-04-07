#!/usr/bin/env python3
"""
Comprehensive cleaning script for Kosovel data.
Fixes:
1. Removes leading colons from poem content lines
2. Removes author name disambiguation from titles
3. Fixes {{PAGENAME template issues by extracting title from URL
"""

import json
import re
from urllib.parse import unquote

def remove_leading_colons(content):
    """Remove colons from the start of lines in content."""
    if not content:
        return content
    lines = content.split('\n')
    cleaned_lines = []
    for line in lines:
        if line.startswith(':'):
            cleaned_lines.append(line[1:])
        else:
            cleaned_lines.append(line)
    return '\n'.join(cleaned_lines)

def clean_title(title):
    """
    Remove Wikisource author disambiguation from title.
    
    Examples:
    - "Balada (Srečko Kosovel)" -> "Balada"
    - "Pesem (Srečko Kosovel, 1)" -> "Pesem 1"
    - "Jesen (Srečko Kosovel, 3)" -> "Jesen 3"
    """
    # Pattern 1: (Srečko Kosovel, N) - keep the number but remove author
    pattern1 = r'\s*\(Srečko Kosovel,\s*(\d+)\)'
    match = re.search(pattern1, title)
    if match:
        number = match.group(1)
        cleaned = re.sub(pattern1, f' {number}', title)
        return cleaned.strip()
    
    # Pattern 2: (Srečko Kosovel) - just remove it
    pattern2 = r'\s*\(Srečko Kosovel\)'
    if re.search(pattern2, title):
        cleaned = re.sub(pattern2, '', title)
        return cleaned.strip()
    
    return title

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
    
    # Clean the title (remove author disambiguation)
    page_name = clean_title(page_name)
    
    return page_name.strip()

def main():
    input_file = '/home/matic/dev/srecko/kosovel_data_cleaned.json'
    output_file = '/home/matic/dev/srecko/kosovel_data_cleaned_final.json'
    
    print(f"Reading {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    colon_changes = 0
    title_changes = 0
    pagename_fixes = 0
    total_works = 0
    
    print("\n=== Title Changes ===")
    # Process all categories
    for category_name, category_data in data['categories'].items():
        if 'works' in category_data:
            for work in category_data['works']:
                total_works += 1
                
                # Fix {{PAGENAME issues first
                title = work.get('title', '')
                if '{{PAGENAME' in title or title.strip() == '{{' or '{{' in title:
                    url = work.get('url', '')
                    if url:
                        new_title = extract_title_from_url(url)
                        if new_title:
                            print(f"  [PAGENAME FIX] {title}")
                            print(f"               → {new_title}")
                            work['title'] = new_title
                            pagename_fixes += 1
                
                # Clean title (remove author disambiguation)
                if 'title' in work:
                    original_title = work['title']
                    cleaned_title = clean_title(original_title)
                    
                    if original_title != cleaned_title:
                        work['title'] = cleaned_title
                        title_changes += 1
                        print(f"  [AUTHOR] {original_title}")
                        print(f"         → {cleaned_title}")
                
                # Clean content (remove leading colons)
                if 'content' in work:
                    original_content = work['content']
                    cleaned_content = remove_leading_colons(original_content)
                    
                    if original_content != cleaned_content:
                        work['content'] = cleaned_content
                        colon_changes += 1
    
    print(f"\n=== Summary ===")
    print(f"Processed {total_works} works")
    print(f"Fixed {pagename_fixes} titles ({{{{PAGENAME}} template issues)")
    print(f"Modified {title_changes} titles (removed author names)")
    print(f"Modified {colon_changes} contents (removed leading colons)")
    
    print(f"\nWriting to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print("Done!")
    print(f"\nCleaned file ready: {output_file}")

if __name__ == '__main__':
    main()
