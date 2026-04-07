#!/usr/bin/env python3
"""
Compare original and cleaned Kosovel data files to ensure data integrity.
"""

import json

def compare_files():
    print("=" * 70)
    print("COMPARING ORIGINAL vs CLEANED DATA FILES")
    print("=" * 70)
    
    # Load both files
    with open('/home/matic/dev/srecko/kosovel_data.json', 'r') as f:
        original = json.load(f)
    
    with open('/home/matic/dev/srecko/kosovel_data_cleaned_final.json', 'r') as f:
        cleaned = json.load(f)
    
    print("\n1. METADATA CHECK")
    print("-" * 70)
    print(f"Original metadata: {original['metadata']}")
    print(f"Cleaned metadata:  {cleaned['metadata']}")
    match = original['metadata'] == cleaned['metadata']
    print(f"Metadata match: {'✓ YES' if match else '✗ NO'}")
    
    print("\n2. CATEGORY COUNT")
    print("-" * 70)
    orig_cats = set(original['categories'].keys())
    clean_cats = set(cleaned['categories'].keys())
    print(f"Original categories: {len(orig_cats)} - {sorted(orig_cats)}")
    print(f"Cleaned categories:  {len(clean_cats)} - {sorted(clean_cats)}")
    print(f"Categories match: {'✓ YES' if orig_cats == clean_cats else '✗ NO'}")
    
    print("\n3. WORK COUNT PER CATEGORY")
    print("-" * 70)
    total_orig = 0
    total_clean = 0
    all_match = True
    
    for cat in sorted(orig_cats):
        orig_count = len(original['categories'][cat].get('works', []))
        clean_count = len(cleaned['categories'][cat].get('works', []))
        total_orig += orig_count
        total_clean += clean_count
        match = orig_count == clean_count
        if not match:
            all_match = False
        status = '✓' if match else '✗'
        print(f"  {cat:30s}: {orig_count:3d} -> {clean_count:3d} {status}")
    
    print(f"\n  {'TOTAL':30s}: {total_orig:3d} -> {total_clean:3d}")
    print(f"  All counts match: {'✓ YES' if all_match else '✗ NO'}")
    
    print("\n4. URL INTEGRITY CHECK")
    print("-" * 70)
    orig_urls = set()
    clean_urls = set()
    
    for cat_data in original['categories'].values():
        for work in cat_data.get('works', []):
            if 'url' in work:
                orig_urls.add(work['url'])
    
    for cat_data in cleaned['categories'].values():
        for work in cat_data.get('works', []):
            if 'url' in work:
                clean_urls.add(work['url'])
    
    print(f"Original URLs: {len(orig_urls)}")
    print(f"Cleaned URLs:  {len(clean_urls)}")
    
    missing_urls = orig_urls - clean_urls
    extra_urls = clean_urls - orig_urls
    
    if missing_urls:
        print(f"\n✗ MISSING URLs in cleaned: {len(missing_urls)}")
        for url in list(missing_urls)[:5]:
            print(f"  - {url}")
    
    if extra_urls:
        print(f"\n✗ EXTRA URLs in cleaned: {len(extra_urls)}")
        for url in list(extra_urls)[:5]:
            print(f"  - {url}")
    
    if not missing_urls and not extra_urls:
        print("✓ All URLs preserved")
    
    print("\n5. CONTENT INTEGRITY CHECK")
    print("-" * 70)
    orig_content_count = 0
    clean_content_count = 0
    orig_empty = 0
    clean_empty = 0
    
    for cat_data in original['categories'].values():
        for work in cat_data.get('works', []):
            if 'content' in work:
                orig_content_count += 1
                if not work['content'].strip():
                    orig_empty += 1
    
    for cat_data in cleaned['categories'].values():
        for work in cat_data.get('works', []):
            if 'content' in work:
                clean_content_count += 1
                if not work['content'].strip():
                    clean_empty += 1
    
    print(f"Original works with content: {orig_content_count}")
    print(f"Cleaned works with content:  {clean_content_count}")
    print(f"Content count match: {'✓ YES' if orig_content_count == clean_content_count else '✗ NO'}")
    
    if orig_empty > 0 or clean_empty > 0:
        print(f"\nEmpty content fields:")
        print(f"  Original: {orig_empty}")
        print(f"  Cleaned:  {clean_empty}")
    
    print("\n6. TITLE CHANGES")
    print("-" * 70)
    title_changes = []
    
    for cat_name in original['categories']:
        orig_works = original['categories'][cat_name].get('works', [])
        clean_works = cleaned['categories'][cat_name].get('works', [])
        
        for orig_w, clean_w in zip(orig_works, clean_works):
            if orig_w.get('url') == clean_w.get('url'):
                if orig_w.get('title') != clean_w.get('title'):
                    title_changes.append({
                        'original': orig_w.get('title'),
                        'cleaned': clean_w.get('title'),
                        'category': cat_name
                    })
    
    print(f"Titles changed: {len(title_changes)}")
    if title_changes:
        print("\nSample changes:")
        for change in title_changes[:10]:
            print(f"  {change['original']}")
            print(f"  → {change['cleaned']}")
            print()
    
    print("\n7. CONTENT CHANGES (COLONS REMOVED)")
    print("-" * 70)
    content_changes = 0
    sample_changes = []
    
    for cat_name in original['categories']:
        orig_works = original['categories'][cat_name].get('works', [])
        clean_works = cleaned['categories'][cat_name].get('works', [])
        
        for orig_w, clean_w in zip(orig_works, clean_works):
            if orig_w.get('url') == clean_w.get('url'):
                orig_content = orig_w.get('content', '')
                clean_content = clean_w.get('content', '')
                
                if orig_content != clean_content:
                    content_changes += 1
                    if len(sample_changes) < 3:
                        sample_changes.append({
                            'title': clean_w.get('title'),
                            'original_sample': orig_content[:100],
                            'cleaned_sample': clean_content[:100]
                        })
    
    print(f"Content modified: {content_changes} works")
    if sample_changes:
        print("\nSample content changes:")
        for i, change in enumerate(sample_changes, 1):
            print(f"\n  {i}. {change['title']}")
            print(f"     Original: {change['original_sample'][:60]}...")
            print(f"     Cleaned:  {change['cleaned_sample'][:60]}...")
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    all_good = (
        orig_cats == clean_cats and
        total_orig == total_clean and
        len(missing_urls) == 0 and
        len(extra_urls) == 0 and
        orig_content_count == clean_content_count
    )
    
    if all_good:
        print("✓ ALL DATA PRESERVED")
        print(f"✓ Total works: {total_clean}")
        print(f"✓ Title cleanups: {len(title_changes)}")
        print(f"✓ Content cleanups (colons removed): {content_changes}")
        print("\nThe cleaned file is ready for use!")
    else:
        print("✗ ISSUES DETECTED - Review above sections")
    
    return all_good

if __name__ == '__main__':
    compare_files()
