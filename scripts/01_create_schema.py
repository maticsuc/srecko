#!/usr/bin/env python3
"""
Create the PostgreSQL database schema for Srečko Kosovel database.

This script:
1. Connects to PostgreSQL
2. Checks for required extensions
3. Runs the initial schema migration
4. Verifies the schema was created successfully
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to import utils
sys.path.insert(0, str(Path(__file__).parent))

from utils.db import (
    get_connection,
    execute_sql_file,
    check_extensions,
    get_table_counts,
    DatabaseError
)


def main():
    """Main execution function."""
    print("=" * 60)
    print("Srečko Kosovel Database - Schema Creation")
    print("=" * 60)
    print()
    
    # Path to migration file
    migrations_dir = Path(__file__).parent.parent / "migrations"
    schema_file = migrations_dir / "001_initial_schema.sql"
    
    if not schema_file.exists():
        print(f"✗ Migration file not found: {schema_file}")
        sys.exit(1)
    
    print(f"Migration file: {schema_file}")
    print()
    
    try:
        # Connect to database
        print("Step 1: Connecting to database...")
        conn = get_connection()
        print("✓ Connected successfully")
        print()
        
        # Check extensions before running migration
        print("Step 2: Checking required extensions...")
        extensions = check_extensions()
        
        missing_extensions = [ext for ext, installed in extensions.items() if not installed]
        
        if missing_extensions:
            print(f"✗ Missing extensions: {', '.join(missing_extensions)}")
            print("\nThe migration will attempt to install them.")
            print("If this fails, you may need superuser privileges.")
            print()
        else:
            print("✓ All required extensions are installed")
            print()
        
        # Execute schema migration
        print("Step 3: Running schema migration...")
        print(f"  Executing: {schema_file.name}")
        
        execute_sql_file(conn, str(schema_file))
        
        print("✓ Schema migration completed successfully")
        print()
        
        # Verify schema
        print("Step 4: Verifying schema...")
        
        # Check extensions again
        extensions = check_extensions()
        for ext, installed in extensions.items():
            status = "✓" if installed else "✗"
            print(f"  {status} Extension: {ext}")
        
        # Check tables
        counts = get_table_counts()
        print()
        print("  Tables created:")
        for table in ['authors', 'categories', 'works', 'tags', 'work_tags']:
            if table in counts:
                print(f"    ✓ {table}")
            else:
                print(f"    ✗ {table} (not found)")
        
        print()
        print("=" * 60)
        print("✓ Schema creation completed successfully!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("  1. Run: python scripts/02_import_data.py")
        print("  2. Run: python scripts/03_generate_embeddings.py")
        print()
        
        conn.close()
        
    except DatabaseError as e:
        print(f"✗ Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
