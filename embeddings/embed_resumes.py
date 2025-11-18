"""
Prepares and embeds resume fields into a Chroma collection named resumes, 
embedding selected fields separately (summary, education, work_experience, skills).
"""

import json
import os
from typing import List, Dict, Any
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions # Chroma helper wrappers for embedding models
from tqdm import tqdm  # progress bars for loops.
import logging

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

def get_resumes_collection(persist_directory: str = "chroma_db"):
    """
    Collection ready to accept documents; 
    embeddings will be produced via SentenceTransformerEmbeddingFunction.
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

    # creates the collection with cosine similarity metadata.
    collection = client.get_or_create_collection(
        name="resumes",
        embedding_function=embedding_function,
        metadata={"hnsw:space": "cosine"}
    )
    logger.info("✅ Resumes collection ready with FREE embeddings")
    return collection

def add_resumes_to_chroma(resumes: List[Dict[str, Any]],collection,batch_size: int = 100):
    """Add resumes to Chroma collection with embeddings - each field separately"""
    logger.info(f"Processing {len(resumes)} resumes...")
    
    documents = []
    metadatas = []
    ids = []
    
    # Fields to embed separately
    fields_to_embed = ["summary", "education", "work_experience", "skills"]
    
    for idx, record in enumerate(tqdm(resumes, desc="Preparing resumes")):
        # Handle both old format (id) and new format (ID)
        resume_id = record.get("ID") or record.get("id", f"resume_{idx}")
        category = record.get("category", "unknown")
        
        # Base metadata for all fields from this resume
        base_metadata = {
            "id": str(resume_id),
            "category": str(category),
            "source": "resumes_cleaned.json"
        }
        
        # Embed each field separately
        for field in fields_to_embed:
            field_value = record.get(field, "")
            
            # Skip empty fields
            if not field_value or not str(field_value).strip():
                continue
            
            # Create document with just this field
            documents.append(str(field_value))
            
            # Create metadata with field type
            metadata = base_metadata.copy()
            metadata["field_type"] = field
            metadatas.append(metadata)
            
            # Create unique ID for this field
            doc_id = f"resume_{resume_id}_{field}_{category.replace(' ', '_')}"
            ids.append(doc_id)
    
    # Add to Chroma in batches
    logger.info(f"Adding {len(documents)} resume fields to Chroma...")
    for i in tqdm(range(0, len(documents), batch_size), desc="Adding to Chroma"):
        batch_docs = documents[i:i+batch_size]
        batch_metas = metadatas[i:i+batch_size]
        batch_ids = ids[i:i+batch_size]
        
        collection.add(
            documents=batch_docs,
            metadatas=batch_metas,
            ids=batch_ids
        )
    
    logger.info(f"✅ Successfully added {len(documents)} resume fields to Chroma")


def embed_resumes(
    input_file: str = "extracted_data_cleaned/resumes_cleaned.json",
    persist_directory: str = "chroma_db",
    batch_size: int = 100
):
    """
    Main function to embed resumes
    
    Args:
        input_file: Path to resumes JSON file
        persist_directory: Directory to store Chroma database
        batch_size: Batch size for adding documents to Chroma
    """
    logger.info("=" * 70)
    logger.info("Embedding Resumes")
    logger.info("=" * 70)
    
    # Load resumes
    resumes = load_json_file(input_file)
    
    if not resumes:
        logger.error("No resumes found to process!")
        return
    
    # Get collection
    collection = get_resumes_collection(persist_directory)
    
    # Process and add to Chroma
    add_resumes_to_chroma(resumes, collection, batch_size)
    
    # Print collection info
    count = collection.count()
    logger.info(f"\n✅ Resumes Collection: {count} documents")
    
    return collection


if __name__ == "__main__":
    # Run standalone
    embed_resumes()
