"""Quick verification script to check cleaning results"""
import json
from pathlib import Path

input_file = Path("extracted_data/resumes_cleaned.json")
if not input_file.exists():
    print(f"❌ File not found: {input_file}")
    print("Please run cleaning_resumes.py first!")
    exit(1)

with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"✅ Total cleaned resumes: {len(data)}")
print(f"\n📊 Sample cleaned resumes:\n")

for i in [0, 38, 47, 100]:
    if i < len(data):
        r = data[i]
        print(f"Resume {i}:")
        print(f"  ID: {r.get('ID', r.get('id', 'N/A'))}")
        print(f"  Category: {r.get('category', 'N/A')}")
        print(f"  Summary: {r.get('summary', 'N/A')[:80]}...")
        print(f"  Work Experience: {r.get('work_experience', 'N/A')[:80]}...")
        print(f"  Education: {r.get('education', 'N/A')[:80]}...")
        print(f"  Skills: {r.get('skills', 'N/A')[:100]}...")
        print()

