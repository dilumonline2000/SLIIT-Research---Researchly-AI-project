# 🧠 CLAUDE CODE OPUS 4.6 — IMPLEMENTATION PROMPT
## Research Paper Upload + RAG Chatbot + Multilingual Chat + Continuous Training
### For: R26-IT-116 AI-Powered Research Paper Assistant Platform

---

## 📌 CONTEXT — READ THIS FIRST

You are working on an existing monorepo project (R26-IT-116) that has 4 modules. This prompt adds **THREE major cross-cutting features** that integrate across ALL 4 modules:

1. **Research Paper Upload & Processing Pipeline** — Upload PDFs from dashboard, extract text/metadata, store as structured JSON, feed into model training
2. **RAG-Based Multilingual Chatbot** — Chat with uploaded papers like ChatGPT, support Sinhala/English/Tamil/Singlish
3. **Continuous Learning Pipeline** — User questions + interactions stored and used to incrementally improve all models

**Tech Stack (already established):**
- Frontend: Next.js 14 (App Router) + TypeScript + Tailwind + shadcn/ui
- Backend: Node.js + Express.js (API Gateway) + Python FastAPI (ML services)
- Database: Supabase (PostgreSQL + pgvector + Auth + Storage + Realtime)
- ML: Hugging Face Transformers, SBERT, PyTorch, LangChain
- The 4 modules: Module 1 (Integrity/Citations), Module 2 (Collaboration), Module 3 (Data Management), Module 4 (Analytics)

---

## 🏗️ FEATURE 1: RESEARCH PAPER UPLOAD & PROCESSING PIPELINE

### 1.1 New Folder Structure Additions

```
research-platform/
├── apps/web/src/
│   ├── app/(dashboard)/
│   │   ├── papers/                         # NEW — Paper Management Hub
│   │   │   ├── page.tsx                    # Paper library (grid/list view)
│   │   │   ├── upload/page.tsx             # Upload interface
│   │   │   ├── [paperId]/page.tsx          # Single paper detail view
│   │   │   └── [paperId]/chat/page.tsx     # Chat with this paper
│   │   └── chat/                           # NEW — Global Chat Interface
│   │       ├── page.tsx                    # Chat home (select papers to chat about)
│   │       ├── [sessionId]/page.tsx        # Active chat session
│   │       └── history/page.tsx            # Past chat sessions
│   ├── components/
│   │   ├── papers/                         # NEW — Paper components
│   │   │   ├── PaperUploader.tsx           # Drag-drop multi-file upload
│   │   │   ├── PaperCard.tsx               # Paper preview card
│   │   │   ├── PaperGrid.tsx               # Grid layout for paper library
│   │   │   ├── PaperDetail.tsx             # Full paper metadata view
│   │   │   ├── ProcessingStatus.tsx        # Real-time processing indicator
│   │   │   └── PaperSelector.tsx           # Select papers for chat context
│   │   └── chat/                           # NEW — Chat components
│   │       ├── ChatWindow.tsx              # Main chat interface
│   │       ├── ChatMessage.tsx             # Single message bubble
│   │       ├── ChatInput.tsx               # Input with language detection
│   │       ├── LanguageSelector.tsx         # EN/SI/TA/Singlish toggle
│   │       ├── CitationPopover.tsx         # Inline paper citation reference
│   │       ├── ChatSidebar.tsx             # Chat history + paper context
│   │       └── TypingIndicator.tsx         # AI typing animation
│   ├── hooks/
│   │   ├── usePaperUpload.ts              # NEW — Upload hook with progress
│   │   ├── useChat.ts                     # NEW — Chat hook with streaming
│   │   └── useLanguageDetect.ts           # NEW — Auto language detection
│   └── stores/
│       ├── paperStore.ts                  # NEW — Paper state management
│       └── chatStore.ts                   # NEW — Chat state management
│
├── services/
│   └── paper-chat/                        # NEW — Unified Paper + Chat Service
│       ├── app/
│       │   ├── __init__.py
│       │   ├── main.py                    # FastAPI entrypoint
│       │   ├── routers/
│       │   │   ├── __init__.py
│       │   │   ├── upload.py              # Paper upload & processing endpoints
│       │   │   ├── chat.py                # Chat endpoints (streaming)
│       │   │   ├── training.py            # Continuous training endpoints
│       │   │   └── language.py            # Language detection/translation
│       │   ├── services/
│       │   │   ├── __init__.py
│       │   │   ├── pdf_processor.py       # PDF → structured JSON pipeline
│       │   │   ├── text_extractor.py      # PyMuPDF + pdfplumber extraction
│       │   │   ├── metadata_extractor.py  # Title, authors, abstract, refs
│       │   │   ├── chunk_manager.py       # Intelligent text chunking
│       │   │   ├── embedding_service.py   # SBERT embedding generation
│       │   │   ├── rag_engine.py          # RAG retrieval + generation
│       │   │   ├── chat_service.py        # Chat orchestration
│       │   │   ├── language_service.py    # Multilingual NLP
│       │   │   ├── singlish_processor.py  # Singlish → Sinhala/English
│       │   │   ├── training_pipeline.py   # Continuous training manager
│       │   │   └── data_formatter.py      # Format data for training
│       │   ├── models/
│       │   │   ├── __init__.py
│       │   │   ├── rag_model.py           # RAG chain configuration
│       │   │   ├── translation_model.py   # Multilingual translation
│       │   │   └── language_detector.py   # Language identification model
│       │   └── schemas/
│       │       ├── __init__.py
│       │       ├── paper.py
│       │       ├── chat.py
│       │       └── training.py
│       ├── requirements.txt
│       ├── Dockerfile
│       └── .env.example
│
├── ml/
│   ├── data/
│   │   ├── uploaded/                      # NEW — User-uploaded paper data
│   │   │   ├── raw_pdfs/                  # Original PDFs (gitignored)
│   │   │   ├── extracted/                 # Extracted JSON data
│   │   │   └── chunks/                    # Chunked text for embeddings
│   │   ├── chat_logs/                     # NEW — Chat interaction data
│   │   │   ├── questions/                 # User questions (training data)
│   │   │   ├── feedback/                  # User feedback on answers
│   │   │   └── sessions/                  # Full session logs
│   │   └── training_queue/                # NEW — Queued data for retraining
│   │       ├── pending/
│   │       ├── processed/
│   │       └── training_manifest.json
│   ├── training/
│   │   ├── continuous_trainer.py          # NEW — Incremental training orchestrator
│   │   ├── data_augmenter.py             # NEW — Augment training data from chats
│   │   └── model_versioner.py            # NEW — Model version management
│   └── configs/
│       ├── rag_config.yaml               # NEW
│       ├── chat_config.yaml              # NEW
│       └── continuous_training.yaml      # NEW
│
└── supabase/migrations/
    ├── 009_paper_uploads.sql             # NEW — Paper upload tables
    ├── 010_chat_tables.sql               # NEW — Chat/conversation tables
    └── 011_training_data.sql             # NEW — Training data tables
```

