import chromadb
from pathlib import Path
from read_and_chunk import *
import os
from dotenv import load_dotenv
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

load_dotenv()

azure_model = OpenAIEmbeddingFunction(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_base=os.getenv("OPENAI_ENDPOINT_EMB"),
    api_type="azure",
    api_version="2024-12-01-preview",
    model_name="text-embedding-3-small",
    deployment_id="text-embedding-3-small"
)

client = chromadb.PersistentClient(path=DB_PATH)

try:
    client.delete_collection(COLLECTION)
except Exception:
    pass

collection = client.create_collection(
    name = COLLECTION,
    embedding_function = azure_model
)

ids, documents, metadatas = [], [], []
files = [Path("data/raw_priority1_headers/admissions_admissions-faqs.md")]

for path in files:
    meta, body = read_file(path)
    for i, chunk in enumerate(chunk_text(body)):
        ids.append(f"{path.stem}-{i}")
        documents.append(f"{meta.get('title', path.stem)}\n\n{chunk}")
        metadatas.append({**meta, "chunk": i})

collection.add(ids=ids, documents=documents, metadatas=metadatas)
# print(len(files), "documents,", len(documents), "chunks")