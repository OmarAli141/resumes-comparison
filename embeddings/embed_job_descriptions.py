"""
Embeds job descriptions into ChromaDB collection.
Uses structured chunks from job_descriptions_structured.json
"""

import json
import os
from typing import List, Dict, Any
import chromadb
from chromadb.utils import embedding_functions
from tqdm import tqdm
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_json_file(file_path: str) -> List[Dict[str, Any]]:
    """Load JSON data from file"""
    # Convert to Path and resolve relative to project root if needed
    path = Path(file_path)
    if not path.is_absolute():
        # If relative, resolve from embeddings directory to project root
        project_root = Path(__file__).parent.parent
        path = project_root / file_path.lstrip("../")
    
    if not path.exists():
        logger.error(f"File not found: {path}")
        return []
    
    logger.info(f"Loading {path}...")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    logger.info(f"Loaded {len(data)} records from {path}")
    return data


def get_job_descriptions_collection(persist_directory: str = "chroma_db"):
    """
    Get or create ChromaDB collection for job descriptions.
    """
    # Resolve path relative to project root
    path = Path(persist_directory)
    if not path.is_absolute():
        project_root = Path(__file__).parent.parent
        path = project_root / persist_directory
    
    os.makedirs(path, exist_ok=True)
    client = chromadb.PersistentClient(path=str(path))

    # FREE embedder
    embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )

    # Create collection with cosine similarity
    collection = client.get_or_create_collection(
        name="job_descriptions",
        embedding_function=embedding_function,
        metadata={"hnsw:space": "cosine"}
    )
    logger.info("✅ Job Descriptions collection ready with FREE embeddings")
    return collection


def add_job_descriptions_to_chroma(
    job_descriptions: List[Dict[str, Any]], 
    collection,
    batch_size: int = 100
):
    """Add job descriptions to Chroma collection - each structured chunk separately"""
    logger.info(f"Processing {len(job_descriptions)} job descriptions...")
    
    documents = []
    metadatas = []
    ids = []
    
    for idx, jd in enumerate(tqdm(job_descriptions, desc="Preparing job descriptions")):
        position_title = jd.get("position_title", f"job_{idx}")
        structured_chunks = jd.get("structured_chunks", [])
        
        if not structured_chunks:
            logger.warning(f"No structured chunks found for {position_title}, skipping...")
            continue
        
        # Embed each chunk separately
        for chunk_idx, chunk in enumerate(structured_chunks):
            if not chunk or not str(chunk).strip():
                continue
            
            # Create document
            documents.append(str(chunk))
            
            # Create metadata
            metadata = {
                "position_title": str(position_title),
                "chunk_index": chunk_idx,
                "total_chunks": len(structured_chunks),
                "source": "job_descriptions_cleaned.json"
            }
            metadatas.append(metadata)
            
            # Create unique ID
            doc_id = f"jd_{idx}_chunk_{chunk_idx}_{position_title.replace(' ', '_')}"
            ids.append(doc_id)
    
    # Add to Chroma in batches
    logger.info(f"Adding {len(documents)} job description chunks to Chroma...")
    for i in tqdm(range(0, len(documents), batch_size), desc="Adding to Chroma"):
        batch_docs = documents[i:i+batch_size]
        batch_metas = metadatas[i:i+batch_size]
        batch_ids = ids[i:i+batch_size]
        
        collection.add(
            documents=batch_docs,
            metadatas=batch_metas,
            ids=batch_ids
        )
    
    logger.info(f"✅ Successfully added {len(documents)} job description chunks to Chroma")


def embed_job_descriptions(
    input_file: str = "extracted_data_cleaned/job_descriptions_cleaned.json",
    persist_directory: str = "chroma_db",
    batch_size: int = 100
):
    """
    Main function to embed job descriptions
    
    Args:
        input_file: Path to structured job descriptions JSON file
        persist_directory: Directory to store Chroma database
        batch_size: Batch size for adding documents to Chroma
    """
    logger.info("=" * 70)
    logger.info("Embedding Job Descriptions")
    logger.info("=" * 70)
    
    # Load job descriptions
    job_descriptions = load_json_file(input_file)
    
    if not job_descriptions:
        logger.error("No job descriptions found to process!")
        return
    
    # Get collection
    collection = get_job_descriptions_collection(persist_directory)
    
    # Process and add to Chroma
    add_job_descriptions_to_chroma(job_descriptions, collection, batch_size)
    
    # Print collection info
    count = collection.count()
    logger.info(f"\n✅ Job Descriptions Collection: {count} documents")
    
    return collection


if __name__ == "__main__":
    # Run standalone
    embed_job_descriptions()