### 1.2 Database Schema — New Tables

```sql
-- ============================================
-- PAPER UPLOAD & PROCESSING
-- ============================================

-- Uploaded papers (user-uploaded research papers)
CREATE TABLE public.uploaded_papers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    
    -- File info
    original_filename TEXT NOT NULL,
    file_url TEXT NOT NULL,                          -- Supabase Storage URL
    file_size_bytes BIGINT,
    mime_type TEXT DEFAULT 'application/pdf',
    page_count INTEGER,
    
    -- Extracted metadata (structured JSON)
    title TEXT,
    authors TEXT[],
    abstract TEXT,
    keywords TEXT[],
    publication_year INTEGER,
    venue TEXT,
    doi TEXT,
    references_list JSONB,                           -- [{title, authors, year, doi}]
    
    -- Full extracted content as structured JSON
    extracted_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    /*
    extracted_data structure:
    {
        "metadata": {title, authors, abstract, keywords, doi, year, venue},
        "sections": [
            {"heading": "Introduction", "content": "...", "page": 1},
            {"heading": "Methodology", "content": "...", "page": 5}
        ],
        "tables": [{"caption": "...", "data": [[]], "page": 3}],
        "figures": [{"caption": "...", "page": 4}],
        "references": [{"raw": "...", "parsed": {title, authors, year}}],
        "full_text": "entire plain text",
        "statistics": {word_count, char_count, page_count, ref_count}
    }
    */
    
    -- Processing status
    processing_status TEXT CHECK (processing_status IN (
        'uploading', 'extracting', 'chunking', 'embedding', 
        'indexing', 'ready', 'failed'
    )) DEFAULT 'uploading',
    processing_error TEXT,
    processing_started_at TIMESTAMPTZ,
    processing_completed_at TIMESTAMPTZ,
    
    -- Embedding (for whole-paper similarity)
    embedding VECTOR(768),
    
    -- Module associations
    used_by_modules TEXT[] DEFAULT '{}',              -- Which modules use this paper
    is_training_data BOOLEAN DEFAULT TRUE,            -- Include in model training
    
    -- Visibility
    is_public BOOLEAN DEFAULT FALSE,                  -- Visible to other users?
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Paper chunks (for RAG retrieval)
CREATE TABLE public.paper_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id UUID REFERENCES public.uploaded_papers(id) ON DELETE CASCADE,
    
    -- Chunk content
    chunk_index INTEGER NOT NULL,                    -- Order within paper
    chunk_text TEXT NOT NULL,
    chunk_type TEXT CHECK (chunk_type IN (
        'abstract', 'introduction', 'methodology', 'results',
        'discussion', 'conclusion', 'references', 'other'
    )) DEFAULT 'other',
    
    -- Source location
    page_start INTEGER,
    page_end INTEGER,
    section_heading TEXT,
    
    -- Embedding for semantic search
    embedding VECTOR(768) NOT NULL,
    
    -- Metadata for retrieval
    token_count INTEGER,
    metadata JSONB DEFAULT '{}'::jsonb,               -- {has_tables, has_figures, etc.}
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for fast chunk retrieval
CREATE INDEX idx_chunks_paper ON public.paper_chunks(paper_id);
CREATE INDEX idx_chunks_embedding ON public.paper_chunks 
    USING hnsw (embedding vector_cosine_ops);
CREATE INDEX idx_uploaded_papers_user ON public.uploaded_papers(user_id);
CREATE INDEX idx_uploaded_papers_embedding ON public.uploaded_papers 
    USING hnsw (embedding vector_cosine_ops);
CREATE INDEX idx_uploaded_papers_status ON public.uploaded_papers(processing_status);

-- ============================================
-- CHAT & CONVERSATIONS
-- ============================================

-- Chat sessions
CREATE TABLE public.chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    
    -- Session info
    title TEXT,                                       -- Auto-generated from first question
    session_type TEXT CHECK (session_type IN (
        'paper_specific',    -- Chat about specific paper(s)
        'corpus_wide',       -- Chat across all user's papers
        'module_specific'    -- Chat within a specific module context
    )) DEFAULT 'paper_specific',
    
    -- Context papers (which papers are in this chat's context)
    paper_ids UUID[] DEFAULT '{}',
    module_context TEXT,                              -- 'module1', 'module2', etc.
    
    -- Language preference
    preferred_language TEXT CHECK (preferred_language IN (
        'en', 'si', 'ta', 'singlish', 'auto'
    )) DEFAULT 'auto',
    
    -- Stats
    message_count INTEGER DEFAULT 0,
    last_message_at TIMESTAMPTZ,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Chat messages
CREATE TABLE public.chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES public.chat_sessions(id) ON DELETE CASCADE,
    
    -- Message content
    role TEXT CHECK (role IN ('user', 'assistant', 'system')) NOT NULL,
    content TEXT NOT NULL,
    
    -- Language info
    detected_language TEXT,                           -- Detected input language
    original_content TEXT,                            -- Original if translated
    response_language TEXT,                           -- Language of response
    
    -- RAG context (what was retrieved for this answer)
    retrieved_chunks JSONB,                           -- [{chunk_id, paper_id, score, text_preview}]
    retrieval_scores JSONB,                           -- {avg_score, max_score, chunks_used}
    
    -- Source citations in the response
    citations JSONB,                                  -- [{paper_id, paper_title, page, section}]
    
    -- Feedback
    user_rating INTEGER CHECK (user_rating BETWEEN 1 AND 5),
    user_feedback TEXT,
    is_helpful BOOLEAN,
    
    -- Training flags
    used_for_training BOOLEAN DEFAULT FALSE,
    training_batch_id TEXT,
    
    -- Token usage
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for chat
CREATE INDEX idx_sessions_user ON public.chat_sessions(user_id);
CREATE INDEX idx_messages_session ON public.chat_messages(session_id);
CREATE INDEX idx_messages_created ON public.chat_messages(created_at);
CREATE INDEX idx_messages_training ON public.chat_messages(used_for_training) 
    WHERE used_for_training = FALSE;

-- ============================================
-- CONTINUOUS TRAINING DATA
-- ============================================

-- Training data queue (collected from user interactions)
CREATE TABLE public.training_data_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Source info
    source_type TEXT CHECK (source_type IN (
        'uploaded_paper',    -- New paper uploaded
        'chat_qa',           -- Question-answer pair from chat
        'user_feedback',     -- User rated an answer
        'paper_annotation',  -- User highlighted/annotated
        'scraped_paper'      -- From web scraping pipeline
    )) NOT NULL,
    source_id UUID,                                  -- ID of source record
    
    -- Training data (structured JSON)
    training_data JSONB NOT NULL,
    /*
    For uploaded_paper:
    {
        "text": "full extracted text",
        "metadata": {title, authors, abstract, keywords},
        "sections": [...],
        "embedding_text": "abstract + keywords for embedding",
        "labels": {topics: [...], quality_indicators: {...}}
    }
    
    For chat_qa:
    {
        "question": "user question",
        "answer": "assistant answer",
        "language": "en|si|ta|singlish",
        "context_chunks": ["chunk texts used"],
        "paper_ids": ["source paper ids"],
        "user_rating": 4,
        "is_helpful": true
    }
    
    For user_feedback:
    {
        "message_id": "...",
        "rating": 5,
        "feedback_text": "very accurate",
        "original_question": "...",
        "original_answer": "..."
    }
    */
    
    -- Target models (which models should train on this)
    target_models TEXT[] NOT NULL,
    -- Possible values: 
    -- 'sbert', 'scibert_classifier', 'citation_ner', 'sentiment',
    -- 'summarizer', 'proposal_llm', 'rag_retriever', 'trend_forecaster',
    -- 'quality_scorer', 'success_predictor'
    
    -- Processing status
    status TEXT CHECK (status IN (
        'pending', 'preprocessing', 'queued', 'training', 
        'completed', 'failed', 'skipped'
    )) DEFAULT 'pending',
    
    -- Quality filter
    quality_score REAL,                              -- Auto-assessed quality (0-1)
    is_approved BOOLEAN DEFAULT NULL,                -- Manual approval if needed
    
    -- Batch info
    batch_id TEXT,
    processed_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Model versions (track training iterations)
CREATE TABLE public.model_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name TEXT NOT NULL,
    version TEXT NOT NULL,
    
    -- Training info
    training_data_count INTEGER,
    training_started_at TIMESTAMPTZ,
    training_completed_at TIMESTAMPTZ,
    training_duration_seconds INTEGER,
    
    -- Performance metrics
    metrics JSONB,                                   -- {accuracy, f1, loss, etc.}
    
    -- Model artifacts
    model_path TEXT,                                  -- Supabase Storage path
    config JSONB,                                     -- Training config used
    
    -- Status
    is_active BOOLEAN DEFAULT FALSE,                 -- Currently serving?
    is_baseline BOOLEAN DEFAULT FALSE,               -- Is this the baseline model?
    
    -- Comparison
    improvement_over_baseline JSONB,                 -- {metric: % change}
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_training_queue_status ON public.training_data_queue(status);
CREATE INDEX idx_training_queue_models ON public.training_data_queue USING GIN(target_models);
CREATE INDEX idx_model_versions_name ON public.model_versions(model_name);
CREATE INDEX idx_model_versions_active ON public.model_versions(model_name, is_active) 
    WHERE is_active = TRUE;

-- Realtime subscriptions for processing status
ALTER PUBLICATION supabase_realtime ADD TABLE public.uploaded_papers;
ALTER PUBLICATION supabase_realtime ADD TABLE public.chat_messages;

-- RLS Policies
ALTER TABLE public.uploaded_papers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.paper_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users manage own papers" ON public.uploaded_papers
    FOR ALL USING (auth.uid() = user_id OR is_public = TRUE);
CREATE POLICY "Users access own chunks" ON public.paper_chunks
    FOR SELECT USING (
        EXISTS (SELECT 1 FROM public.uploaded_papers 
                WHERE id = paper_id AND (user_id = auth.uid() OR is_public = TRUE))
    );
CREATE POLICY "Users manage own chats" ON public.chat_sessions
    FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users access own messages" ON public.chat_messages
    FOR ALL USING (
        EXISTS (SELECT 1 FROM public.chat_sessions 
                WHERE id = session_id AND user_id = auth.uid())
    );

-- ============================================
-- HELPER FUNCTIONS
-- ============================================

-- Semantic search across paper chunks
CREATE OR REPLACE FUNCTION search_paper_chunks(
    query_embedding VECTOR(768),
    target_paper_ids UUID[] DEFAULT NULL,
    match_threshold FLOAT DEFAULT 0.6,
    match_count INT DEFAULT 8
)
RETURNS TABLE (
    chunk_id UUID, 
    paper_id UUID, 
    chunk_text TEXT, 
    section_heading TEXT,
    similarity FLOAT,
    paper_title TEXT
)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT 
        pc.id AS chunk_id,
        pc.paper_id,
        pc.chunk_text,
        pc.section_heading,
        1 - (pc.embedding <=> query_embedding) AS similarity,
        up.title AS paper_title
    FROM public.paper_chunks pc
    JOIN public.uploaded_papers up ON up.id = pc.paper_id
    WHERE 
        up.processing_status = 'ready'
        AND 1 - (pc.embedding <=> query_embedding) > match_threshold
        AND (target_paper_ids IS NULL OR pc.paper_id = ANY(target_paper_ids))
    ORDER BY pc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Get pending training data for a specific model
CREATE OR REPLACE FUNCTION get_pending_training_data(
    target_model TEXT,
    batch_size INT DEFAULT 100
)
RETURNS TABLE (id UUID, training_data JSONB, source_type TEXT)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT tdq.id, tdq.training_data, tdq.source_type
    FROM public.training_data_queue tdq
    WHERE tdq.status = 'pending'
        AND target_model = ANY(tdq.target_models)
        AND (tdq.is_approved IS NULL OR tdq.is_approved = TRUE)
        AND tdq.quality_score IS NULL OR tdq.quality_score > 0.3
    ORDER BY tdq.created_at
    LIMIT batch_size;
END;
$$;
```

