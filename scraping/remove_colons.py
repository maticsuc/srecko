#!/usr/bin/env python3
"""
Remove leading colons from poem content lines in the JSON file.
This script removes ':' characters that appear at the start of lines in content fields.
"""

import json
import re

def remove_leading_colons(content):
    """Remove colons from the start of lines in content."""
    # Split by newlines, remove leading ':', rejoin
    lines = content.split('\n')
    cleaned_lines = []
    for line in lines:
        # Remove leading ':' if present
        if line.startswith(':'):
            cleaned_lines.append(line[1:])
        else:
            cleaned_lines.append(line)
    return '\n'.join(cleaned_lines)

def main():
    input_file = '/home/matic/dev/srecko/kosovel_data_cleaned.json'
    output_file = '/home/matic/dev/srecko/kosovel_data_no_colons.json'
    
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
                if 'content' in work:
                    original_content = work['content']
                    cleaned_content = remove_leading_colons(original_content)
                    
                    if original_content != cleaned_content:
                        work['content'] = cleaned_content
                        changes_count += 1
                        print(f"  Cleaned: {work['title']}")
    
    print(f"\nProcessed {total_works} works")
    print(f"Modified {changes_count} works with leading colons")
    
    print(f"\nWriting to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print("Done!")

if __name__ == '__main__':
    main()
