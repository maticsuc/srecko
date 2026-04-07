"""
Search tools for the Srečko Kosovel poetry database.

Each function is a LangChain tool — a plain Python function decorated with @tool.
The LLM reads the docstring to decide when and how to call each one.

Four tools, four different search strategies:
  - get_poem:           "I want to read poem X"  →  fuzzy title match
  - search_by_keyword:  "Which poems mention X?" →  substring search in content
  - search_by_meaning:  "Poems about loneliness" →  vector similarity (embedding)
  - search_facts:       "Where were you born?"   →  biographical knowledge base
"""

import json
import re
import sys
from pathlib import Path
from langchain_core.tools import tool

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.utils.db import get_connection, get_cursor


def _italicize(text: str) -> str:
    """Wrap each non-empty line in italic markdown so poem text renders in italic."""
    return '\n'.join(
        f'_{line}_' if line.strip() else ''
        for line in text.split('\n')
    )


def create_tools(embeddings):
    """
    Create the three search tools, bound to the given embeddings instance.

    We use a factory function (closure) so the tools can share the embeddings
    object without relying on a global singleton.
    """

    @tool
    def get_poem(title: str) -> str:
        """
        Retrieve the full text of a poem by title.
        Use this when the user asks to recite, read, or show a specific poem.
        Supports partial and fuzzy matching: 'Bori' also finds 'Temni bori'.
        Returns up to 3 closest title matches with full text.
        """
        conn = get_connection()
        cur = get_cursor(conn, dict_cursor=True)
        cur.execute("""
            SELECT title, content,
                CASE
                    WHEN LOWER(title) = LOWER(%s)      THEN 1.0
                    WHEN LOWER(title) LIKE LOWER(%s)   THEN 0.9
                    ELSE similarity(LOWER(title), LOWER(%s))
                END AS score
            FROM works
            WHERE LOWER(title) = LOWER(%s)
               OR LOWER(title) LIKE LOWER(%s)
               OR similarity(LOWER(title), LOWER(%s)) > 0.3
            ORDER BY score DESC
            LIMIT 3
        """, (title, f'%{title}%', title, title, f'%{title}%', title))
        rows = cur.fetchall()
        cur.close()
        conn.close()

        if not rows:
            return f'No poem found with title matching "{title}".'

        parts = []
        for row in rows:
            parts.append(f'**{row["title"]}**\n\n{_italicize(row["content"])}')
        return '\n\n---\n\n'.join(parts)

    @tool
    def search_by_keyword(word: str) -> str:
        """
        Find poems that contain a specific word, name, or place in their text.
        Use this for questions like "V katerih pesmih omenjam X?" or "poems that mention X".
        Use the base/root form of the word for best results (e.g. 'Sežana' not 'Sežano').
        Returns titles and the surrounding context where the word appears.
        """
        conn = get_connection()
        cur = get_cursor(conn, dict_cursor=True)
        cur.execute("""
            SELECT title, content
            FROM works
            WHERE content ILIKE %s OR title ILIKE %s
            ORDER BY title
            LIMIT 10
        """, (f'%{word}%', f'%{word}%'))
        rows = cur.fetchall()
        cur.close()
        conn.close()

        if not rows:
            return f'No poems contain the word or phrase "{word}".'

        lines = [f'Found {len(rows)} poem(s) mentioning "{word}":']
        for row in rows:
            # Extract the snippet around the match
            content_lower = row['content'].lower()
            idx = content_lower.find(word.lower())
            if idx >= 0:
                start = max(0, idx - 80)
                end = min(len(row['content']), idx + len(word) + 80)
                snippet = '..._' + row['content'][start:end].strip() + '_...'
            else:
                snippet = '_' + row['content'][:160] + '..._'
            lines.append(f'\n**{row["title"]}**\n{snippet}')

        return '\n'.join(lines)

    @tool
    def search_by_meaning(query: str) -> str:
        """
        Find poems by theme or concept using semantic similarity.
        Use this for thematic questions like "poems about loneliness", "death and nature",
        or any question where the exact word may not appear in the poems.
        Returns the 5 most semantically similar poems with a short excerpt.
        """
        query_embedding = embeddings.embed_query(query)
        embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'

        conn = get_connection()
        cur = get_cursor(conn, dict_cursor=True)
        cur.execute("""
            SELECT title, content,
                   1 - (embedding <=> %s::vector) AS similarity
            FROM works
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> %s::vector
            LIMIT 5
        """, (embedding_str, embedding_str))
        rows = cur.fetchall()
        cur.close()
        conn.close()

        if not rows:
            return 'No poems found.'

        lines = [f'Most semantically relevant poems for "{query}":']
        for row in rows:
            lines.append(
                f'\n**{row["title"]}** (similarity: {row["similarity"]:.2f})\n'
                f'_{row["content"][:200]}..._'
            )
        return '\n'.join(lines)

    @tool
    def hybrid_search(query: str) -> str:
        """
        Search poems using a combination of semantic meaning AND keyword matching.
        Use this as the default search when the query contains both specific words
        and a thematic/conceptual element. Better than either search_by_meaning or
        search_by_keyword alone for most natural-language queries.
        Returns the 5 best matching poems ranked by combined relevance score.
        """
        query_embedding = embeddings.embed_query(query)
        embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'

        conn = get_connection()
        cur = get_cursor(conn, dict_cursor=True)
        cur.execute("""
            SELECT title, content, combined_score
            FROM hybrid_search(%s::vector, %s, 60, 5)
        """, (embedding_str, query))
        rows = cur.fetchall()
        cur.close()
        conn.close()

        if not rows:
            return f'No poems found for "{query}".'

        lines = [f'Most relevant poems for "{query}":']
        for row in rows:
            lines.append(
                f'\n**{row["title"]}** (score: {row["combined_score"]:.4f})\n'
                f'_{row["content"][:200]}..._'
            )
        return '\n'.join(lines)

    _FACTS_PATH = Path(__file__).parent.parent / "scraping" / "kosovel_facts.json"

    @tool
    def search_facts(query: str) -> str:
        """
        Search for biographical and historical facts about Srečko Kosovel.
        Use this for questions about his life: birthplace, family, education,
        death, influences, literary movements, and legacy.
        Examples: "Kje si se rodil?", "Kdo je bil tvoj oče?", "Kako si umrl?",
        "Where were you born?", "Tell me about your family."
        Returns matching facts with answers in Slovenian and English.
        """
        with open(_FACTS_PATH, encoding="utf-8") as f:
            data = json.load(f)

        # Tokenize query: lowercase words, strip punctuation
        tokens = set(re.findall(r"[a-zA-ZšžčŠŽČđĐćĆ]+", query.lower()))

        scored = []
        for fact in data["facts"]:
            searchable = " ".join([
                fact.get("question_sl", ""),
                fact.get("question_en", ""),
                fact.get("answer_sl", ""),
                fact.get("answer_en", ""),
                " ".join(fact.get("keywords", [])),
            ]).lower()
            score = sum(1 for t in tokens if t in searchable)
            if score > 0:
                scored.append((score, fact))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:5]

        if not top:
            return "No biographical facts found for this query."

        lines = []
        for _, fact in top:
            lines.append(
                f"**{fact['topic']}** [{fact['category']}]\n"
                f"{fact['answer_sl']}\n"
                f"_{fact['answer_en']}_"
            )
        return "\n\n---\n\n".join(lines)

    return [get_poem, search_by_keyword, search_by_meaning, hybrid_search, search_facts]