### 1.3 Paper Upload & Processing Pipeline (Python Service)

```
IMPLEMENTATION SPECIFICATION — pdf_processor.py:

UPLOAD FLOW:
1. User drops PDF(s) on PaperUploader component
2. Frontend uploads to Supabase Storage (bucket: 'research-papers')
3. Frontend creates record in uploaded_papers table (status: 'uploading')
4. Frontend calls POST /api/v1/papers/process with paper_id
5. Backend processing pipeline starts (status updates via Supabase Realtime):

PROCESSING PIPELINE (async):
Step 1 — TEXT EXTRACTION (status: 'extracting')
  - Use PyMuPDF (fitz) as primary extractor
  - Fallback to pdfplumber for complex layouts
  - Extract: full text, page-by-page text, tables, images metadata
  - Detect sections using heading patterns (regex + font-size analysis)
  
Step 2 — METADATA EXTRACTION (still 'extracting')
  - Title: First large-font text or first line
  - Authors: Pattern match after title (name patterns, affiliations)
  - Abstract: Text between "Abstract" and "Introduction"/"Keywords"
  - Keywords: Text after "Keywords:" or "Index Terms:"
  - DOI: Regex match for DOI pattern
  - References: Parse reference section (use GROBID pattern matching)
  - Year: Extract from DOI, header, or reference dates
  
Step 3 — STRUCTURED JSON CREATION (still 'extracting')
  Create the extracted_data JSONB with this exact structure:
  {
      "metadata": {
          "title": "...",
          "authors": ["Name 1", "Name 2"],
          "abstract": "...",
          "keywords": ["keyword1", "keyword2"],
          "doi": "10.xxx/xxx",
          "year": 2024,
          "venue": "Conference/Journal Name"
      },
      "sections": [
          {
              "heading": "Introduction",
              "content": "Full section text...",
              "page_start": 1,
              "page_end": 3,
              "subsections": [
                  {"heading": "1.1 Background", "content": "..."}
              ]
          }
      ],
      "tables": [
          {
              "caption": "Table 1: Results comparison",
              "data": [["Col1", "Col2"], ["val1", "val2"]],
              "page": 5
          }
      ],
      "figures": [
          {"caption": "Figure 1: System Architecture", "page": 4}
      ],
      "references": [
          {
              "raw": "[1] Author et al., Title, Journal, 2023",
              "parsed": {
                  "authors": ["Author1"],
                  "title": "Paper Title",
                  "year": 2023,
                  "venue": "Journal",
                  "doi": null
              }
          }
      ],
      "full_text": "Complete extracted text...",
      "statistics": {
          "word_count": 5420,
          "char_count": 32500,
          "page_count": 12,
          "section_count": 7,
          "reference_count": 28,
          "table_count": 3,
          "figure_count": 5
      }
  }

Step 4 — TEXT CHUNKING (status: 'chunking')
  - Use LangChain RecursiveCharacterTextSplitter
  - Chunk size: 512 tokens, overlap: 64 tokens
  - Respect section boundaries (don't split mid-section if possible)
  - Tag each chunk with section type (abstract, methodology, etc.)
  - Store chunks in paper_chunks table

Step 5 — EMBEDDING GENERATION (status: 'embedding')
  - Generate SBERT embedding for each chunk
  - Generate whole-paper embedding from abstract + title + keywords
  - Store embeddings in pgvector columns
  - Model: sentence-transformers/all-MiniLM-L6-v2 (or fine-tuned version)

Step 6 — INDEXING & CROSS-MODULE INTEGRATION (status: 'indexing')
  - Add paper to Module 1 corpus (for gap analysis, plagiarism comparison)
  - Add to Module 2 knowledge base (for supervisor matching context)
  - Add to Module 3 data pipeline (for topic categorization)
  - Add to Module 4 analytics pool (for trend analysis, quality scoring)
  - Queue as training data in training_data_queue

Step 7 — COMPLETE (status: 'ready')
  - Update processing_completed_at timestamp
  - Emit Supabase Realtime event for frontend update

ERROR HANDLING:
  - If any step fails → status: 'failed', processing_error: detailed message
  - Implement retry logic (max 3 retries with exponential backoff)
  - Partial extraction is acceptable — save what was extracted
```

