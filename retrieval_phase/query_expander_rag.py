# retrieval_phase/get_related_titles.py
# Returns ONLY clean, professional job titles filtered by seniority level

from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions

# === Paths ===
ROOT = Path(__file__).parent.parent
CHROMA_PATH = ROOT / "chroma_db"

# === Chroma Setup ===
client = chromadb.PersistentClient(path=str(CHROMA_PATH))
embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

try:
    title_collection = client.get_collection("job_titles_index")
    resumes_collection = client.get_collection("resumes")
    print("✅ Collections loaded.\n")
except Exception as e:
    print(f"❌ ERROR: Collections not found! {e}")
    print("Run: python retrieval_phase/build_clean_title_index.py")
    print("And: python embeddings/embed_resumes.py")
    exit()


def expand_query_with_similar_titles(query: str, similarity_threshold: float = 0.65, max_similar: int = 10) -> list:
    """
    Automatically find semantically similar job titles using embeddings.
    No manual lists needed - uses semantic similarity from your actual database!
    
    Args:
        query: User's job title query (e.g., "AI Engineer")
        similarity_threshold: Minimum similarity score (0-1)
        max_similar: Maximum number of similar titles to return
    
    Returns:
        List of similar job titles including the original query
    """
    # Query the title collection to find similar titles
    results = title_collection.query(
        query_texts=[query],
        n_results=max_similar * 2,  # Get more to filter
        include=["documents", "distances"]
    )
    
    similar_titles = [query]  # Always include original query
    titles = results["documents"][0]
    distances = results["distances"][0]
    
    # Add titles that are similar enough
    for title, dist in zip(titles, distances):
        similarity = 1 - dist
        if similarity >= similarity_threshold and title not in similar_titles:
            # Skip sentence-like titles
            if len(title.split()) <= 8 and not any(word in title.lower() for word in 
                ["years", "experience", "domain", "skilled at", "focused on"]):
                similar_titles.append(title)
        
        if len(similar_titles) >= max_similar + 1:  # +1 for original query
            break
    
    return similar_titles


def get_related_titles(query: str, seniority: str = None, top_k: int = 10, auto_expand: bool = True):
    """
    Get related job titles filtered by seniority level.
    Automatically expands query to include semantically similar titles!
    
    Args:
        query: Job title or category (e.g., "AI Engineer")
        seniority: "senior", "junior", "mid", "intern", or None for all
        top_k: Number of results to return
        auto_expand: If True, automatically find similar titles and search for all of them
    """
    print(f"🔍 Searching for: {query}")
    if seniority:
        print(f"📊 Seniority filter: {seniority}")
    
    # AUTOMATIC EXPANSION: Find similar titles using semantic similarity
    if auto_expand:
        similar_titles = expand_query_with_similar_titles(query, similarity_threshold=0.65, max_similar=8)
        if len(similar_titles) > 1:
            print(f"🧠 Auto-expanded to {len(similar_titles)} similar titles:")
            for i, title in enumerate(similar_titles[:5], 1):
                marker = "👈 Your query" if title == query else "   "
                print(f"   {marker} {i}. {title}")
            if len(similar_titles) > 5:
                print(f"   ... and {len(similar_titles) - 5} more")
            print()
            
            # Combine all similar titles into one search query
            expanded_query = " ".join(similar_titles)
        else:
            expanded_query = query
    else:
        expanded_query = query
    
    print()

    # Query with more results to filter by seniority
    query_size = top_k * 3 if seniority else top_k
    
    results = title_collection.query(
        query_texts=[expanded_query],
        n_results=query_size,
        include=["documents", "metadatas", "distances"]
    )

    titles = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    # Filter by seniority if specified
    filtered_results = []
    for title, meta, dist in zip(titles, metadatas, distances):
        if seniority:
            if meta.get("seniority", "mid") != seniority:
                continue
        
        # Additional validation: skip titles that look like sentences
        if len(title.split()) > 8:
            continue
        if any(word in title.lower() for word in ["years", "experience", "domain", "skilled at", "focused on"]):
            continue
        
        score = round(1 - dist, 4)
        filtered_results.append({
            "title": title,
            "seniority": meta.get("seniority", "mid"),
            "category": meta.get("category", ""),
            "score": score
        })
        
        if len(filtered_results) >= top_k:
            break

    # Display results
    print(f"📋 Top {len(filtered_results)} Professional Job Titles:\n")
    print("-" * 80)
    
    for i, result in enumerate(filtered_results, 1):
        seniority_label = result["seniority"].upper()
        print(f"{i:2}. {result['title']:<50} | {seniority_label:<6} | Score: {result['score']:.4f}")
    
    print("-" * 80)
    
    if not filtered_results:
        print("⚠️  No matching titles found. Try:")
        print("   - Different seniority level")
        print("   - Broader search term")
        print("   - Rebuild index: python retrieval_phase/build_clean_title_index.py")
    
    return filtered_results


