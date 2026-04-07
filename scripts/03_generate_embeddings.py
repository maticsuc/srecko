#!/usr/bin/env python3
"""
Generate embeddings for all works using Ollama.

This script:
1. Connects to Ollama API
2. Fetches all works without embeddings (or all works if --reembed flag)
3. Generates embeddings in batches
4. Updates the database with embeddings
5. Verifies embedding quality
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List, Tuple
import psycopg2

# Add parent directory to path to import utils
sys.path.insert(0, str(Path(__file__).parent))

from utils.db import get_connection, get_cursor, DatabaseError
from utils.embeddings import OllamaClient, OllamaError


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate embeddings for Srečko Kosovel works"
    )
    parser.add_argument(
        '--reembed',
        action='store_true',
        help='Re-generate embeddings for all works (including those with existing embeddings)'
    )
    parser.add_argument(
        '--model',
        type=str,
        default=None,
        help='Override embedding model (default: from .env or nomic-embed-text)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=10,
        help='Number of works to process in each batch (default: 10)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limit number of works to process (for testing)'
    )
    
    return parser.parse_args()


def get_works_to_embed(conn, reembed: bool = False, limit: int = None) -> List[Tuple]:
    """
    Fetch works that need embeddings.
    
    Returns:
        List of tuples: (work_id, title, content)
    """
    cursor = get_cursor(conn, dict_cursor=False)
    
    if reembed:
        # Get all works
        query = """
            SELECT id, title, content
            FROM works
            ORDER BY id
        """
    else:
        # Get only works without embeddings
        query = """
            SELECT id, title, content
            FROM works
            WHERE embedding IS NULL
            ORDER BY id
        """
    
    if limit:
        query += f" LIMIT {limit}"
    
    cursor.execute(query)
    works = cursor.fetchall()
    cursor.close()
    
    return works


def prepare_embedding_text(title: str, content: str, max_length: int = 1000) -> str:
    """
    Prepare text for embedding by combining title and content.

    Args:
        title: Work title
        content: Work content
        max_length: Maximum character length (default 1000)

    Returns:
        Combined text for embedding (truncated if needed)
    """
    # Combine title and content for better semantic representation
    # The title provides context, and content provides the main information
    combined = f"{title}\n\n{content}"

    # mxbai-embed-large is based on BERT with a 512-token limit.
    # Slovenian diacritical characters tokenize as multiple subword pieces,
    # so ~1000 chars is a safe upper bound (~300-400 tokens with safety margin).
    if len(combined) > max_length:
        combined = combined[:max_length]

    return combined


def update_embedding(conn, work_id: int, embedding: List[float]) -> bool:
    """
    Update work with embedding vector.
    
    Args:
        conn: Database connection
        work_id: Work ID
        embedding: Embedding vector
        
    Returns:
        True if successful, False otherwise
    """
    try:
        cursor = get_cursor(conn, dict_cursor=False)
        
        # Convert embedding to string format for pgvector
        embedding_str = '[' + ','.join(map(str, embedding)) + ']'
        
        cursor.execute("""
            UPDATE works
            SET embedding = %s::vector
            WHERE id = %s
        """, (embedding_str, work_id))
        
        cursor.close()
        return True
        
    except psycopg2.Error as e:
        print(f"    Warning: Failed to update embedding for work {work_id}: {e}")
        return False


def generate_embeddings(
    conn, 
    ollama: OllamaClient, 
    works: List[Tuple],
    batch_size: int = 10
) -> Tuple[int, int]:
    """
    Generate embeddings for works.
    
    Args:
        conn: Database connection
        ollama: Ollama client
        works: List of (work_id, title, content) tuples
        batch_size: Commit after this many successful embeddings
        
    Returns:
        Tuple of (successful_count, failed_count)
    """
    total = len(works)
    successful = 0
    failed = 0
    
    print(f"\nGenerating embeddings for {total} works...")
    print(f"Batch size: {batch_size}")
    print()
    
    for i, (work_id, title, content) in enumerate(works, 1):
        try:
            # Prepare text
            text = prepare_embedding_text(title, content)
            
            # Generate embedding
            embedding = ollama.generate_embedding(text)
            
            # Update database
            if update_embedding(conn, work_id, embedding):
                successful += 1
                
                # Commit in batches
                if successful % batch_size == 0:
                    conn.commit()
                    print(f"  [{i}/{total}] Committed batch (✓ {successful}, ✗ {failed})")
            else:
                failed += 1
            
        except OllamaError as e:
            print(f"  [{i}/{total}] Failed to generate embedding for '{title[:50]}...': {e}")
            failed += 1
        except Exception as e:
            print(f"  [{i}/{total}] Unexpected error for '{title[:50]}...': {e}")
            failed += 1
    
    # Final commit
    conn.commit()
    
    print()
    print(f"✓ Generation complete: {successful} successful, {failed} failed")
    
    return successful, failed


def verify_embeddings(conn):
    """Verify embedding generation results."""
    print("\nVerifying embeddings...")
    
    cursor = get_cursor(conn, dict_cursor=True)
    
    # Count works with/without embeddings
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(embedding) as with_embedding,
            COUNT(*) - COUNT(embedding) as without_embedding
        FROM works;
    """)
    
    stats = cursor.fetchone()
    
    print(f"  Total works:         {stats['total']}")
    print(f"  With embeddings:     {stats['with_embedding']}")
    print(f"  Without embeddings:  {stats['without_embedding']}")
    
    # Check embedding dimensions
    cursor.execute("""
        SELECT 
            id, 
            title,
            vector_dims(embedding) as dimension
        FROM works
        WHERE embedding IS NOT NULL
        LIMIT 5;
    """)
    
    print("\n  Sample embedding dimensions:")
    for row in cursor.fetchall():
        print(f"    Work {row['id']:3d}: {row['dimension']} dims - '{row['title'][:50]}'")
    
    cursor.close()
    
    if stats['without_embedding'] == 0:
        print("\n✓ All works have embeddings!")
    else:
        print(f"\n⚠ {stats['without_embedding']} works still need embeddings")


