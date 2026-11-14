from vectordb import collection
from llm import ask_llm

def ask_query(query, n):
    result = collection.query(
        query_texts = query,
        n_results = n
    )
    documents = result['documents']
    metadatas = result['metadatas']
    distances = result['distances']

    chunks = []

    for doc, meta, dis in zip(documents[0], metadatas[0], distances[0]):
        chunks.append({
            "text": doc,
            "title": meta["title"],
            "url": meta["source_url"],
            "ay": meta["ay_or_updated"],
            "distance": dis
        })

    return chunks

def create_text(chunks):
    result = []
    for i, c in enumerate(chunks):
        result.append(f"({i}) -  ({c['title'], c['ay']})\n{c['text']}")

    return "\n\n".join(result)


RAG_PROMPT = """You are the SIT Admissions Assistant for prospective applicants.
Rules:
1. Answer ONLY using the context provided. Do not use outside knowledge.
2. Cite the sources you use with their numbers, like [1] or [2].
3. If the context does not contain the answer, say "I don't have that information." and suggest contacting the SIT admissions team.
4. Never say or imply that someone will be admitted or is eligible. Explain the published requirements instead.
5. Remind the user to verify dates and fees on the official SIT website, because they can change.
6. Keep answers short and clear."""

def rag(prompt, assistant):
    chunks = ask_query(prompt, 3)
    best = chunks[0]["distance"]
    if best > 0.5:
        response = ask_llm(prompt, memory = assistant)
        return {
            "answer": response,
            "sources": [],
            "best_distance": best,
        }

    message = f"Context:\n{create_text(chunks)}\n\nQuestion: {prompt}"
    response = ask_llm(message, RAG_PROMPT, assistant)

    sources = []
    for i, c in enumerate(chunks, start=1):
        sources.append({"n": i, "title": c["title"], "url": c["url"], "ay": c["ay"]})
    return {"answer": response, "sources": sources, "best_distance": best}



# response = rag("What is my age?")
# print(response["answer"])