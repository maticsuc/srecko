# Srečko Kosovel AI Chat Database 🇸🇮

An AI-friendly PostgreSQL database of Srečko Kosovel's literary works with hybrid search capabilities for conversational AI interfaces.

## 📖 About

This project creates a searchable database of ~460 literary works by Slovenian poet Srečko Kosovel (1904-1926), optimized for LLM-powered conversations. Users can ask questions about his works, request recitations, and explore themes through natural language.

**Use Case**: Build a chat interface where you can talk to Srečko Kosovel, ask him about his poems, and have him recite his works as if he were alive.

## 🎯 Features

- **Hybrid Search**: Semantic (vector) + keyword (full-text) search
- **AI-Optimized**: Designed for LangChain/LlamaIndex integration
- **768D Embeddings**: Multilingual embeddings via Ollama
- **Slovenian Language Support**: Native PostgreSQL text search configuration
- **Tag System**: Auto-generated thematic tags from categories
- **Supabase Ready**: Easy migration to cloud hosting
- **No Chunking**: Poems kept whole for better context and recitation
- **Interactive CLI**: Chat with Srečko Kosovel through a conversational interface

## 💬 Quick Start - Chat Interface

After completing setup (see below), you can immediately start chatting:

```bash
# Activate virtual environment
source venv/bin/activate

# Start the chat
python3 chat_srecko.py
```

**Example conversation:**
```
You: Tell me about your poems on Kras

Srečko Kosovel:
Kras, my homeland, my inspiration. My poems about Kras explore the harsh 
beauty of this limestone plateau - the stone, the wind (burja), the 
resilient people...

📚 Sources:
  1. Kraške ceste (relevance: 0.82)
  2. Kras (relevance: 0.79)
  3. Kraška vas (relevance: 0.71)

You: Recite Kras

Srečko Kosovel:
Of course. This poem captures the essence of the Karst landscape:

[Full poem recitation...]
```

**Chat commands:**
- Type your question naturally
- `exit`, `quit`, or `q` to end
- `help` for instructions
- `sources` to toggle source display

## 🗄️ Database Schema

### Tables

#### `authors`
Stores author biographical information
- `id` (PRIMARY KEY)
- `name` (UNIQUE)
- `birth_year`, `death_year`
- `biography`

#### `categories`
Work categories with slugs
- `id` (PRIMARY KEY)
- `name`, `slug` (UNIQUE)
- `index_page`, `description`

#### `works`
Main content table with AI features
- `id` (PRIMARY KEY)
- `title`, `content`, `url`
- `author_id`, `category_id` (FOREIGN KEYS)
- `word_count` (auto-calculated)
- `search_vector` (full-text search, auto-generated)
- `embedding` (768D vector for semantic search)
- `language` (default: 'sl')

#### `tags`
Thematic tags
- `id` (PRIMARY KEY)
- `name`, `slug` (UNIQUE)
- `category` (e.g., "theme", "motif", "location")
- `description`

#### `work_tags`
Many-to-many relationship between works and tags
- `work_id`, `tag_id` (COMPOSITE PRIMARY KEY)

### Work Categories

Based on the source data:

1. **Lirika** (260 works) - Lyric poetry
2. **Avantgardistična poezija** (140 works) - Avant-garde poetry
3. **Pesmi v prozi** (51 works) - Prose poems
4. **Članki** (6 works) - Articles
5. **Eseji o umetnosti** (2 works) - Essays on art
6. **Literarne kritike** (1 work) - Literary criticism
7. **Črtice** (0 works) - Sketches
8. **Prečevanja** (variable) - Transcriptions/correspondence

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **PostgreSQL 16+** (tested with 16.13) with pgvector extension (0.8.2+)
- **Ollama** with embedding model installed

### Installation

#### 1. Install PostgreSQL + pgvector

See detailed guide: [docs/postgresql-setup.md](docs/postgresql-setup.md)