def print_summary(successful: int, failed: int, total_time: float):
    """Print generation summary."""
    print("\n" + "=" * 60)
    print("Embedding Generation Summary")
    print("=" * 60)
    print(f"\nSuccessful:  {successful}")
    print(f"Failed:      {failed}")
    print(f"Total time:  {total_time:.2f} seconds")
    
    if successful > 0:
        print(f"Avg time:    {total_time/successful:.2f} seconds per embedding")
    
    print("\n" + "=" * 60)
    
    if failed == 0:
        print("✓ All embeddings generated successfully!")
    else:
        print(f"⚠ {failed} embeddings failed - check logs above")
    
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Test semantic search: python scripts/test_search.py")
    print("  2. Build LangChain integration")
    print()


def main():
    """Main execution function."""
    args = parse_arguments()
    
    print("=" * 60)
    print("Srečko Kosovel Database - Embedding Generation")
    print("=" * 60)
    print()
    
    import time
    start_time = time.time()
    
    try:
        # Initialize Ollama client
        print("Step 1: Connecting to Ollama...")
        ollama = OllamaClient(model=args.model)
        
        if not ollama.is_available():
            print("✗ Ollama is not running")
            print("\nPlease start Ollama:")
            print("  ollama serve")
            sys.exit(1)
        
        print(f"✓ Ollama is running")
        print(f"  Model: {ollama.model}")
        print(f"  Endpoint: {ollama.base_url}")
        
        # Check embedding dimension
        print("\nChecking embedding dimension...")
        dimension = ollama.get_embedding_dimension()
        print(f"✓ Embedding dimension: {dimension}")
        
        expected_dim = int(os.getenv('EMBEDDING_DIMENSION', '1024'))
        if dimension != expected_dim:
            print(f"\n⚠ Warning: Expected {expected_dim} dimensions, got {dimension}")
            print(f"  Check EMBEDDING_DIMENSION in .env (currently {expected_dim}).")
            sys.exit(1)
        
        # Connect to database
        print("\nStep 2: Connecting to database...")
        conn = get_connection()
        print("✓ Connected successfully")
        
        # Get works to embed
        print("\nStep 3: Fetching works to embed...")
        works = get_works_to_embed(conn, reembed=args.reembed, limit=args.limit)
        
        if not works:
            print("✓ No works need embeddings")
            verify_embeddings(conn)
            conn.close()
            sys.exit(0)
        
        print(f"✓ Found {len(works)} works to process")
        
        if args.reembed:
            print("  (Re-embedding mode: will overwrite existing embeddings)")
        
        if args.limit:
            print(f"  (Limited to {args.limit} works for testing)")
        
        # Generate embeddings
        print("\nStep 4: Generating embeddings...")
        successful, failed = generate_embeddings(
            conn, 
            ollama, 
            works,
            batch_size=args.batch_size
        )
        
        # Verify results
        verify_embeddings(conn)
        
        # Close connection
        conn.close()
        
        # Print summary
        total_time = time.time() - start_time
        print_summary(successful, failed, total_time)
        
        # Exit with error code if any failed
        if failed > 0:
            sys.exit(1)
        
    except DatabaseError as e:
        print(f"✗ Database error: {e}")
        sys.exit(1)
    except OllamaError as e:
        print(f"✗ Ollama error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n✗ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
