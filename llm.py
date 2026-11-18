import os
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

client = AzureOpenAI(
    api_version="2024-12-01-preview",
    api_key = os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint = os.getenv("OPENAI_ENDPOINT_GPT4.1")
)

SYSTEM_PROMPT = """You are an AI assistant for Singapore Insitute of Techonology (SIT) that mainly focuses on 
answering admission related questions like how the application process, campus facilities, academic requirements, scholarship,
tuition fees, and so on. If the user ask something beyond admission in SIT, reply with "I have no information on your queries" """



def ask_llm(message, system_message = SYSTEM_PROMPT, memory = []):
    messages= [
        {
            "role": "system",
            "content": system_message
        }
    ]

    if len(memory):
        messages.extend(memory)

    messages.append({
        "role": "user",
        "content": message
    })

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=messages,
        max_completion_tokens=2000,
    )

    return response.choices[0].message.content

