from rag import rag

memory = []

while True:
    user = input("Input: ")
    if user == "exit" or user == "Exit":
        break
    response = rag(user, memory)["answer"]
    memory.extend([
        {
            "role": "user",
            "content": user,
        },
        {
            "role": "assistant",
            "content": response
        }
    ])
    print(f"AI: {response}")

    
