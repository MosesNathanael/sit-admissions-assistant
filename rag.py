from llm import ask_llm
from vectordb import collection


def ask_query(query, n):
    result = collection.query(
        query_texts = query,
        n_results = n
    )
    documents = result['documents']
    metadatas = result['metadatas']
    distances = result['distances']

    return documents, metadatas, distances

documents, metadata, distances = ask_query("when the admission open", 2)
print(documents)
print(metadata)
print(distances)
