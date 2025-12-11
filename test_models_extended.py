import os
import google.generativeai as genai
from dotenv import load_dotenv
import time

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

models_to_test = [
    'gemini-1.5-flash-001',
    'gemini-1.5-flash-002',
    'gemini-2.0-flash',
    'gemini-2.0-flash-001'
]

print("Starting Extended Model Test...")
for m_name in models_to_test:
    print(f"\n--- Testing {m_name} ---")
    try:
        model = genai.GenerativeModel(m_name)
        response = model.generate_content("Hi")
        print(f"SUCCESS: {m_name} responded: {response.text}")
    except Exception as e:
        print(f"FAIL: {m_name} error: {e}")
    time.sleep(1)
