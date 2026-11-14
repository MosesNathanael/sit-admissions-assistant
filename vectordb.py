import chromadb
from pathlib import Path
from read_and_chunk import *

client = chromadb.PersistentClient(path=DB_PATH)

try:
    client.delete_collection(COLLECTION)
except Exception:
    pass
collection = client.create_collection(COLLECTION)

ids, documents, metadatas = [], [], []
files = [Path("data/raw_priority1_headers/admissions_admissions-faqs.md")]

for path in files:
    meta, body = read_file(path)
    for i, chunk in enumerate(chunk_text(body)):
        ids.append(f"{path.stem}-{i}")
        documents.append(f"{meta.get('title', path.stem)}\n\n{chunk}")
        metadatas.append({**meta, "chunk": i})

collection.add(ids=ids, documents=documents, metadatas=metadatas)
print(len(files), "documents,", len(documents), "chunks")