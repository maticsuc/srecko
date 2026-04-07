-- =========================================
-- Srečko Kosovel AI Chat Database Schema
-- PostgreSQL 16+ (tested with 16.13)
-- pgvector 0.8.2+
-- =========================================
-- 
-- Note: Uses 'simple' text search config (no language-specific stemming)
-- because 'slovenian' is not available by default in PostgreSQL.
-- The 'simple' config works for all languages but doesn't perform 
-- language-specific word stemming or stopword removal.
--
-- =========================================

-- Create extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- =========================================
-- Table: authors
-- =========================================
CREATE TABLE authors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    birth_year INTEGER,
    death_year INTEGER,
    biography TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE authors IS 'Stores author biographical information';
COMMENT ON COLUMN authors.name IS 'Full name of the author';
COMMENT ON COLUMN authors.biography IS 'Biographical information about the author';

-- =========================================
-- Table: categories
-- =========================================
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    slug VARCHAR(100) NOT NULL UNIQUE,
    index_page VARCHAR(255),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE categories IS 'Work categories (lirika, avantgardisticna_poezija, etc.)';
COMMENT ON COLUMN categories.slug IS 'URL-friendly identifier (e.g., "lirika", "pesmi-v-prozi")';
COMMENT ON COLUMN categories.index_page IS 'Source index page from Wikisource';

-- =========================================
-- Table: works
-- =========================================
CREATE TABLE works (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    url VARCHAR(500) UNIQUE,
    author_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    
    -- Metadata
    word_count INTEGER,
    language VARCHAR(10) DEFAULT 'sl',
    
    -- Full-text search vector (auto-generated)
    -- Using 'simple' config as 'slovenian' is not available by default
    -- 'simple' works for all languages but without stemming/stopwords
    search_vector tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('simple', coalesce(title, '')), 'A') ||
        setweight(to_tsvector('simple', coalesce(content, '')), 'B')
    ) STORED,
    
    -- Vector embedding for semantic search (1024 dimensions)
    embedding vector(1024),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (author_id) REFERENCES authors(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
);

COMMENT ON TABLE works IS 'Main content table with poems, prose, and other literary works';
COMMENT ON COLUMN works.content IS 'Full text content of the work';
COMMENT ON COLUMN works.word_count IS 'Number of words in the content';
COMMENT ON COLUMN works.search_vector IS 'Full-text search vector (auto-generated)';
COMMENT ON COLUMN works.embedding IS '1024-dimensional vector for semantic search (mxbai-embed-large)';
COMMENT ON COLUMN works.language IS 'ISO 639-1 language code (sl = Slovenian)';

-- Indexes for works table
CREATE INDEX idx_works_author ON works(author_id);
CREATE INDEX idx_works_category ON works(category_id);
CREATE INDEX idx_works_title ON works USING gin(title gin_trgm_ops);
CREATE INDEX idx_works_search ON works USING GIN(search_vector);
CREATE INDEX idx_works_embedding ON works USING ivfflat(embedding vector_cosine_ops) WITH (lists = 100);

COMMENT ON INDEX idx_works_title IS 'Trigram index for fuzzy title matching';
COMMENT ON INDEX idx_works_search IS 'GIN index for full-text search';
COMMENT ON INDEX idx_works_embedding IS 'IVFFlat index for fast vector similarity search';

-- =========================================
-- Table: tags
-- =========================================
CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    slug VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(50),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE tags IS 'Thematic tags for works';
COMMENT ON COLUMN tags.category IS 'Tag category: theme, motif, location, emotion, etc.';
COMMENT ON COLUMN tags.slug IS 'URL-friendly identifier';

CREATE INDEX idx_tags_name ON tags(name);
CREATE INDEX idx_tags_category ON tags(category);