def search_resumes_with_auto_expansion(query: str, seniority: str = None, top_k: int = 80):
    """
    Search resumes using automatic title expansion.
    When you search for "AI Engineer", it automatically finds similar titles
    and searches for all of them!
    
    Args:
        query: Job title (e.g., "AI Engineer")
        seniority: "senior", "junior", "mid", "intern", or None
        top_k: Number of candidates to return
    
    Returns:
        List of candidate dictionaries with resume_id, category, field_type, similarity
    """
    print(f"🔍 Searching resumes for: {query}")
    if seniority:
        print(f"📊 Seniority filter: {seniority}")
    print()
    
    # Step 1: Auto-expand query to find similar titles
    similar_titles = expand_query_with_similar_titles(query, similarity_threshold=0.65, max_similar=10)
    
    if len(similar_titles) > 1:
        print(f"🧠 Auto-expanded query to {len(similar_titles)} similar titles:")
        for i, title in enumerate(similar_titles[:8], 1):
            marker = "👈 Your query" if title == query else "   "
            print(f"   {marker} {i}. {title}")
        if len(similar_titles) > 8:
            print(f"   ... and {len(similar_titles) - 8} more")
        print()
    
    # Step 2: Combine all similar titles into one search query
    expanded_query = " ".join(similar_titles)
    
    # Step 3: Search resumes collection with expanded query
    print(f"🔎 Searching resumes collection...")
    results = resumes_collection.query(
        query_texts=[expanded_query],
        n_results=top_k * 2,  # Get more to filter by seniority if needed
        include=["metadatas", "distances"]
    )
    
    # Step 4: Process results
    seen = set()
    candidates = []
    
    for i, meta in enumerate(results["metadatas"][0]):
        resume_id = meta.get("id")
        if not resume_id or resume_id in seen:
            continue
        
        # Note: Seniority filtering would need to be done by loading resume data
        # For now, we return all candidates
        similarity = round(1 - results["distances"][0][i], 4)
        
        candidates.append({
            "resume_id": resume_id,
            "category": meta.get("category", "Unknown"),
            "field_type": meta.get("field_type", "N/A"),
            "similarity": similarity
        })
        
        seen.add(resume_id)
        
        if len(candidates) >= top_k:
            break
    
    print(f"✅ Found {len(candidates)} unique candidates")
    return candidates


def parse_user_input(user_input: str):
    """Parse user input to extract job title and seniority."""
    user_input = user_input.strip().lower()
    
    # Detect seniority keywords
    seniority = None
    seniority_keywords = {
        "senior": ["senior", "sr", "lead", "principal", "head", "chief"],
        "junior": ["junior", "jr", "entry", "associate", "assistant"],
        "intern": ["intern", "internship", "trainee"]
    }
    
    for level, keywords in seniority_keywords.items():
        if any(kw in user_input for kw in keywords):
            seniority = level
            # Remove seniority from query
            for kw in keywords:
                user_input = user_input.replace(kw, "").strip()
            break
    
    # Clean up query
    query = " ".join(user_input.split())
    
    return query, seniority


# === Run directly or import ===
if __name__ == "__main__":
    print("=" * 80)
    print("        PROFESSIONAL JOB TITLES SEARCH (with Seniority Filter)")
    print("=" * 80)
    print()
    print("Examples:")
    print("  - 'Financial Analyst senior' → Shows only senior-level Financial Analysts")
    print("  - 'Software Engineer junior' → Shows only junior Software Engineers")
    print("  - 'Accountant' → Shows all Accountants (all levels)")
    print()

    user_input = input("Enter job title/category [optional: add 'senior', 'junior', or 'intern']: ").strip()
    
    if not user_input:
        user_input = "Financial Analyst"
    
    # Parse input
    query, seniority = parse_user_input(user_input)
    
    if not query:
        query = "Financial Analyst"
    
    # Ask for seniority if not specified
    if not seniority:
        print()
        print("Select seniority level (or press Enter for all levels):")
        print("  1. Senior")
        print("  2. Mid-level")
        print("  3. Junior")
        print("  4. Intern")
        print("  5. All levels")
        
        choice = input("Choice (1-5): ").strip()
        seniority_map = {"1": "senior", "2": "mid", "3": "junior", "4": "intern", "5": None}
        seniority = seniority_map.get(choice, None)
    
    print()
    print("What would you like to do?")
    print("  1. Show related job titles only")
    print("  2. Search resumes with auto-expansion (recommended)")
    
    choice = input("Choice (1 or 2): ").strip()
    
    if choice == "2":
        print()
        candidates = search_resumes_with_auto_expansion(query, seniority=seniority, top_k=80)
        
        print(f"\n📋 Top {min(20, len(candidates))} Candidates:\n")
        print("-" * 80)
        for i, c in enumerate(candidates[:20], 1):
            print(f"{i:2}. Resume ID: {c['resume_id']:<15} | Category: {c['category']:<20} | "
                  f"Field: {c['field_type']:<15} | Score: {c['similarity']:.4f}")
        print("-" * 80)
        print(f"\n💡 Total candidates found: {len(candidates)}")
    else:
        get_related_titles(query, seniority=seniority, top_k=10)