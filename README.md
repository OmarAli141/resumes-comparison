# Resumes Comparison

A comprehensive resume analysis and job description matching system that uses semantic search and embeddings to match resumes with job descriptions.

## Overview

This project provides tools for:
- Extracting and parsing resume data from PDF files
- Extracting job descriptions from datasets
- Cleaning and structuring resume and job description data
- Creating semantic embeddings using ChromaDB
- Matching resumes to job descriptions using RAG (Retrieval-Augmented Generation) techniques
- Building job title indexes for improved search capabilities

## Project Structure

```
.
├── data/                           # Resume PDF files organized by category
├── extracted_data/                 # Raw extracted data (JSON)
├── extracted_data_cleaned/         # Cleaned and structured data
├── embeddings/                     # Scripts for creating embeddings
│   ├── embed_resumes.py           # Generate embeddings for resumes
│   └── embed_job_descriptions.py  # Generate embeddings for job descriptions
├── extracting_JD/                  # Job description extraction
│   └── job_description_extraction.py
├── extracting_pdfplumber/          # PDF extraction using pdfplumber
│   ├── extract_text.py
│   ├── resume_parser.py
│   └── run_extraction.py
├── query_structuring_JD/           # Job description structuring
│   ├── clean_and_structure_jds.py
│   └── match_resumes_to_jd.py
├── query_structuring_resumes/      # Resume structuring
│   ├── cleaning_resumes.py
│   └── verify_cleaning.py
├── retrieval_phase/                # Retrieval and matching phase
│   ├── build_clean_title_index.py # Build job title index
│   ├── config.py                   # Configuration settings
│   └── query_expander_rag.py      # RAG-based query expansion
└── results/                        # Output results directory
```

## Features

- **PDF Resume Parsing**: Extracts text and structured information from resume PDFs
- **Job Description Extraction**: Extracts and processes job descriptions from datasets
- **Data Cleaning**: Cleans and normalizes resume and job description data
- **Semantic Search**: Uses ChromaDB with sentence transformers for semantic search
- **Job Title Indexing**: Builds clean job title indexes for improved matching
- **RAG Integration**: Query expansion using RAG techniques for better matching

## Installation

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/resumes-comparison.git
cd resumes-comparison
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Requirements

- Python 3.8+
- See `requirements.txt` for package dependencies:
  - chromadb
  - pdfplumber
  - tqdm
  - datasets
  - sentence-transformers

## Usage

### 1. Extract Resume Data
```bash
python extracting_pdfplumber/run_extraction.py
```

### 2. Clean Resume Data
```bash
python query_structuring_resumes/cleaning_resumes.py
```

### 3. Extract Job Descriptions
```bash
python extracting_JD/job_description_extraction.py
```

### 4. Structure Job Descriptions
```bash
python query_structuring_JD/clean_and_structure_jds.py
```

### 5. Generate Embeddings
```bash
python embeddings/embed_resumes.py
python embeddings/embed_job_descriptions.py
```

### 6. Build Job Title Index
```bash
python retrieval_phase/build_clean_title_index.py
```

## Configuration

Edit `retrieval_phase/config.py` to adjust:
- `TOP_K_INITIAL`: Number of initial candidates (default: 80)
- `TOP_K_FINAL`: Final ranked list size (default: 10)
- `MIN_SCORE_ACCEPT`: ATS acceptance threshold (default: 0.70)

## Data Format

### Resume Data (JSON)
```json
{
  "ID": "resume_id",
  "category": "JOB_CATEGORY",
  "summary": "Resume summary text",
  "work_experience": "Work experience details",
  ...
}
```

### Job Description Data (JSON)
```json
{
  "id": "jd_id",
  "title": "Job Title",
  "description": "Job description text",
  ...
}
```

## Notes

- The `chroma_db/` directory stores the vector database and will be created automatically
- Large PDF files in `data/` directory are excluded from version control by default
- Results are saved in the `results/` directory