### 1.4 Training Data Format (JSON)

```
CRITICAL: All uploaded papers must be stored in a CONSISTENT JSON format
that can be directly consumed by training pipelines.

TRAINING DATA JSON SCHEMA (saved per paper):

{
    "paper_id": "uuid",
    "version": "1.0",
    "extracted_at": "2026-04-14T10:30:00Z",
    
    "for_sbert_training": {
        "anchor_text": "abstract text here",
        "positive_texts": ["similar section texts"],
        "metadata": {"topic": "AI", "year": 2024}
    },
    
    "for_scibert_classification": {
        "text": "abstract + introduction combined",
        "labels": ["AI", "Machine Learning", "NLP"],
        "confidence": [0.95, 0.88, 0.72]
    },
    
    "for_citation_ner": {
        "references": [
            {
                "raw_text": "[1] Smith et al., Deep Learning for NLP, EMNLP 2023",
                "entities": [
                    {"text": "Smith et al.", "label": "AUTHOR", "start": 4, "end": 16},
                    {"text": "Deep Learning for NLP", "label": "TITLE", "start": 18, "end": 39},
                    {"text": "EMNLP", "label": "VENUE", "start": 41, "end": 46},
                    {"text": "2023", "label": "YEAR", "start": 47, "end": 51}
                ]
            }
        ]
    },
    
    "for_summarization": {
        "full_text": "entire paper text",
        "abstract_as_summary": "author-written abstract (ground truth)",
        "section_texts": {"introduction": "...", "methodology": "..."}
    },
    
    "for_proposal_llm": {
        "topic": "extracted research topic",
        "problem_statement": "extracted from intro",
        "objectives": ["obj1", "obj2"],
        "methodology": "extracted methodology text"
    },
    
    "for_trend_analysis": {
        "topics": ["keyword1", "keyword2"],
        "year": 2024,
        "citation_count": 15,
        "venue_type": "conference"
    },
    
    "for_quality_scoring": {
        "has_abstract": true,
        "reference_count": 28,
        "methodology_present": true,
        "results_present": true,
        "word_count": 5420
    },
    
    "for_rag_retrieval": {
        "chunks": [
            {
                "text": "chunk text",
                "section": "methodology",
                "page": 5,
                "token_count": 480
            }
        ]
    }
}

This JSON is stored in:
  1. Supabase: uploaded_papers.extracted_data column
  2. File system: ml/data/uploaded/extracted/{paper_id}.json
  3. Training queue: training_data_queue table (for each target model)
```

