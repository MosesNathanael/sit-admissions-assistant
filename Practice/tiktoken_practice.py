import tiktoken

enc = tiktoken.encoding_for_model('gpt-4o')

text = "Hello, how many tokens is this sentence?"
tokens = enc.encode(text)

print(f"Token count: {len(tokens)}")
print(f"Token IDs: {tokens}")