#!/usr/bin/env python3
"""
Comprehensive Test Suite for Srečko Kosovel AI Chat Database

This script provides standardized tests to verify the entire system state:
- Database connectivity and schema
- Data import completeness
- Embedding generation
- Search functionality (semantic, keyword, hybrid)
- RAG chain and chat interface
- Environment configuration

Usage:
    python tests_srecko.py                    # Run all tests
    python tests_srecko.py -q database        # Run only database tests
    python tests_srecko.py -q search          # Run only search tests
    python tests_srecko.py --json             # Output results as JSON
    python tests_srecko.py --verbose          # Verbose output

Exit codes:
    0 = All tests passed
    1 = Some tests failed
    2 = Critical error (cannot continue)
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

# Load environment early
load_dotenv()


class TestResult:
    """Represents the result of a single test."""

    def __init__(self, name: str, category: str, passed: bool, message: str = "", duration: float = 0):
        self.name = name
        self.category = category
        self.passed = passed
        self.message = message
        self.duration = duration
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category,
            "passed": self.passed,
            "message": self.message,
            "duration": f"{self.duration:.2f}s",
            "timestamp": self.timestamp,
        }


class TestSuite:
    """Manages and runs a suite of tests."""

    def __init__(self, verbose: bool = False, json_output: bool = False):
        self.verbose = verbose
        self.json_output = json_output
        self.results: List[TestResult] = []
        self.start_time = None
        self.end_time = None

    def add_result(self, result: TestResult):
        """Add a test result."""
        self.results.append(result)

    def print_result(self, result: TestResult):
        """Print a single test result."""
        if self.json_output:
            return

        symbol = "✓" if result.passed else "✗"
        status = "PASS" if result.passed else "FAIL"

        duration_str = f"({result.duration:.2f}s)" if result.duration > 0 else ""
        print(f"  {symbol} {result.name} {duration_str}")

        if result.message and (not result.passed or self.verbose):
            for line in result.message.split("\n"):
                print(f"    {line}")

    def summary(self) -> Dict[str, int]:
        """Get summary statistics."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed

        by_category = {}
        for r in self.results:
            if r.category not in by_category:
                by_category[r.category] = {"total": 0, "passed": 0}
            by_category[r.category]["total"] += 1
            if r.passed:
                by_category[r.category]["passed"] += 1

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "by_category": by_category,
        }

    def print_summary(self):
        """Print test summary."""
        if self.json_output:
            return

        summary = self.summary()
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print(f"Total: {summary['total']} | Passed: {summary['passed']} | Failed: {summary['failed']}")
        print()

        for category, stats in summary['by_category'].items():
            passed = stats['passed']
            total = stats['total']
            pct = (passed / total * 100) if total > 0 else 0
            print(f"  {category}: {passed}/{total} ({pct:.0f}%)")

        print()
        if summary['failed'] == 0:
            print("🎉 All tests passed!")
        else:
            print(f"⚠ {summary['failed']} test(s) failed")

        if self.start_time and self.end_time:
            elapsed = (self.end_time - self.start_time).total_seconds()
            print(f"Duration: {elapsed:.2f}s")

    def export_json(self) -> str:
        """Export results as JSON."""
        summary = self.summary()
        return json.dumps({
            "timestamp": datetime.now().isoformat(),
            "summary": summary,
            "results": [r.to_dict() for r in self.results],
        }, indent=2)


# ============================================================================
# Test Functions
# ============================================================================

def test_environment(suite: TestSuite) -> bool:
    """Test environment configuration."""
    print("\n[Environment]")

    required_vars = ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD", "OLLAMA_BASE_URL"]
    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        result = TestResult(
            "Environment variables",
            "environment",
            False,
            f"Missing: {', '.join(missing)}\nCheck .env file"
        )
    else:
        result = TestResult(
            "Environment variables",
            "environment",
            True,
            f"DB_HOST={os.getenv('DB_HOST')}, OLLAMA_BASE_URL={os.getenv('OLLAMA_BASE_URL')}"
        )

    suite.add_result(result)
    suite.print_result(result)

    return result.passed