---

## 🤖 FEATURE 2: RAG-BASED MULTILINGUAL CHATBOT

### 2.1 Chat Architecture

```
USER QUESTION FLOW:

User types question (any language)
        ↓
[1] LANGUAGE DETECTION
    - Use langdetect + custom Singlish detector
    - Singlish detection: regex patterns for mixed Sinhala-English
      Examples: "meka mokakda", "how to use karanawa", "research eka gana"
    - Detect: English, Sinhala (සිංහල), Tamil (தமிழ்), Singlish
    - Store detected_language in chat_messages
        ↓
[2] QUERY PREPROCESSING  
    - If Singlish → transliterate to English using custom mapping
    - If Sinhala/Tamil → translate to English using Helsinki-NLP/opus-mt models
    - Keep original content in original_content column
    - Preprocessed English query used for embedding search
        ↓
[3] QUERY EMBEDDING
    - Generate SBERT embedding of the English query
    - This embedding used for vector similarity search
        ↓
[4] RAG RETRIEVAL (from Supabase pgvector)
    - Call search_paper_chunks() function
    - Retrieve top-8 most relevant chunks
    - Filter by session's paper_ids (if paper-specific chat)
    - Or search across all user's papers (if corpus-wide)
    - Return: chunk texts + paper titles + sections + similarity scores
        ↓
[5] CONTEXT ASSEMBLY
    - Sort retrieved chunks by relevance score
    - Assemble context window (max ~3000 tokens of context)
    - Include paper titles and section headings for citation
    - Format as structured context block
        ↓
[6] LLM GENERATION (with RAG context)
    - Use the fine-tuned LLM (or fallback to API-based model)
    - System prompt includes:
      * "You are a research paper assistant. Answer based on provided context."
      * "Always cite which paper and section your answer comes from."
      * "If the context doesn't contain the answer, say so clearly."
      * "Respond in {detected_language} language."
    - Stream response tokens to frontend via SSE
        ↓
[7] RESPONSE POST-PROCESSING
    - If user language was Sinhala → translate response to Sinhala
    - If Tamil → translate to Tamil
    - If Singlish → respond in Singlish-style English
    - If English → respond in English (default)
    - Add inline citations: [Paper Title, Section X, Page Y]
        ↓
[8] SAVE & QUEUE FOR TRAINING
    - Save message to chat_messages table
    - Save retrieved_chunks and citations as JSONB
    - Queue the Q&A pair in training_data_queue for model improvement
    - If user gives feedback (thumbs up/down) → also queue that
```

### 2.2 Multilingual Support Implementation

