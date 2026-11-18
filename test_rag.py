"""Quick checks for retrieval and both MCP tools (no Inspector needed).

Run from the project root:  python test_rag.py
"""

import json
import sys
from pathlib import Path

from vectordb import collection
from rag import ask_query, MAX_DISTANCE
from mcp_server import search_admissions_info, get_key_dates

failures = 0


def check(label, ok, detail=""):
    global failures
    if not ok:
        failures += 1
    print(f"[{'PASS' if ok else 'FAIL'}] {label}" + (f"  ({detail})" if detail else ""))


# 1. Database contents
print("== Database ==")
count = collection.count()
check("collection is not empty", count > 0, f"{count} chunks")
metas = collection.get(include=["metadatas"])["metadatas"]
print("titles:", sorted({m["title"] for m in metas}))

# 2. Distance threshold: in-scope should pass, out-of-scope should be filtered
print(f"\n== Threshold (MAX_DISTANCE = {MAX_DISTANCE}) ==")
in_scope = [
    "When does the application period open?",
    "What is the appeal period?",
    "How many programmes can I choose?",
]
out_of_scope = [
    "What is the capital of France?",
    "Best pizza in Singapore",
]
for q in in_scope:
    d = ask_query(q, 1)[0]["distance"]
    check(f"in scope kept: {q}", d <= MAX_DISTANCE, f"distance {d:.3f}")
for q in out_of_scope:
    d = ask_query(q, 1)[0]["distance"]
    check(f"out of scope filtered: {q}", d > MAX_DISTANCE, f"distance {d:.3f}")

# 3. Tool 1: search_admissions_info
print("\n== search_admissions_info ==")
res = search_admissions_info("application period")
check("returns passages", len(res) > 0, f"{len(res)} passages")
if res:
    check(
        "passages have text, title, source_url, ay, distance",
        all({"text", "title", "source_url", "ay", "distance"} <= set(r) for r in res),
    )
    print("top hit:", res[0]["title"], "|", res[0]["source_url"])
res_topic = search_admissions_info("appeal", topic="deadlines")
check("works with topic", len(res_topic) > 0, f"{len(res_topic)} passages")
check("irrelevant query returns nothing", search_admissions_info("best pizza in Singapore") == [])

# 4. Tool 2: get_key_dates
print("\n== get_key_dates ==")
expected = len(json.loads((Path(__file__).parent / "data" / "key_dates.json").read_text(encoding="utf-8")))
all_dates = get_key_dates()
check("returns every entry when no filter", len(all_dates) == expected, f"{len(all_dates)}/{expected}")
check(
    "entries have all 5 fields",
    all({"event", "date", "applies_to", "source_url", "ay"} <= set(d) for d in all_dates),
)
check(
    "source_url is an official SIT page",
    all(d["source_url"].startswith("https://www.singaporetech.edu.sg/") for d in all_dates),
)
allied = get_key_dates("Allied Health")
check(
    "filter 'Allied Health' finds the Health Sciences exercise",
    any("Health Sciences Admission Exercise" in d["event"] for d in allied),
    f"{len(allied)} entries",
)
check("filter narrows the list", len(allied) < len(all_dates))
check("filter with no match still returns all-applicant entries", len(get_key_dates("zzz")) > 0)

print(f"\n{'All checks passed.' if failures == 0 else str(failures) + ' check(s) failed.'}")
sys.exit(1 if failures else 0)