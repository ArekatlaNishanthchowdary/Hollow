import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

try:
    print("Available Groq Models:")
    models = client.models.list()
    for m in models.data:
        print(f"- {m.id}")
except Exception as e:
    print(f"Error: {e}")