```
LANGUAGE SERVICE SPECIFICATION:

SUPPORTED LANGUAGES:
  1. English (en) — Primary, no translation needed
  2. Sinhala (si) — Full Unicode Sinhala script support
  3. Tamil (ta) — Full Unicode Tamil script support  
  4. Singlish — Romanized Sinhala mixed with English

SINGLISH PROCESSOR (singlish_processor.py):
  This is the most complex language task. Singlish examples:
  
  Input: "me research paper eke methodology eka gana kiyanna"
  Meaning: "Tell me about the methodology of this research paper"
  
  Input: "meka hodai da for my research?"
  Meaning: "Is this good for my research?"
  
  Input: "citation format eka APA da IEEE da?"
  Meaning: "Is the citation format APA or IEEE?"
  
  Input: "supervisor kenek recommend karanna"
  Meaning: "Recommend a supervisor"
  
  SINGLISH → ENGLISH APPROACH:
  1. Dictionary mapping for common Sinhala-romanized words:
     {
         "eka": "the/this", "da": "?/is it", "gana": "about",
         "kiyanna": "tell/say", "hodai": "good", "karanna": "do/make",
         "mokakda": "what is", "kohomada": "how", "aye": "why",
         "meka": "this", "eka": "that one", "tiyenawa": "have/exists",
         "danna": "know", "banna": "cannot", "puluwan": "can",
         "kenek": "person/someone", "walata": "for", "wala": "in/of"
     }
  2. Keep English words as-is
  3. Use context from surrounding English words to disambiguate
  4. If ambiguous, use the SBERT embedding to match intent

TRANSLATION MODELS:
  - English ↔ Sinhala: Helsinki-NLP/opus-mt-en-si, opus-mt-si-en
  - English ↔ Tamil: Helsinki-NLP/opus-mt-en-ta, opus-mt-ta-en
  - Fallback: Google Translate API (for edge cases)
  
LANGUAGE DETECTION RULES:
  1. Check for Sinhala Unicode range (U+0D80–U+0DFF) → Sinhala
  2. Check for Tamil Unicode range (U+0B80–U+0BFF) → Tamil
  3. Check for Singlish patterns (mixed romanized + English) → Singlish
  4. Default → English
  
RESPONSE LANGUAGE:
  - Always respond in the same language the user used
  - For Singlish: respond in casual English with some Romanized Sinhala terms
  - For Sinhala: Full Sinhala Unicode response with technical terms in English
  - For Tamil: Full Tamil Unicode response with technical terms in English
  - User can override via LanguageSelector component
```

### 2.3 Chat UI Components Specification

```
ChatWindow.tsx:
  - Full-height chat interface (similar to ChatGPT)
  - Paper context panel on left (collapsible sidebar)
  - Message area with auto-scroll
  - Fixed input bar at bottom
  - Language indicator badge on each message
  - Streaming response with typing animation
  - Citation hover cards (show paper + section when hovering reference)

ChatInput.tsx:
  - Auto-expanding textarea
  - Send button + keyboard shortcut (Ctrl+Enter)
  - Language auto-detection indicator (shows detected language)
  - Manual language override dropdown
  - File attachment button (add more papers to context)
  - Voice input button (optional - Web Speech API)

ChatMessage.tsx:
  - User messages: right-aligned, colored bubble
  - Assistant messages: left-aligned, white/dark bubble
  - Citations rendered as clickable badges: [📄 Paper Title, p.5]
  - Clicking citation opens paper at that page/section
  - Thumbs up/down feedback buttons on assistant messages
  - "Copy" button on assistant messages
  - Language badge (🇬🇧/🇱🇰/🇮🇳 flag icon)
  - Markdown rendering for formatted responses

PaperSelector.tsx:
  - Shown when starting a new chat or adding papers to existing chat
  - Grid of user's uploaded papers (with search/filter)
  - Multi-select with checkboxes
  - Shows paper title, author, upload date, page count
  - "Select All" / "Clear" buttons
  - Selected papers appear as chips in chat header

ChatSidebar.tsx:
  - "New Chat" button at top
  - Chat history list (sorted by last message date)
  - Each item shows: title, paper count icon, message count, last active
  - Search past conversations
  - Delete/archive chat options
```

### 2.4 API Endpoints — New Routes

```
API GATEWAY ROUTES (apps/api-gateway/src/routes/):

# Paper Upload & Management
POST   /api/v1/papers/upload              # Upload PDF to Supabase Storage
POST   /api/v1/papers/process             # Trigger processing pipeline
GET    /api/v1/papers                     # List user's papers (paginated)
GET    /api/v1/papers/:id                 # Get single paper with metadata
GET    /api/v1/papers/:id/chunks          # Get paper chunks
DELETE /api/v1/papers/:id                 # Delete paper + chunks + embeddings
PATCH  /api/v1/papers/:id                 # Update paper metadata
POST   /api/v1/papers/:id/reprocess      # Re-run processing pipeline
GET    /api/v1/papers/:id/training-data   # Get paper's training data JSON

# Chat
POST   /api/v1/chat/sessions              # Create new chat session
GET    /api/v1/chat/sessions              # List user's chat sessions
GET    /api/v1/chat/sessions/:id          # Get session with messages
DELETE /api/v1/chat/sessions/:id          # Delete chat session
POST   /api/v1/chat/sessions/:id/message  # Send message (SSE streaming response)
POST   /api/v1/chat/sessions/:id/feedback # Rate a message (thumbs up/down)
PATCH  /api/v1/chat/sessions/:id/papers   # Add/remove papers from session context

# Language
POST   /api/v1/language/detect            # Detect language of text
POST   /api/v1/language/translate         # Translate text between languages

# Training
GET    /api/v1/training/status            # Get training pipeline status
GET    /api/v1/training/queue             # View queued training data
POST   /api/v1/training/trigger           # Manually trigger training cycle
GET    /api/v1/training/models            # List model versions & metrics

→ All proxied to Python FastAPI service: paper-chat (port 8005)
```

