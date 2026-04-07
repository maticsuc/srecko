#!/usr/bin/env python3
import json
import re

def clean_content(content):
    if not content:
        return ""
    
    result = content
    
    result = re.sub(r'<poem>|</poem>', '', result, flags=re.IGNORECASE)
    result = re.sub(r'<p>|</p>', '', result, flags=re.IGNORECASE)
    result = re.sub(r'<br\s*/?>', '\n', result, flags=re.IGNORECASE)
    result = re.sub(r'<poem/>', '', result, flags=re.IGNORECASE)
    
    result = re.sub(r'\{\{[^}]+\}\}', '', result, flags=re.IGNORECASE)
    
    result = re.sub(r'\[\[Kategori[^\]]+\]\]', '', result, flags=re.IGNORECASE)
    result = re.sub(r'\[\[[^\]|]+\|([^\]]+)\]\]', r'\1', result)
    result = re.sub(r'\[\[([^\]|]+)\]\]', r'\1', result)
    
    result = re.sub(r"'''", "", result)
    result = re.sub(r"''", "", result)
    
    lines = result.split('\n')
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if '=' in line:
            continue
        if line.startswith('|'):
            continue
        if line.startswith('!'):
            continue
        if line.startswith('{') or line.startswith('}'):
            continue
        cleaned_lines.append(line)
    
    result = '\n'.join(cleaned_lines)
    
    result = re.sub(r'^[A-Z][a-z]+$', '', result, flags=re.MULTILINE)
    result = re.sub(r'\n{3,}', '\n\n', result)
    result = result.strip()
    
    return result

def extract_title_from_content(content):
    match = re.search(r'\{\{naslov[^{}]*naslov\s*=\s*([^\n|}]+)', content, re.IGNORECASE)
    if match:
        title = match.group(1).strip()
        if title and title != '{{PAGENAME}}':
            return title
    
    match = re.search(r'\{\{naslov[^{}]*\}\s*([A-Z][a-z]+)', content, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    return None

def clean_title(title):
    if not title:
        return ""
    title = title.replace('_', ' ')
    title = title.strip()
    return title

def process_works(works):
    cleaned_works = []
    
    for work in works:
        title = work.get('title', '')
        content = work.get('content', '')
        url = work.get('url', '')
        
        extracted_title = extract_title_from_content(content)
        if extracted_title:
            title = extracted_title
        
        title = clean_title(title)
        content = clean_content(content)
        
        cleaned_works.append({
            'title': title,
            'content': content,
            'url': url
        })
    
    return cleaned_works

def main():
    with open('kosovel_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    cleaned_data = {
        'metadata': data.get('metadata', {}),
        'author_info': {},
        'categories': {}
    }
    
    for category_name, category_data in data.get('categories', {}).items():
        if isinstance(category_data, dict) and 'works' in category_data:
            cleaned_data['categories'][category_name] = {
                'index_page': category_data.get('index_page', ''),
                'works': process_works(category_data.get('works', []))
            }
    
    with open('kosovel_data_cleaned.json', 'w', encoding='utf-8') as f:
        json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
    
    print("Cleaned data saved to kosovel_data_cleaned.json")

if __name__ == '__main__':
    main()
