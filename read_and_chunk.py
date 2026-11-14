import re
from pathlib import Path
import chromadb

RAW = Path("data/raw_priority1_headers")
DB_PATH = "chroma_db"
COLLECTION = "sit_admissions"
CHUNK_SIZE = 1500
OVERLAP = 200

def read_file(path):
    text = path.read_text(encoding="utf-8")
    _, header, body = text.split("---", 2)
    meta = {}
    for line in header.strip().splitlines():
        key, value = line.split(": ", 1)
        meta[key] = value
    return meta, body.strip()

meta, body = read_file(Path("data/raw_priority1_headers/admissions_admissions-faqs.md"))
# print(meta)
# print(len(body))


def chunk_text(text, size=CHUNK_SIZE, overlap=OVERLAP):
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start:start + size])
        if start + size >= len(text):
            break
        start += size - overlap
    return chunks

# print(chunk_text("abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMN", size=20, overlap=5))



