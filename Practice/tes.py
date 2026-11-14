import os
from dotenv import load_dotenv
from openai import AzureOpenAI
from sklearn.manifold import TSNE
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import distance

load_dotenv()

client = AzureOpenAI(
    api_version="2024-12-01-preview",
    api_key= os.getenv("AZURE_OPENAI_API_KEY"),
    base_url = os.getenv("OPENAI_ENDPOINT_EMB")
    )

# response = client.embeddings.create(
#     model = "text-embedding-3-small",
#     input = "i love you"
# )

# response_dict = response.model_dump()
# # print(response_dict)
# print(response_dict['usage']['total_tokens'])
# print(response_dict['data'][0]['embedding'])


sentences = [ 
    {
        "text": "Artificial intelligence are leading the tech industry in 2026",
        'topic': "Technology"
    },
    {
        "text": "Depression can be a serious problem if we think it carelessly",
        "topic": "Psychology"
    },
    {
        "text": "No amount of time ever bought a second of time",
        "topic": "Time vs Money"
    },
    {
        "text": "Nowadays people depend on AI and social media in their daily activities",
        "topic": "Technology"
    }
]

headline_text = [sentence["text"] for sentence in sentences]

def create_embedding(msg):
    response = client.embeddings.create(
        model = "text-embedding-3-small",
        input = msg
    )
    return response.model_dump()

### How to anaylse and plot where the embeddings are located
response_dict = create_embedding(headline_text)

for i, text in enumerate(sentences):
    text['embedding'] = response_dict['data'][i]['embedding']

topic = [sentence['topic'] for sentence in sentences]
embeddings = [sentence['embedding'] for sentence in sentences]

tsne = TSNE(n_components=2, perplexity=1)
embeddings_2d = tsne.fit_transform(np.array(embeddings))
plt.scatter(embeddings_2d[:, 0], embeddings_2d[:, 1])

for i, category in enumerate(topic):
    plt.annotate(category, (embeddings_2d[i, 0], embeddings_2d[i, 1]))

plt.show()



#### Find the similarity between embeddings 
search_text = "How we should spend our time wisely"
search_embedding = create_embedding(search_text)['data'][0]['embedding']

distances = []
for sentence in sentences:
    dist = distance.cosine(search_embedding, sentence['embedding'])
    distances.append(dist)

min_dist_ind = np.argmin(distances)
print(sentences[min_dist_ind]['topic'])