def test_database_connection(suite: TestSuite) -> bool:
    """Test PostgreSQL connection."""
    print("\n[Database]")

    import time
    start = time.time()

    try:
        from scripts.utils.db import get_connection

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()

        duration = time.time() - start
        result = TestResult(
            "Database connection",
            "database",
            True,
            duration=duration
        )
    except Exception as e:
        result = TestResult(
            "Database connection",
            "database",
            False,
            f"Error: {str(e)[:100]}"
        )

    suite.add_result(result)
    suite.print_result(result)

    return result.passed


def test_database_schema(suite: TestSuite) -> bool:
    """Test database schema completeness."""
    import time
    start = time.time()

    try:
        from scripts.utils.db import get_connection, get_cursor

        conn = get_connection()
        cursor = get_cursor(conn, dict_cursor=True)

        # Check required tables
        tables = ["authors", "categories", "works", "tags", "work_tags"]
        missing_tables = []

        for table in tables:
            cursor.execute(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = '{table}'
                )
            """)
            if not cursor.fetchone()['exists']:
                missing_tables.append(table)

        cursor.close()
        conn.close()

        duration = time.time() - start

        if missing_tables:
            result = TestResult(
                "Database schema",
                "database",
                False,
                f"Missing tables: {', '.join(missing_tables)}",
                duration
            )
        else:
            result = TestResult(
                "Database schema",
                "database",
                True,
                f"All {len(tables)} tables exist",
                duration
            )
    except Exception as e:
        result = TestResult(
            "Database schema",
            "database",
            False,
            f"Error: {str(e)[:100]}"
        )

    suite.add_result(result)
    suite.print_result(result)

    return result.passed


def test_data_import(suite: TestSuite) -> bool:
    """Test data import completeness."""
    import time
    start = time.time()

    try:
        from scripts.utils.db import get_connection, get_cursor

        conn = get_connection()
        cursor = get_cursor(conn, dict_cursor=True)

        # Expected counts
        queries = {
            "Authors": "SELECT COUNT(*) as count FROM authors",
            "Categories": "SELECT COUNT(*) as count FROM categories",
            "Works": "SELECT COUNT(*) as count FROM works",
            "Tags": "SELECT COUNT(*) as count FROM tags",
            "Work-Tag relationships": "SELECT COUNT(*) as count FROM work_tags",
        }

        counts = {}
        all_have_data = True

        for name, query in queries.items():
            cursor.execute(query)
            count = cursor.fetchone()['count']
            counts[name] = count
            if count == 0:
                all_have_data = False

        cursor.close()
        conn.close()

        duration = time.time() - start

        message = "\n".join([f"{k}: {v}" for k, v in counts.items()])

        result = TestResult(
            "Data import",
            "database",
            all_have_data and counts['Works'] >= 450,
            message,
            duration
        )
    except Exception as e:
        result = TestResult(
            "Data import",
            "database",
            False,
            f"Error: {str(e)[:100]}"
        )

    suite.add_result(result)
    suite.print_result(result)

    return result.passed


def test_embeddings(suite: TestSuite) -> bool:
    """Test embedding generation and storage."""
    import time
    start = time.time()

    try:
        from scripts.utils.db import get_connection, get_cursor

        conn = get_connection()
        cursor = get_cursor(conn, dict_cursor=True)

        cursor.execute("SELECT COUNT(*) as count FROM works WHERE embedding IS NOT NULL")
        embedding_count = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM works")
        total_count = cursor.fetchone()['count']

        cursor.close()
        conn.close()

        duration = time.time() - start

        pct = (embedding_count / total_count * 100) if total_count > 0 else 0
        message = f"{embedding_count}/{total_count} works have embeddings ({pct:.0f}%)"

        result = TestResult(
            "Embeddings generated",
            "embeddings",
            embedding_count == total_count and total_count > 0,
            message,
            duration
        )
    except Exception as e:
        result = TestResult(
            "Embeddings generated",
            "embeddings",
            False,
            f"Error: {str(e)[:100]}"
        )

    suite.add_result(result)
    suite.print_result(result)

    return result.passed


def test_ollama_connection(suite: TestSuite) -> bool:
    """Test Ollama connection."""
    import time
    start = time.time()

    try:
        import requests
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        duration = time.time() - start

        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m.get("name", "unknown") for m in models]

            result = TestResult(
                "Ollama connection",
                "ollama",
                True,
                f"Connected, {len(models)} models available",
                duration
            )
        else:
            result = TestResult(
                "Ollama connection",
                "ollama",
                False,
                f"HTTP {response.status_code}",
                duration
            )
    except Exception as e:
        result = TestResult(
            "Ollama connection",
            "ollama",
            False,
            f"Error: {str(e)[:100]}"
        )

    suite.add_result(result)
    suite.print_result(result)

    return result.passed


def test_ollama_models(suite: TestSuite) -> bool:
    """Test required Ollama models."""
    import time
    start = time.time()

    try:
        import requests
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        embed_model = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
        chat_model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        duration = time.time() - start

        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m.get("name", "unknown") for m in models]

            has_embed = any(embed_model in m for m in model_names)
            has_chat = any(chat_model in m or m.startswith("llama") or m.startswith("qwen")
                          for m in model_names)

            missing = []
            if not has_embed:
                missing.append(embed_model)
            if not has_chat:
                missing.append(chat_model)

            message = f"Embedding: {has_embed}, Chat: {has_chat}"
            if missing:
                message += f"\nMissing: {', '.join(missing)}"

            result = TestResult(
                "Required Ollama models",
                "ollama",
                has_embed and has_chat,
                message,
                duration
            )
        else:
            result = TestResult(
                "Required Ollama models",
                "ollama",
                False,
                f"Cannot query models (HTTP {response.status_code})",
                duration
            )
    except Exception as e:
        result = TestResult(
            "Required Ollama models",
            "ollama",
            False,
            f"Error: {str(e)[:100]}"
        )

    suite.add_result(result)
    suite.print_result(result)

    return result.passed


def test_keyword_search(suite: TestSuite) -> bool:
    """Test keyword/full-text search."""
    import time
    start = time.time()

    try:
        from scripts.utils.db import get_connection, get_cursor

        conn = get_connection()
        cursor = get_cursor(conn, dict_cursor=True)

        cursor.execute("""
            SELECT COUNT(*) as count FROM works, plainto_tsquery('simple', 'kras') query
            WHERE search_vector @@ query
        """)
        result_count = cursor.fetchone()['count']

        cursor.close()
        conn.close()

        duration = time.time() - start

        result = TestResult(
            "Keyword search",
            "search",
            result_count > 0,
            f"Found {result_count} results for 'kras'",
            duration
        )
    except Exception as e:
        result = TestResult(
            "Keyword search",
            "search",
            False,
            f"Error: {str(e)[:100]}"
        )

    suite.add_result(result)
    suite.print_result(result)

    return result.passed


def test_semantic_search(suite: TestSuite) -> bool:
    """Test semantic/vector search."""
    import time
    start = time.time()

    try:
        from scripts.utils.db import get_connection, get_cursor
        import ollama

        # Generate embedding for test query
        embed_model = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
        response = ollama.embeddings(model=embed_model, prompt="kras landscape")
        query_embedding = response['embedding']

        # Search by similarity
        conn = get_connection()
        cursor = get_cursor(conn, dict_cursor=True)

        # First, check embedding dimensions match
        cursor.execute("""
            SELECT id, embedding FROM works
            WHERE embedding IS NOT NULL
            LIMIT 1
        """)

        row = cursor.fetchone()
        if row and row['embedding']:
            db_embedding = row['embedding']
            if len(db_embedding) != len(query_embedding):
                raise Exception(f"Embedding dimension mismatch: DB has {len(db_embedding)}D, query has {len(query_embedding)}D")

        # Perform semantic search
        cursor.execute("""
            SELECT id, title FROM works
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> %s::vector
            LIMIT 5
        """, (query_embedding,))

        results = cursor.fetchall()
        result_count = len(results)

        cursor.close()
        conn.close()

        duration = time.time() - start

        result = TestResult(
            "Semantic search",
            "search",
            result_count > 0,
            f"Found {result_count} results for embedding query",
            duration
        )
    except Exception as e:
        err_msg = str(e)
        if "dimension" in err_msg.lower():
            error_detail = f"Embedding dimension mismatch\n→ Run: python scripts/03_generate_embeddings.py"
        else:
            error_detail = f"Error: {err_msg[:100]}"

        result = TestResult(
            "Semantic search",
            "search",
            False,
            error_detail
        )

    suite.add_result(result)
    suite.print_result(result)

    return result.passed


def test_rag_chain(suite: TestSuite) -> bool:
    """Test RAG chain initialization and execution."""
    import time
    start = time.time()

    try:
        from langchain_rag.chains import create_rag_chain

        db_config = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", "5432")),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "database": os.getenv("DB_NAME"),
        }

        ollama_config = {
            "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            "model": os.getenv("OLLAMA_MODEL", "llama3.2:3b"),
            "embed_model": os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text"),
        }

        chain = create_rag_chain(db_config, ollama_config, top_k=5)
        duration = time.time() - start

        result = TestResult(
            "RAG chain initialization",
            "rag",
            True,
            "Chain created successfully",
            duration
        )
    except Exception as e:
        result = TestResult(
            "RAG chain initialization",
            "rag",
            False,
            f"Error: {str(e)[:100]}"
        )

    suite.add_result(result)
    suite.print_result(result)

    return result.passed


def test_rag_query(suite: TestSuite) -> bool:
    """Test RAG chain query execution."""
    import time
    start = time.time()

    try:
        from langchain_rag.chains import create_rag_chain

        db_config = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", "5432")),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "database": os.getenv("DB_NAME"),
        }

        ollama_config = {
            "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            "model": os.getenv("OLLAMA_MODEL", "llama3.2:3b"),
            "embed_model": os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text"),
        }

        chain = create_rag_chain(db_config, ollama_config, top_k=5)

        # Test with a simple query
        result_obj = chain.invoke("Tell me about Kras", return_sources=True)
        duration = time.time() - start

        has_answer = bool(result_obj.get('answer'))
        has_sources = len(result_obj.get('sources', [])) > 0

        message = f"Answer: {len(result_obj.get('answer', ''))} chars, Sources: {len(result_obj.get('sources', []))}"

        result = TestResult(
            "RAG query execution",
            "rag",
            has_answer and has_sources,
            message,
            duration
        )
    except Exception as e:
        result = TestResult(
            "RAG query execution",
            "rag",
            False,
            f"Error: {str(e)[:100]}"
        )

    suite.add_result(result)
    suite.print_result(result)

    return result.passed


def test_prompt_detection(suite: TestSuite) -> bool:
    """Test prompt type detection."""
    import time
    start = time.time()

    try:
        from langchain_rag.chains import create_rag_chain

        db_config = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", "5432")),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "database": os.getenv("DB_NAME"),
        }

        ollama_config = {
            "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            "model": os.getenv("OLLAMA_MODEL", "llama3.2:3b"),
            "embed_model": os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text"),
        }

        chain = create_rag_chain(db_config, ollama_config, top_k=5)

        test_cases = [
            ("Recite Zapevanje", "recitation"),
            ("Tell me about love", "qa"),
            ("Analyze your themes", "analysis"),
        ]

        detections = []
        for query, expected in test_cases:
            result_obj = chain.invoke(query, return_sources=False)
            actual = result_obj.get('prompt_type', 'unknown')
            detections.append((expected, actual, expected == actual))

        duration = time.time() - start

        all_correct = all(d[2] for d in detections)
        message = ", ".join([f"{e}->{a}{'✓' if c else '✗'}" for e, a, c in detections])

        result = TestResult(
            "Prompt type detection",
            "rag",
            all_correct,
            message,
            duration
        )
    except Exception as e:
        result = TestResult(
            "Prompt type detection",
            "rag",
            False,
            f"Error: {str(e)[:100]}"
        )

    suite.add_result(result)
    suite.print_result(result)

    return result.passed


def test_langchain_imports(suite: TestSuite) -> bool:
    """Test LangChain package imports."""
    import time
    start = time.time()

    try:
        import langchain
        import langchain_community

        duration = time.time() - start

        result = TestResult(
            "LangChain imports",
            "dependencies",
            True,
            f"langchain {langchain.__version__}",
            duration
        )
    except ImportError as e:
        result = TestResult(
            "LangChain imports",
            "dependencies",
            False,
            f"Import error: {str(e)[:100]}"
        )

    suite.add_result(result)
    suite.print_result(result)

    return result.passed


def test_ollama_import(suite: TestSuite) -> bool:
    """Test Ollama Python client."""
    import time
    start = time.time()

    try:
        import ollama
        duration = time.time() - start

        result = TestResult(
            "Ollama client",
            "dependencies",
            True,
            f"Ollama client available",
            duration
        )
    except ImportError as e:
        result = TestResult(
            "Ollama client",
            "dependencies",
            False,
            f"Import error: {str(e)[:100]}"
        )

    suite.add_result(result)
    suite.print_result(result)

    return result.passed


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Comprehensive Test Suite for Srečko Kosovel Database"
    )
    parser.add_argument(
        "-q", "--quick",
        dest="quick",
        action="store_true",
        help="Quick tests only (skip RAG chain tests)"
    )
    parser.add_argument(
        "-c", "--category",
        type=str,
        help="Run only tests from specific category (environment, database, embeddings, ollama, search, rag, dependencies)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )

    args = parser.parse_args()

    suite = TestSuite(verbose=args.verbose, json_output=args.json)
    suite.start_time = datetime.now()

    if not args.json:
        print("=" * 70)
        print("SREČKO KOSOVEL DATABASE TEST SUITE")
        print("=" * 70)

    # Run tests based on filters
    tests = [
        # Environment & Config
        ("environment", test_environment),

        # Dependencies
        ("dependencies", test_langchain_imports),
        ("dependencies", test_ollama_import),

        # Database
        ("database", test_database_connection),
        ("database", test_database_schema),
        ("database", test_data_import),

        # Embeddings
        ("embeddings", test_embeddings),

        # Ollama
        ("ollama", test_ollama_connection),
        ("ollama", test_ollama_models),

        # Search
        ("search", test_keyword_search),
        ("search", test_semantic_search),
    ]

    # Add RAG tests unless --quick
    if not args.quick:
        tests.extend([
            ("rag", test_rag_chain),
            ("rag", test_rag_query),
            ("rag", test_prompt_detection),
        ])

    # Filter by category if specified
    if args.category:
        tests = [(cat, func) for cat, func in tests if cat == args.category]

    # Run tests
    for category, test_func in tests:
        try:
            test_func(suite)
        except Exception as e:
            if not args.json:
                print(f"\n  ✗ Unexpected error: {e}")
            result = TestResult(
                test_func.__name__,
                category,
                False,
                f"Unexpected error: {str(e)[:100]}"
            )
            suite.add_result(result)

    suite.end_time = datetime.now()

    # Output results
    if args.json:
        print(suite.export_json())
    else:
        suite.print_summary()

    # Exit code
    summary = suite.summary()
    return 0 if summary['failed'] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
