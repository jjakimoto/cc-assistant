# Glossary: Paper Researcher Plugin

**Version:** 1.0
**Date:** 2026-01-27

---

## 1. Domain Terminology

### 1.1 Core Concepts

| Term | Definition | Usage |
|------|------------|-------|
| **Paper** | A research paper/preprint from arXiv or other academic source | "Collect papers on LLM agents" |
| **Collection** | The set of papers stored locally | "Search your collection" |
| **Summary** | AI-generated structured summary of a paper | "View paper summary" |
| **Digest** | Aggregated report of recently collected papers | "Generate weekly digest" |
| **Topic** | A keyword or phrase used to search for papers | "Topic: LLM agents" |

### 1.2 Paper Metadata

| Term | Definition | Example |
|------|------------|---------|
| **arXiv ID** | Unique identifier for arXiv papers | `2401.12345` |
| **Abstract** | Brief summary written by paper authors | First paragraph of paper |
| **Category** | arXiv classification code | `cs.CL`, `cs.AI`, `stat.ML` |
| **Authors** | Paper authors | `["Smith, John", "Doe, Jane"]` |
| **Published Date** | Original publication date | `2024-01-15` |
| **Updated Date** | Last revision date | `2024-01-20` |

### 1.3 Summary Structure

| Term | Definition |
|------|------------|
| **Problem** | The research question or challenge addressed |
| **Method** | The approach or technique used |
| **Results** | Key findings and metrics |
| **Takeaways** | Actionable insights and implications |

---

## 2. Technical Terminology

### 2.1 Claude Code Components

| Term | Definition | Location |
|------|------------|----------|
| **Plugin** | Extension package for Claude Code | `paper-researcher/` |
| **Command** | Slash command entry point | `commands/*.md` |
| **Skill** | Workflow package with scripts | `skills/{name}/` |
| **Agent** | Autonomous worker definition | `agents/*.md` |
| **Script** | Python utility called by skills | `skills/{name}/scripts/*.py` |

### 2.2 API Terms

| Term | Definition |
|------|------------|
| **arXiv API** | HTTP API for querying arXiv paper database |
| **Rate Limit** | Maximum request frequency (1 per 3 seconds for arXiv) |
| **Exponential Backoff** | Retry strategy with increasing delays |
| **Atom Feed** | XML format used by arXiv API responses |

### 2.3 Data Storage

| Term | Definition | Path |
|------|------------|------|
| **Data Directory** | Local storage for papers and indexes | `data/` |
| **Paper Directory** | Individual paper's files | `data/papers/{id}/` |
| **Index** | Searchable catalog of papers | `data/index/` |
| **Metadata File** | JSON file with paper information | `metadata.json` |

---

## 3. Action Terminology

### 3.1 User Actions

| Action | Definition | Command |
|--------|------------|---------|
| **Collect** | Fetch papers from source and store locally | `/paper-collect` |
| **Search** | Find papers in collection by query | `/paper-search` |
| **Summarize** | Generate/regenerate paper summary | `/paper-summarize` |
| **Digest** | Create aggregated paper report | `/paper-digest` |

### 3.2 System Actions

| Action | Definition |
|--------|------------|
| **Fetch** | Download paper metadata from arXiv |
| **Parse** | Extract data from API response or PDF |
| **Store** | Save paper to local filesystem |
| **Index** | Update searchable paper catalog |
| **Generate** | Create summary or digest content |

---

## 4. Status Terminology

### 4.1 Paper Status

| Status | Definition |
|--------|------------|
| **Collected** | Paper metadata saved locally |
| **Summarized** | Summary has been generated |
| **Unsummarized** | No summary generated yet |

### 4.2 Operation Status

| Status | Definition |
|--------|------------|
| **Success** | Operation completed successfully |
| **Failed** | Operation failed after retries |
| **Skipped** | Paper already exists, not re-collected |
| **Retry** | Operation being retried after failure |

---

## 5. Error Terminology

| Term | Definition |
|------|------------|
| **API Error** | arXiv API request failed |
| **Network Error** | Connection or timeout issue |
| **Parse Error** | Failed to extract data from response |
| **Storage Error** | Failed to read/write files |
| **Validation Error** | Invalid input data |

---

## 6. Abbreviations

| Abbreviation | Full Form |
|--------------|-----------|
| **API** | Application Programming Interface |
| **CLI** | Command Line Interface |
| **ID** | Identifier |
| **JSON** | JavaScript Object Notation |
| **PDF** | Portable Document Format |
| **URL** | Uniform Resource Locator |
| **LLM** | Large Language Model |
| **ML** | Machine Learning |
| **AI** | Artificial Intelligence |
| **CS** | Computer Science |

---

## 7. arXiv Categories

Common categories for filtering papers:

| Code | Category Name |
|------|---------------|
| `cs.CL` | Computation and Language |
| `cs.AI` | Artificial Intelligence |
| `cs.LG` | Machine Learning |
| `cs.CV` | Computer Vision and Pattern Recognition |
| `cs.NE` | Neural and Evolutionary Computing |
| `cs.IR` | Information Retrieval |
| `stat.ML` | Machine Learning (Statistics) |

---

## 8. Naming Conventions in Code

### 8.1 Variable Names

| Concept | Variable Name |
|---------|---------------|
| Paper metadata | `paper`, `paper_meta`, `metadata` |
| Paper ID | `paper_id`, `arxiv_id` |
| List of papers | `papers` |
| Search query | `query` |
| Search results | `results` |
| File path | `path`, `file_path` |
| Data directory | `data_dir` |

### 8.2 Function Names

| Action | Function Pattern |
|--------|------------------|
| Fetch data | `fetch_*()` |
| Parse data | `parse_*()` |
| Store data | `store_*()` |
| Search data | `search_*()` |
| Build output | `build_*()` |
| Validate input | `validate_*()` |

### 8.3 File Names

| Content | File Name |
|---------|-----------|
| arXiv fetching | `fetch_arxiv.py` |
| Paper storage | `store_paper.py` |
| PDF parsing | `parse_pdf.py` |
| Search indexing | `search_index.py` |
| Digest building | `build_digest.py` |

---

## 9. Cross-Reference

### 9.1 Synonyms to Avoid

| Preferred Term | Avoid |
|----------------|-------|
| Paper | Article, publication, document |
| Collection | Library, database, repository |
| Summary | Synopsis, abstract, overview |
| Collect | Download, fetch, import |
| Topic | Keyword, tag, subject |
| Digest | Report, newsletter, roundup |

### 9.2 Term Consistency

Always use these terms consistently:

- Use "paper" not "article" or "document"
- Use "collect" not "download" or "import"
- Use "summary" not "synopsis" (reserve "abstract" for author-written)
- Use "topic" not "keyword" or "tag"