**Quick install** (macOS with Homebrew):
```bash
brew install postgresql@15
brew services start postgresql@15
brew install pgvector
```

#### 2. Install Ollama and embedding model

```bash
# Install Ollama (see https://ollama.ai)
# macOS/Linux:
curl https://ollama.ai/install.sh | sh

# Pull embedding model
ollama pull nomic-embed-text
```

#### 3. Clone and setup Python environment

```bash
cd /home/matic/dev/srecko
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
```

#### 4. Configure environment

```bash
cp .env.example .env
# Edit .env with your database credentials
```

#### 5. Create database and schema

```bash
python scripts/01_create_schema.py
```

#### 6. Import data

```bash
python scripts/02_import_data.py
```

This will:
- Import 1 author (Srečko Kosovel)
- Import 8 categories
- Import ~460 works
- Auto-generate slugs
- Calculate word counts
- Create basic tags

#### 7. Generate embeddings

```bash
python scripts/03_generate_embeddings.py
```

This will:
- Connect to Ollama
- Generate 768D embeddings for all works
- Store embeddings in the database
- Build vector indexes

**Note**: This takes ~5-10 minutes depending on your machine.

## 📂 Project Structure

```
srecko/
├── AGENTS.md                       # Agent workflows and architecture
├── README.md                       # This file
├── kosovel_data_cleaned.json       # Source data (~460 works)
│
├── .env.example                    # Environment template
├── requirements.txt                # Python dependencies
│
├── chat_srecko.py                  # 🎯 Main CLI chat interface
├── test_cli.py                     # CLI testing script
├── verify_rag_setup.py             # RAG setup verification
│
├── langchain_rag/                  # 🤖 LangChain RAG Implementation
│   ├── __init__.py
│   ├── vector_store.py            # Custom embeddings wrapper
│   ├── retriever.py               # Hybrid search retriever
│   ├── prompts.py                 # Prompt templates (Q&A, Recitation, Analysis)
│   ├── llm.py                     # Ollama LLM wrapper
│   └── chains.py                  # Complete RAG chain
│
├── migrations/
│   └── 001_initial_schema.sql     # Database schema DDL
│
├── scripts/
│   ├── 01_create_schema.py        # Create database and schema
│   ├── 02_import_data.py          # Import JSON data
│   ├── 03_generate_embeddings.py  # Generate embeddings via Ollama
│   ├── test_search.py             # Search testing
│   │
│   └── utils/
│       ├── __init__.py
│       ├── db.py                  # Database connection utilities
│       ├── embeddings.py          # Embedding generation helpers
│       └── slugify.py             # Slug generation utilities
│
└── docs/
    ├── postgresql-setup.md         # PostgreSQL installation guide
    ├── schema-design.md            # Schema documentation
    ├── query-examples.md           # SQL and Python query examples
    ├── LANGCHAIN_RAG_PLAN.md       # Step-by-step RAG learning plan
    ├── TEXT_SEARCH_CONFIG.md       # Text search configuration notes
    ├── IMPORT_SCRIPT_FIXES.md      # Import script fixes documentation
    └── EMBEDDING_SCRIPT_FIXES.md   # Embedding script fixes documentation
```

## 🔍 Query Examples

### Python (with psycopg2)

```python
from scripts.utils.db import get_connection
import ollama

# 1. Semantic Search
def semantic_search(query_text, limit=5):
    conn = get_connection()
    cur = conn.cursor()
    
    # Generate embedding for query
    response = ollama.embeddings(model='nomic-embed-text', prompt=query_text)
    query_embedding = response['embedding']
    
    # Search by vector similarity
    cur.execute("""
        SELECT id, title, content, 
               1 - (embedding <=> %s::vector) AS similarity
        FROM works
        ORDER BY embedding <=> %s::vector
        LIMIT %s
    """, (query_embedding, query_embedding, limit))
    
    return cur.fetchall()

# Example
results = semantic_search("poems about Karst landscape")
```