---

## 🔄 FEATURE 3: CONTINUOUS LEARNING PIPELINE

### 3.1 How User Data Feeds Back Into Models

```
CONTINUOUS TRAINING ARCHITECTURE:

═══════════════════════════════════════════════════════
DATA COLLECTION (Automatic — happens on every interaction)
═══════════════════════════════════════════════════════

TRIGGER 1 — Paper Upload:
  When: User uploads a new research paper
  What's collected:
    - Full extracted text + structured JSON
    - Parsed references (for citation NER training)
    - Abstract (for summarization ground truth)
    - Topics/keywords (for SciBERT classifier)
    - Metadata (for trend analysis time series)
  Queued for: sbert, scibert_classifier, citation_ner, summarizer, 
              proposal_llm, trend_forecaster, quality_scorer

TRIGGER 2 — Chat Q&A:
  When: User asks a question and receives an answer
  What's collected:
    - Question text (in detected language + English translation)
    - Answer text
    - Retrieved chunk IDs and similarity scores
    - Session context (which papers were in context)
  Queued for: rag_retriever, sbert (query-document pairs)

TRIGGER 3 — User Feedback:
  When: User clicks thumbs up/down or gives rating
  What's collected:
    - The Q&A pair with quality rating
    - Was the answer helpful? (boolean)
    - Optional text feedback
  Effect: 
    - Positive feedback → higher quality_score in queue
    - Negative feedback → flagged for review, lower quality_score
    - Used for RLHF-style preference data
  Queued for: rag_retriever, sbert, proposal_llm

TRIGGER 4 — Module Interactions:
  When: User interacts with any of the 4 modules
  What's collected:
    - Module 1: Citations parsed → citation_ner training data
    - Module 1: Gaps identified → gap analysis training data
    - Module 2: Supervisor matches accepted/rejected → recommendation training
    - Module 2: Feedback analyzed → sentiment model training data
    - Module 3: Topic categorizations confirmed → SciBERT training data
    - Module 4: Quality scores validated → quality scorer training data
  Queued for: respective module's models

═══════════════════════════════════════════════════════
DATA PROCESSING (Periodic — runs on schedule or manual trigger)
═══════════════════════════════════════════════════════

TRAINING PIPELINE (continuous_trainer.py):

1. DATA ASSESSMENT (every 1 hour):
   - Count pending items in training_data_queue per model
   - Check quality_score distribution
   - Filter out low-quality data (score < 0.3)
   - Log statistics to training dashboard

2. BATCH PREPARATION (when threshold reached):
   Thresholds per model:
   - sbert: 50 new text pairs → trigger fine-tuning
   - scibert_classifier: 30 new labeled papers → trigger
   - citation_ner: 100 new annotated references → trigger
   - summarizer: 20 new paper-abstract pairs → trigger
   - sentiment: 50 new feedback entries → trigger
   - rag_retriever: 100 new Q&A pairs → trigger retriever tuning
   - quality_scorer: 30 new validated scores → trigger
   
   When threshold met:
   a. Pull pending data from training_data_queue
   b. Format into model-specific training format
   c. Split: 80% train, 10% validation, 10% holdout
   d. Save formatted batch to ml/data/training_queue/pending/
   e. Update queue status to 'preprocessing'

3. INCREMENTAL TRAINING (triggered when batch ready):
   For each model with a pending batch:
   
   a. Load current active model version
   b. Prepare incremental training data
   c. Run fine-tuning with LOW learning rate (1e-6 to 5e-6)
      - Few epochs only (1-3) to avoid catastrophic forgetting
      - Use learning rate warmup
   d. Evaluate on validation set
   e. Compare with current active model metrics
   f. If improved → save as new version, set is_active = true
   g. If worse → discard, keep current model active
   h. Update training_data_queue status to 'completed'
   i. Log everything to model_versions table

4. MODEL VERSIONING:
   - Every training run creates new entry in model_versions
   - Track: model_name, version (semver), metrics, training data count
   - Easy rollback: set is_active = false on bad model, reactivate previous
   - Baseline comparison: improvement_over_baseline shows % change

═══════════════════════════════════════════════════════
INTEGRATION WITH ALL 4 MODULES
═══════════════════════════════════════════════════════

MODULE 1 (Integrity) — How uploaded papers enhance it:
  - Citation NER model improves with each parsed reference
  - Gap analysis corpus grows → more accurate gap detection
  - Plagiarism comparison pool expands
  - RAG context for proposal generation enriched
  - Mind map knowledge graph expands with new concepts

MODULE 2 (Collaboration) — How uploaded papers enhance it:
  - Supervisor matching embeddings improve with more paper data
  - New paper embeddings improve cosine similarity accuracy
  - Sentiment model learns from feedback on chat interactions
  - Peer recommendation learns from which papers users share

MODULE 3 (Data Management) — How uploaded papers enhance it:
  - SciBERT topic classifier gets new labeled training data
  - BERTopic discovers new emerging themes from user papers
  - Plagiarism trend database grows with each upload
  - Summarizer improves with more paper-abstract pairs
  - Data quality patterns learned from upload quality

MODULE 4 (Analytics) — How uploaded papers enhance it:
  - Trend forecasting gets new data points for time series
  - Quality scoring model calibrated with new examples
  - Mind map concept graph grows with new relationships
  - Success prediction features enriched with new project data
```

### 3.2 Training Data Flow Diagram

