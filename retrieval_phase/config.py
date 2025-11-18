from pathlib import Path

ROOT = Path(__file__).parent.parent
CHROMA = ROOT / "chroma_db"
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)

JDS_FULL = ROOT / "extracted_data" / "job_descriptions_filtered.json"
JDS_STRUCTURED = ROOT / "extracted_data" / "job_descriptions_structured.json"
RESUMES = ROOT / "extracted_data" / "resumes_data_pdfplumber.json"

TOP_K_INITIAL = 80        # pull 80 candidates with semantic search
TOP_K_FINAL = 10          # final ranked list
MIN_SCORE_ACCEPT = 0.70   # ATS "Accept" threshold