```python
# 2. Keyword Search
def keyword_search(keywords, limit=10):
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT id, title, 
               ts_rank(search_vector, query) AS rank
        FROM works,
             plainto_tsquery('simple', %s) query
        WHERE search_vector @@ query
        ORDER BY rank DESC
        LIMIT %s
    """, (keywords, limit))
    
    return cur.fetchall()

# Example
results = keyword_search("burja Kras")
```

```python
# 3. Hybrid Search (60% semantic + 40% keyword)
def hybrid_search(query_text, limit=5):
    conn = get_connection()
    cur = conn.cursor()
    
    # Generate embedding
    response = ollama.embeddings(model='nomic-embed-text', prompt=query_text)
    query_embedding = response['embedding']
    
    cur.execute("""
        WITH semantic AS (
            SELECT id, 1 - (embedding <=> %s::vector) AS score
            FROM works
            ORDER BY embedding <=> %s::vector
            LIMIT 20
        ),
        keyword AS (
            SELECT id, ts_rank(search_vector, query) AS score
            FROM works, plainto_tsquery('simple', %s) query
            WHERE search_vector @@ query
            LIMIT 20
        )
        SELECT w.id, w.title, w.content,
               COALESCE(s.score, 0) * 0.6 + COALESCE(k.score, 0) * 0.4 AS combined_score
        FROM works w
        LEFT JOIN semantic s ON w.id = s.id
        LEFT JOIN keyword k ON w.id = k.id
        WHERE s.id IS NOT NULL OR k.id IS NOT NULL
        ORDER BY combined_score DESC
        LIMIT %s
    """, (query_embedding, query_embedding, query_text, limit))
    
    return cur.fetchall()

# Example
results = hybrid_search("melancholic autumn poems")
```

```python
# 4. Get work by title (for recitation)
def get_work_by_title(title):
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT w.*, c.name as category, a.name as author
        FROM works w
        JOIN categories c ON w.category_id = c.id
        JOIN authors a ON w.author_id = a.id
        WHERE w.title ILIKE %s
    """, (f"%{title}%",))
    
    return cur.fetchone()

# Example
poem = get_work_by_title("Kraška vas")
print(poem['content'])  # Recite the full poem
```

### SQL (direct queries)

```sql
-- Find similar works to a specific work
SELECT 
    w2.id, 
    w2.title,
    1 - (w1.embedding <=> w2.embedding) AS similarity
FROM works w1
CROSS JOIN works w2
WHERE w1.title = 'Kraška vas' AND w2.id != w1.id
ORDER BY w1.embedding <=> w2.embedding
LIMIT 5;

-- Get all works in a category with tags
SELECT 
    w.title,
    c.name AS category,
    array_agg(DISTINCT t.name) AS tags
FROM works w
JOIN categories c ON w.category_id = c.id
LEFT JOIN work_tags wt ON w.id = wt.work_id
LEFT JOIN tags t ON wt.tag_id = t.id
WHERE c.slug = 'lirika'
GROUP BY w.id, w.title, c.name
LIMIT 10;

-- Search for works mentioning specific words
SELECT title, ts_headline('simple', content, query) AS excerpt
FROM works,
     plainto_tsquery('simple', 'burja bore') query
WHERE search_vector @@ query
ORDER BY ts_rank(search_vector, query) DESC
LIMIT 5;
```

## 🤖 LangChain Integration

