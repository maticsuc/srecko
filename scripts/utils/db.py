"""
Database connection and utility functions.
"""

import os
import sys
from typing import Optional
import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class DatabaseError(Exception):
    """Custom exception for database errors."""
    pass


def get_connection() -> connection:
    """
    Create and return a PostgreSQL database connection.

    Supports two modes:
      - DATABASE_URL env var (single connection string, used by Supabase)
      - Individual DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD vars (local dev)

    Returns:
        psycopg2 connection object

    Raises:
        DatabaseError: If connection fails
    """
    try:
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            conn = psycopg2.connect(database_url)
        else:
            conn = psycopg2.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                port=os.getenv('DB_PORT', '5432'),
                dbname=os.getenv('DB_NAME', 'srecko_kosovel'),
                user=os.getenv('DB_USER', 'postgres'),
                password=os.getenv('DB_PASSWORD', '')
            )
        return conn
    except psycopg2.OperationalError as e:
        raise DatabaseError(f"Failed to connect to database: {e}")


def get_cursor(conn: connection, dict_cursor: bool = True):
    """
    Get a cursor from the connection.
    
    Args:
        conn: Database connection
        dict_cursor: If True, return RealDictCursor (rows as dicts)
        
    Returns:
        Database cursor
    """
    if dict_cursor:
        return conn.cursor(cursor_factory=RealDictCursor)
    return conn.cursor()


def execute_sql_file(conn: connection, filepath: str) -> None:
    """
    Execute SQL commands from a file.
    
    Args:
        conn: Database connection
        filepath: Path to SQL file
        
    Raises:
        DatabaseError: If execution fails
        FileNotFoundError: If SQL file not found
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"SQL file not found: {filepath}")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()
        cursor.close()
        
    except psycopg2.Error as e:
        conn.rollback()
        raise DatabaseError(f"Failed to execute SQL file {filepath}: {e}")


def test_connection() -> bool:
    """
    Test database connection.
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        cursor.close()
        conn.close()
        print(f"✓ Connected to PostgreSQL")
        print(f"  Version: {version[0]}")
        return True
    except DatabaseError as e:
        print(f"✗ Connection failed: {e}")
        return False


def check_extensions() -> dict:
    """
    Check if required PostgreSQL extensions are installed.
    
    Returns:
        Dictionary with extension names as keys and boolean status as values
    """
    required_extensions = ['vector', 'pg_trgm']
    results = {}
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT extname 
            FROM pg_extension 
            WHERE extname IN ('vector', 'pg_trgm');
        """)
        
        installed = [row[0] for row in cursor.fetchall()]
        
        for ext in required_extensions:
            results[ext] = ext in installed
        
        cursor.close()
        conn.close()
        
    except DatabaseError as e:
        print(f"Error checking extensions: {e}")
        return {ext: False for ext in required_extensions}
    
    return results


def get_table_counts() -> dict:
    """
    Get row counts for all main tables.
    
    Returns:
        Dictionary with table names and row counts
    """
    tables = ['authors', 'categories', 'works', 'tags', 'work_tags']
    counts = {}
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table};")
            counts[table] = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
    except (DatabaseError, psycopg2.Error) as e:
        print(f"Error getting table counts: {e}")
        return {}
    
    return counts


if __name__ == "__main__":
    """Test database connection and extensions."""
    print("Testing database connection...")
    print()
    
    if test_connection():
        print()
        print("Checking required extensions...")
        extensions = check_extensions()
        
        for ext, installed in extensions.items():
            status = "✓" if installed else "✗"
            print(f"  {status} {ext}")
        
        print()
        print("Checking table counts...")
        counts = get_table_counts()
        
        if counts:
            for table, count in counts.items():
                print(f"  {table}: {count} rows")
        else:
            print("  (No tables found or error occurred)")
    else:
        print("\nPlease check your .env file and ensure PostgreSQL is running.")
        sys.exit(1)
