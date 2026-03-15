import os
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("OPENAI_API_KEY")
print(f"Key: '{key}'")
print(f"Length: {len(key)}")
print(f"Bytes: {key.encode('utf-8')}")