```
                    ┌─────────────┐
                    │   USER      │
                    └──────┬──────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
    ┌──────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
    │Upload Paper │ │ Chat Q&A    │ │ Module Use  │
    │   (PDF)     │ │(any language)│ │ (1,2,3,4)  │
    └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
           │               │               │
    ┌──────▼──────────────▼───────────────▼──────┐
    │         Supabase Database                    │
    │  ┌─────────────────────────────────────┐    │
    │  │     training_data_queue table       │    │
    │  │  (all interactions queued here)      │    │
    │  └──────────────┬──────────────────────┘    │
    └─────────────────┼───────────────────────────┘
                      │
           ┌──────────▼──────────┐
           │  Continuous Trainer  │
           │  (periodic check)   │
           └──────────┬──────────┘
                      │
    ┌─────────────────┼─────────────────┐
    │                 │                 │
    ▼                 ▼                 ▼
┌────────┐     ┌──────────┐     ┌──────────┐
│ SBERT  │     │ SciBERT  │     │ Citation │  ... (all models)
│Retrain │     │ Retrain  │     │NER Retrain│
└───┬────┘     └────┬─────┘     └────┬─────┘
    │               │                │
    └───────────────┼────────────────┘
                    │
           ┌────────▼────────┐
           │  model_versions │
           │  table (track)  │
           └────────┬────────┘
                    │
           ┌────────▼────────┐
           │ Active Models   │
           │ (serving users) │
           └─────────────────┘
```

---

## 🔧 IMPLEMENTATION PRIORITY ORDER

```
PHASE 1 — Paper Upload (Week 1-2):
  1. Create Supabase tables (migrations 009, 010, 011)
  2. Build PaperUploader.tsx component (drag-drop, multi-file)
  3. Build pdf_processor.py (extraction pipeline)
  4. Build chunk_manager.py + embedding_service.py
  5. Wire up upload → process → store → ready flow
  6. Show processing status in real-time (Supabase Realtime)
  7. Build paper library page (grid view with search)
  8. Build paper detail page (show extracted metadata + full text)
  
PHASE 2 — RAG Chat Engine (Week 2-3):
  1. Build rag_engine.py (retrieval + generation)
  2. Build language_service.py + singlish_processor.py
  3. Build chat_service.py (orchestration + streaming)
  4. Implement search_paper_chunks() function in Supabase
  5. Build ChatWindow.tsx + ChatInput.tsx + ChatMessage.tsx
  6. Implement SSE streaming for real-time response
  7. Add citation references in responses
  8. Test with all 3 languages + Singlish

PHASE 3 — Multilingual Polish (Week 3-4):
  1. Fine-tune language detection for Singlish
  2. Build comprehensive Singlish dictionary (500+ words)
  3. Test Sinhala/Tamil Unicode rendering in chat
  4. Add language indicator badges
  5. Test edge cases (code-switching mid-sentence)

PHASE 4 — Continuous Training (Week 4-5):
  1. Build training_pipeline.py (data collection)
  2. Build data_formatter.py (JSON formatting)
  3. Build continuous_trainer.py (incremental training)
  4. Build model_versioner.py (version management)
  5. Wire up all triggers (upload, chat, feedback, module use)
  6. Build training dashboard (view model versions, metrics)
  7. Test full loop: upload → chat → feedback → retrain → improved

PHASE 5 — Module Integration (Week 5-6):
  1. Connect uploaded papers to Module 1 corpus
  2. Connect to Module 2 knowledge base
  3. Connect to Module 3 pipeline
  4. Connect to Module 4 analytics
  5. Add paper upload button in each module's relevant pages
  6. End-to-end testing across all modules
```

---

## 📋 ENVIRONMENT VARIABLES (New Additions)

```env
# Paper Processing
MAX_UPLOAD_SIZE_MB=50
MAX_PAPERS_PER_USER=100
CHUNK_SIZE_TOKENS=512
CHUNK_OVERLAP_TOKENS=64

# Chat
CHAT_MAX_CONTEXT_TOKENS=3000
CHAT_MAX_RESPONSE_TOKENS=2000
CHAT_STREAMING_ENABLED=true
RAG_SIMILARITY_THRESHOLD=0.6
RAG_TOP_K_CHUNKS=8

# Language
SINGLISH_DICT_PATH=./data/singlish_dictionary.json
TRANSLATION_MODEL_SI=Helsinki-NLP/opus-mt-en-si
TRANSLATION_MODEL_TA=Helsinki-NLP/opus-mt-en-ta

# Continuous Training
TRAINING_CHECK_INTERVAL_HOURS=1
SBERT_TRAINING_THRESHOLD=50
SCIBERT_TRAINING_THRESHOLD=30
TRAINING_LEARNING_RATE=1e-6
TRAINING_MAX_EPOCHS=3

# Paper Chat Service
PAPER_CHAT_SERVICE_PORT=8005
PAPER_CHAT_SERVICE_URL=http://localhost:8005
```

---

## ⚠️ CRITICAL RULES

1. **Paper data must ALWAYS be stored as structured JSON** — never just raw text dumps
2. **Every chat message must save detected_language** — no exceptions
3. **Every uploaded paper must go through the FULL processing pipeline** — no shortcuts
4. **Training data queue must be append-only** — never delete, only mark as processed
5. **Model versions must NEVER be overwritten** — always create new version
6. **Singlish dictionary must be extensible** — store in JSON file, not hardcoded
7. **Chat responses must ALWAYS cite sources** — include paper title + section
8. **SSE streaming must work for ALL languages** — test Unicode streaming
9. **RLS policies must cover ALL new tables** — users can ONLY see their own data
10. **Processing pipeline must be IDEMPOTENT** — re-running on same paper produces same result

---

> **START WITH PHASE 1.** Create the Supabase migrations first, then build the paper upload pipeline. The chat and training features build on top of the paper processing infrastructure.