```python
from langchain_community.vectorstores import PGVector
from langchain_community.embeddings import OllamaEmbeddings
from langchain.chains import RetrievalQA
from langchain_community.llms import Ollama

# Setup embeddings
embeddings = OllamaEmbeddings(
    model="nomic-embed-text",
    base_url="http://localhost:11434"
)

# Connect to vector store
vectorstore = PGVector(
    connection_string="postgresql://user:password@localhost:5432/srecko_kosovel",
    embedding_function=embeddings,
    collection_name="works",
    distance_strategy="cosine"
)

# Create retrieval chain
llm = Ollama(model="llama3", base_url="http://localhost:11434")
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vectorstore.as_retriever(search_kwargs={"k": 5}),
    return_source_documents=True
)

# Ask questions
response = qa_chain.invoke("Tell me about Kosovel's poems about the Karst region")
print(response['result'])
```

## 🏗️ Development Roadmap

- [x] Design AI-friendly schema
- [x] Create AGENTS.md workflow documentation
- [x] Create README.md
- [ ] PostgreSQL setup guide
- [ ] SQL schema migration file
- [ ] Python import scripts
- [ ] Embedding generation script
- [ ] LangChain integration examples
- [ ] Chat UI interface
- [ ] Supabase migration guide
- [ ] Performance optimization
- [ ] Add work relationships (future)
- [ ] Add chunking support for longer works (future)

## 📊 Database Statistics

| Metric | Value |
|--------|-------|
| Total Works | ~460 |
| Authors | 1 (Srečko Kosovel) |
| Categories | 8 |
| Largest Category | Lirika (260 works) |
| Embedding Dimensions | 768 |
| Primary Language | Slovenian (sl) |
| Avg Words per Work | ~100-200 |

## 🛠️ Technology Stack

- **Database**: PostgreSQL 16+ (tested with 16.13) with pgvector 0.8.2+
- **Embeddings**: Ollama (nomic-embed-text, 768 dims)
- **Language**: Python 3.10+
- **Framework**: LangChain/LlamaIndex (future)
- **Text Search**: PostgreSQL full-text search (simple config - works for all languages)
- **Hosting**: Local → Supabase (future migration)

## 📝 Environment Variables

Create a `.env` file:

```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=srecko_kosovel
DB_USER=postgres
DB_PASSWORD=your_password_here

# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_EMBEDDING_MODEL=nomic-embed-text

# Optional: LLM Configuration
OLLAMA_LLM_MODEL=llama3
```

## 🧪 Testing

After setup, verify everything works:

```bash
# Check database connection
psql -d srecko_kosovel -c "SELECT COUNT(*) FROM works;"

# Should return: ~460

# Check embeddings
psql -d srecko_kosovel -c "SELECT COUNT(*) FROM works WHERE embedding IS NOT NULL;"

# Should return: ~460

# Test Ollama
curl http://localhost:11434/api/embeddings -d '{
  "model": "nomic-embed-text",
  "prompt": "test"
}'

# Should return JSON with embedding array
```

## 🚀 Next Steps

After completing the setup:

1. **Explore the data**: Run example queries to understand the works
2. **Build LangChain integration**: Connect the database to an LLM
3. **Create chat interface**: Build a UI to talk to Srečko Kosovel
4. **Deploy to Supabase**: Migrate to cloud hosting for production
5. **Optimize performance**: Add caching, query optimization
6. **Add features**: Work relationships, user favorites, reading history

## 🤝 Contributing

This is a personal project, but suggestions and improvements are welcome!

## 📄 License

- **Data**: Sourced from [Wikisource - Srečko Kosovel](https://sl.wikisource.org/wiki/Sre%C4%8Dko_Kosovel) (Public Domain)
- **Code**: MIT License

## 🙏 Acknowledgments

- Srečko Kosovel (1904-1926) - Slovenian poet
- Wikisource contributors for digitizing the works
- Ollama for free local embeddings
- PostgreSQL and pgvector teams

## 📚 Additional Resources

- [Srečko Kosovel on Wikipedia](https://en.wikipedia.org/wiki/Sre%C4%8Dko_Kosovel)
- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [Ollama Documentation](https://ollama.ai/docs)
- [LangChain Documentation](https://python.langchain.com/)

---

**Made with ❤️ for Slovenian literature and AI**
