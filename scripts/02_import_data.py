#!/usr/bin/env python3
"""
Import data from kosovel_data_cleaned.json into PostgreSQL database.

This script:
1. Loads data from JSON file
2. Inserts author information
3. Creates categories with slugs
4. Generates and inserts tags
5. Imports all works with metadata
6. Links works to tags
7. Calculates word counts
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Set
import psycopg2
from psycopg2.extras import execute_values

# Add parent directory to path to import utils
sys.path.insert(0, str(Path(__file__).parent))

from utils.db import get_connection, get_cursor, DatabaseError
from utils.slugify import slugify, CATEGORY_SLUGS, get_category_display_name


def load_json_data(filepath: str) -> dict:
    """Load and parse JSON data file."""
    print(f"Loading data from: {filepath}")
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Data file not found: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"✓ Loaded data successfully")
    return data


def insert_author(conn, data: dict) -> int:
    """Insert author information and return author_id."""
    print("\nStep 1: Inserting author information...")
    
    author_info = data.get('author', {})
    
    cursor = get_cursor(conn, dict_cursor=False)
    
    cursor.execute("""
        INSERT INTO authors (name, birth_year, death_year, biography)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (name) DO UPDATE 
        SET birth_year = EXCLUDED.birth_year,
            death_year = EXCLUDED.death_year,
            biography = EXCLUDED.biography
        RETURNING id;
    """, (
        author_info.get('name', 'Srečko Kosovel'),
        author_info.get('birth_year', 1904),
        author_info.get('death_year', 1926),
        author_info.get('biography', 'Slovenski pesnik ekspresionizma in konstruktivizma.')
    ))
    
    author_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    
    print(f"✓ Author inserted (ID: {author_id})")
    return author_id


def insert_categories(conn, data: dict) -> Dict[str, int]:
    """Insert categories and return mapping of slug -> category_id."""
    print("\nStep 2: Inserting categories...")
    
    categories = data.get('categories', {})
    category_map = {}
    
    cursor = get_cursor(conn, dict_cursor=False)
    
    for category_key, category_data in categories.items():
        # Get display name from slug
        display_name = get_category_display_name(category_key)
        work_count = len(category_data.get('works', []))
        
        cursor.execute("""
            INSERT INTO categories (name, slug, description)
            VALUES (%s, %s, %s)
            ON CONFLICT (slug) DO UPDATE 
            SET name = EXCLUDED.name,
                description = EXCLUDED.description
            RETURNING id;
        """, (
            display_name,
            category_key,
            f"{display_name} - {work_count} works"
        ))
        
        category_id = cursor.fetchone()[0]
        category_map[category_key] = category_id
        
        print(f"  ✓ {display_name} (slug: {category_key}, {work_count} works)")
    
    conn.commit()
    cursor.close()
    
    print(f"✓ Inserted {len(category_map)} categories")
    return category_map


def generate_tags_from_categories(categories: Dict) -> Set[str]:
    """Generate minimal tags from category names."""
    tags = set()
    
    # Add category-based tags
    for category_key in categories.keys():
        display_name = get_category_display_name(category_key)
        tags.add(display_name)
    
    # Add some common thematic tags
    common_tags = {
        'poezija', 'proza', 'kritika', 'esej',
        'lirika', 'avantgarda', 'ekspresionizem', 'konstruktivizem'
    }
    tags.update(common_tags)
    
    return tags


def insert_tags(conn, data: dict) -> Dict[str, int]:
    """Insert tags and return mapping of name -> tag_id."""
    print("\nStep 3: Generating and inserting tags...")
    
    categories = data.get('categories', {})
    tags = generate_tags_from_categories(categories)
    tag_map = {}
    
    cursor = get_cursor(conn, dict_cursor=False)
    
    for tag_name in sorted(tags):
        tag_slug = slugify(tag_name, separator='-')
        
        cursor.execute("""
            INSERT INTO tags (name, slug)
            VALUES (%s, %s)
            ON CONFLICT (slug) DO UPDATE 
            SET name = EXCLUDED.name
            RETURNING id;
        """, (tag_name, tag_slug))
        
        tag_id = cursor.fetchone()[0]
        tag_map[tag_name] = tag_id
    
    conn.commit()
    cursor.close()
    
    print(f"✓ Inserted {len(tag_map)} tags")
    return tag_map


def count_words(text: str) -> int:
    """Count words in text."""
    if not text:
        return 0
    return len(text.split())


def insert_works(conn, data: dict, author_id: int, category_map: Dict[str, int]) -> Dict[str, int]:
    """Insert all works and return mapping of title -> work_id."""
    print("\nStep 4: Inserting works...")
    
    categories = data.get('categories', {})
    work_map = {}
    total_works = 0
    
    cursor = get_cursor(conn, dict_cursor=False)
    
    for category_key, category_data in categories.items():
        works = category_data.get('works', [])
        category_id = category_map[category_key]
        
        print(f"\n  Category: {get_category_display_name(category_key)}")
        
        for i, work in enumerate(works, 1):
            title = work.get('title', 'Untitled')
            content = work.get('content', '')
            url = work.get('url', '')
            word_count = count_words(content)
            
            # Skip if URL is empty (shouldn't happen but be safe)
            if not url:
                print(f"    Warning: Skipping work '{title}' - no URL")
                continue
            
            cursor.execute("""
                INSERT INTO works (
                    title, content, url, author_id, category_id, 
                    word_count, language
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (url) DO UPDATE 
                SET title = EXCLUDED.title,
                    content = EXCLUDED.content,
                    category_id = EXCLUDED.category_id,
                    word_count = EXCLUDED.word_count
                RETURNING id;
            """, (
                title,
                content,
                url,
                author_id,
                category_id,
                word_count,
                'sl'  # Slovenian
            ))
            
            work_id = cursor.fetchone()[0]
            # Use URL as key to avoid duplicate titles
            work_map[url] = work_id
            total_works += 1
            
            if i % 50 == 0:
                print(f"    Inserted {i}/{len(works)} works...")
        
        print(f"  ✓ Inserted {len(works)} works")
        conn.commit()
    
    cursor.close()
    
    print(f"\n✓ Total works inserted: {total_works}")
    return work_map


def link_works_to_tags(conn, data: dict, work_map: Dict[str, int], tag_map: Dict[str, int]):
    """Create work-tag relationships."""
    print("\nStep 5: Linking works to tags...")
    
    categories = data.get('categories', {})
    links = []
    
    for category_key, category_data in categories.items():
        category_display = get_category_display_name(category_key)
        
        # Get tag_id for this category
        if category_display not in tag_map:
            continue
        
        tag_id = tag_map[category_display]
        works = category_data.get('works', [])
        
        for work in works:
            url = work.get('url', '')
            if url and url in work_map:
                work_id = work_map[url]
                links.append((work_id, tag_id))
    
    # Bulk insert work-tag links
    if links:
        cursor = get_cursor(conn, dict_cursor=False)
        
        execute_values(
            cursor,
            """
            INSERT INTO work_tags (work_id, tag_id)
            VALUES %s
            ON CONFLICT (work_id, tag_id) DO NOTHING
            """,
            links
        )
        
        conn.commit()
        cursor.close()
        
        print(f"✓ Created {len(links)} work-tag links")
    else:
        print("  No links to create")


def print_summary(conn):
    """Print import summary statistics."""
    print("\n" + "=" * 60)
    print("Import Summary")
    print("=" * 60)
    
    cursor = get_cursor(conn, dict_cursor=True)
    
    # Count totals
    cursor.execute("SELECT COUNT(*) as count FROM authors;")
    authors = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM categories;")
    categories = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM works;")
    works = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM tags;")
    tags = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM work_tags;")
    work_tags = cursor.fetchone()['count']
    
    print(f"\nDatabase Statistics:")
    print(f"  Authors:     {authors}")
    print(f"  Categories:  {categories}")
    print(f"  Works:       {works}")
    print(f"  Tags:        {tags}")
    print(f"  Work-Tags:   {work_tags}")
    
    # Category breakdown
    print(f"\nWorks by Category:")
    cursor.execute("""
        SELECT c.name, COUNT(w.id) as count
        FROM categories c
        LEFT JOIN works w ON w.category_id = c.id
        GROUP BY c.name
        ORDER BY count DESC;
    """)
    
    for row in cursor.fetchall():
        print(f"  {row['name']:30} {row['count']:4} works")
    
    cursor.close()
    
    print("\n" + "=" * 60)
    print("✓ Import completed successfully!")
    print("=" * 60)
    print("\nNext step:")
    print("  Run: python scripts/03_generate_embeddings.py")
    print()


def main():
    """Main execution function."""
    print("=" * 60)
    print("Srečko Kosovel Database - Data Import")
    print("=" * 60)
    print()
    
    # Path to data file
    data_file = Path(__file__).parent.parent / "scraping" / "kosovel_data_cleaned_final.json"
    
    try:
        # Load JSON data
        data = load_json_data(str(data_file))
        
        # Connect to database
        print("\nConnecting to database...")
        conn = get_connection()
        print("✓ Connected successfully")
        
        # Import data
        author_id = insert_author(conn, data)
        category_map = insert_categories(conn, data)
        tag_map = insert_tags(conn, data)
        work_map = insert_works(conn, data, author_id, category_map)
        link_works_to_tags(conn, data, work_map, tag_map)
        
        # Print summary
        print_summary(conn)
        
        conn.close()
        
    except FileNotFoundError as e:
        print(f"✗ File error: {e}")
        sys.exit(1)
    except DatabaseError as e:
        print(f"✗ Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
