# MCP Memory Server v1.0

A production-style Memory Server built using the Model Context Protocol (MCP), PostgreSQL, pgvector, local embeddings, and Ollama.

This project provides long-term memory capabilities for AI agents by combining structured storage, semantic retrieval, hybrid search, automatic tagging, summarization, and Retrieval-Augmented Generation (RAG).

---

## Features

### Memory Storage

* Store memories with metadata
* PostgreSQL-backed persistence
* Memory update and soft-delete support
* Duplicate memory detection

### Semantic Retrieval

* Local embeddings using Sentence Transformers
* pgvector-powered vector similarity search
* Hybrid search (keyword + semantic retrieval)
* Similarity scoring and ranking

#### Semantic Similarity Guide

The system uses cosine similarity derived from pgvector embeddings.

##### Rough Guide

| Similarity Score | Interpretation |
|-----------------|----------------|
| 0.70 - 1.00 | Very Similar |
| 0.50 - 0.70 | Related |
| 0.30 - 0.50 | Weak Relation |
| Below 0.30 | Usually Unrelated |

##### Examples

Query:
fintech business

Memory:
Ali wants to build an AI finance startup

Similarity:
0.73 → Very Similar

---

Query:
business

Memory:
Ali wants to build an AI finance startup

Similarity:
~0.55 → Related

---

Query:
hassan

Memory:
Ali likes football

Similarity:
~0.34 → Weak Relation

Usually filtered out before answer generation.

### AI-Powered Memory

* Local RAG using Ollama
* Source-aware answers
* Confidence scoring
* Hallucination reduction through retrieval filtering

### Memory Organization

* Automatic AI-generated tagging
* Topic-based summarization
* Tag-based search
* Importance scoring

### Memory Management

* Context optimization
* Soft deletion
* Memory updates
* Duplicate prevention

---

## Architecture

```text
User Question
      │
      ▼
MCP Tool
      │
      ▼
Hybrid Retrieval
(Keyword + Semantic Search)
      │
      ▼
Context Optimization
(Filter Weak Memories)
      │
      ▼
Ollama (LLM)
      │
      ▼
Answer + Confidence + Sources
```

### Storage Layer

```text
PostgreSQL
   │
   ├── Memory Records
   ├── Metadata
   ├── Tags
   ├── Importance Scores
   └── Embeddings (pgvector)
```

---

## Technology Stack

### Backend

* Python
* MCP Python SDK
* PostgreSQL
* pgvector

### AI Components

* Sentence Transformers
* all-MiniLM-L6-v2 embeddings model
* Ollama
* Llama 3.2

### Database

* PostgreSQL 16
* pgvector extension

---

## Project Structure

```text
mcp-memory-server/
│
├── mcp_server.py
├── db_init.py
├── db_upgrade_phase4.py
├── db_upgrade_phase6.py
├── db_upgrade_phase7.py
├── backfill_embeddings.py
├── .env
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd mcp-memory-server
```

### 2. Create Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Start PostgreSQL + pgvector

```bash
docker run --name mcp-postgres \
-e POSTGRES_USER=mcp_user \
-e POSTGRES_PASSWORD=mcp_pass \
-e POSTGRES_DB=mcp_memory \
-p 5432:5432 \
-d pgvector/pgvector:pg16
```

### 5. Configure Environment

Create `.env`

```env
DATABASE_URL=postgresql://mcp_user:mcp_pass@localhost:5432/mcp_memory
```

### 6. Initialize Database

```bash
python db_init.py
python db_upgrade_phase4.py
python db_upgrade_phase6.py
python db_upgrade_phase7.py
```

### 7. Install Ollama Model

```bash
ollama pull llama3.2
```

### 8. Run Server

```bash
python mcp_server.py
```

---

## Available MCP Tools

### Memory Operations

* store_memory
* get_memories
* update_memory
* delete_memory

### Search Operations

* search_memory
* semantic_search_memory
* hybrid_search_memory
* search_by_tag

### AI Operations

* answer_from_memory
* summarize_memories

---

## Example Queries

### Store Memory

```text
Ali wants to build an AI finance startup
```

### Semantic Search

```text
fintech business idea
```

Returns:

```text
Ali wants to build an AI finance startup
```

### Ask Questions

```text
What business idea does Ali want to build?
```

Returns:

```json
{
  "answer": "Ali wants to build an AI finance startup.",
  "confidence": "high",
  "sources": [...]
}
```

---

## Learning Outcomes

This project demonstrates:

* Model Context Protocol (MCP)
* Vector Databases
* Embeddings
* Semantic Search
* Hybrid Retrieval
* Retrieval-Augmented Generation (RAG)
* Local LLM Integration
* Memory Management
* Context Optimization
* AI Agent Infrastructure

---

## Future Improvements

### Planned

* Memory relationships and knowledge graphs
* Multi-user authentication
* Memory dashboard UI
* Memory versioning
* Advanced ranking strategies
* Multi-agent integration

### Long-Term Vision

Transform the memory server into a reusable AI memory platform that can serve multiple agents and applications through the Model Context Protocol.

---

## Version

Current Release:

```text
v1.0.0
```

Production Features Included:

* Semantic Search
* Hybrid Search
* RAG Answer Generation
* Auto Tagging
* Summarization
* Memory Lifecycle Management
* Context Optimization


