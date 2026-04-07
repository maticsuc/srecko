#!/usr/bin/env python3
"""
Remove author name disambiguation from poem titles.
Wikisource adds "(Srečko Kosovel)" or "(Srečko Kosovel, N)" to distinguish 
poems with identical names. Since this is a single-author database, 
we should remove these markers.
"""

import json
import re

def clean_title(title):
    """
    Remove Wikisource author disambiguation from title.
    
    Examples:
    - "Balada (Srečko Kosovel)" -> "Balada"
    - "Pesem (Srečko Kosovel, 1)" -> "Pesem 1"
    - "Jesen (Srečko Kosovel, 3)" -> "Jesen 3"
    - "Večerja (Srečko Kosovel)" -> "Večerja"
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

def main():
    input_file = '/home/matic/dev/srecko/kosovel_data_cleaned.json'
    output_file = '/home/matic/dev/srecko/kosovel_data_final_cleaned.json'
    
    print(f"Reading {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    changes_count = 0
    total_works = 0
    
    # Process all categories
    for category_name, category_data in data['categories'].items():
        if 'works' in category_data:
            for work in category_data['works']:
                total_works += 1
                if 'title' in work:
                    original_title = work['title']
                    cleaned_title = clean_title(original_title)
                    
                    if original_title != cleaned_title:
                        work['title'] = cleaned_title
                        changes_count += 1
                        print(f"  {original_title}")
                        print(f"  → {cleaned_title}")
                        print()
    
    print(f"Processed {total_works} works")
    print(f"Modified {changes_count} titles")
    
    print(f"\nWriting to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print("Done!")

if __name__ == '__main__':
    main()