-- =========================================
-- Table: work_tags
-- =========================================
CREATE TABLE work_tags (
    work_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (work_id, tag_id),
    FOREIGN KEY (work_id) REFERENCES works(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

COMMENT ON TABLE work_tags IS 'Many-to-many relationship between works and tags';

CREATE INDEX idx_work_tags_work ON work_tags(work_id);
CREATE INDEX idx_work_tags_tag ON work_tags(tag_id);

-- =========================================
-- Helper Functions
-- =========================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER update_authors_updated_at
    BEFORE UPDATE ON authors
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_categories_updated_at
    BEFORE UPDATE ON categories
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_works_updated_at
    BEFORE UPDATE ON works
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =========================================
-- Utility Views
-- =========================================

-- View: works with category and author info
CREATE VIEW works_full AS
SELECT 
    w.id,
    w.title,
    w.content,
    w.url,
    w.word_count,
    w.language,
    a.name AS author_name,
    c.name AS category_name,
    c.slug AS category_slug,
    w.created_at,
    w.updated_at
FROM works w
JOIN authors a ON w.author_id = a.id
JOIN categories c ON w.category_id = c.id;

COMMENT ON VIEW works_full IS 'Works with joined author and category information';

-- View: category statistics
CREATE VIEW category_stats AS
SELECT 
    c.id,
    c.name,
    c.slug,
    COUNT(w.id) AS work_count,
    AVG(w.word_count) AS avg_word_count,
    MIN(w.created_at) AS first_work_date,
    MAX(w.created_at) AS last_work_date
FROM categories c
LEFT JOIN works w ON c.id = w.category_id
GROUP BY c.id, c.name, c.slug;

COMMENT ON VIEW category_stats IS 'Statistics for each category';

-- =========================================
-- Helper Functions for Search
-- =========================================

-- Function: Hybrid search using Reciprocal Rank Fusion (RRF)
-- RRF is scale-invariant: rank positions are used instead of raw scores,
-- so the cosine similarity (0-1) vs ts_rank (0.00001-0.1) mismatch doesn't matter.
CREATE OR REPLACE FUNCTION hybrid_search(
    query_embedding vector(1024),
    query_text TEXT,
    rrf_k INTEGER DEFAULT 60,
    result_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    work_id INTEGER,
    title VARCHAR(500),
    content TEXT,
    combined_score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    WITH semantic_ranked AS (
        SELECT
            id,
            ROW_NUMBER() OVER (ORDER BY embedding <=> query_embedding) AS rank
        FROM works
        WHERE embedding IS NOT NULL
        LIMIT 20
    ),
    keyword_ranked AS (
        SELECT
            id,
            ROW_NUMBER() OVER (ORDER BY ts_rank(search_vector, q) DESC) AS rank
        FROM works,
             plainto_tsquery('simple', query_text) q
        WHERE search_vector @@ q
        LIMIT 20
    )
    SELECT
        w.id,
        w.title,
        w.content,
        (COALESCE(1.0 / (rrf_k + s.rank), 0) +
         COALESCE(1.0 / (rrf_k + k.rank), 0))::FLOAT AS rrf_score
    FROM works w
    LEFT JOIN semantic_ranked s ON w.id = s.id
    LEFT JOIN keyword_ranked k ON w.id = k.id
    WHERE s.id IS NOT NULL OR k.id IS NOT NULL
    ORDER BY rrf_score DESC
    LIMIT result_limit;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION hybrid_search IS 'Hybrid search with Reciprocal Rank Fusion (RRF): scale-invariant combination of vector and full-text search';

-- =========================================
-- Sample Data (Optional - for testing)
-- =========================================

-- Insert sample author (will be replaced by actual data)
-- INSERT INTO authors (name, birth_year, death_year, biography) VALUES
-- ('Srečko Kosovel', 1904, 1926, 'Slovenian poet from the Karst region...');

-- =========================================
-- Grants (Adjust as needed)
-- =========================================

-- Grant privileges to application user
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO srecko_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO srecko_user;

-- =========================================
-- Schema Information
-- =========================================

-- Print schema version
DO $$
BEGIN
    RAISE NOTICE 'Schema created successfully!';
    RAISE NOTICE 'Database: srecko_kosovel';
    RAISE NOTICE 'Schema version: 001';
    RAISE NOTICE 'Tables: authors, categories, works, tags, work_tags';
    RAISE NOTICE 'Extensions: vector, pg_trgm';
    RAISE NOTICE '';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '1. Run: python scripts/02_import_data.py';
    RAISE NOTICE '2. Run: python scripts/03_generate_embeddings.py';
END $$;
