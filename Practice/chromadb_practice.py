import chromadb
import os
from dotenv import load_dotenv
from openai import AzureOpenAI
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
import csv

load_dotenv()

azure_ef = OpenAIEmbeddingFunction(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_base=os.getenv("OPENAI_ENDPOINT_EMB"),
    api_type="azure",
    api_version="2024-12-01-preview",
    model_name="text-embedding-3-small",
    deployment_id="text-embedding-3-small"
)


client = chromadb.PersistentClient()

collection = client.get_or_create_collection(
    name = "vector-database",
    embedding_function = azure_ef
)

# ids = []
# documents = []

# with open('netflix_titles.csv') as csvfile:
#   reader = csv.DictReader(csvfile)
#   for i, row in enumerate(reader):
#     ids.append(row['show_id'])
#     text = f"Title: {row['title']} ({row['type']})\nDescription: {row['description']}\nCategories: {row['listed_in']}"
#     documents.append(text)

# collection.add(ids=ids, documents=documents)

# print(client.list_collections())
# print(f"No. of documents: {collection.count()}")
# print(f"First ten documents: {collection.peek()}")

#add collection
# result = collection.add(ids=["s5"], documents=["Hello"])


#get collection
result = collection.get(ids=["s1"])['documents']

print(result)

# result = collection.query(
#     query_texts = ["Movies where people kiss a lot"],
#     n_results=2
# )

# collection.upsert(
#     ids = ["s5"],
#     documents = ["Title: Interstellar (Movie)\nDescription: A journey through space to save humanity.\nCategories: Sci-Fi", ]
# )
# print(collection.peek())

# #delete
# collection.delete(
#     id = ["s1", "s2"]
# )

# #reset/delete_all
# client.reset()




#Multiple Queries 
reference_texts = ["children's story about a car", "lions"]

# Query two results using reference_texts
result = collection.query(
  query_texts=reference_texts,
  n_results=2,
  # Filter for titles with a G rating released before 2019
  where={
    "$and": [
        {"rating": 
        	{"$eq": "G"}
        },
        {"release_year": 
         	{"$lt": 2019}
        }
    ]
  }
)

print(result['documents'])