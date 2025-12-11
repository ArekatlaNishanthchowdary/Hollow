import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

try:
    print("Testing gemini-1.5-flash...")
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("Hello")
    print(f"Success with gemini-1.5-flash: {response.text}")
except Exception as e:
    print(f"Failed gemini-1.5-flash: {e}")

try:
    print("\nTesting gemini-flash-latest...")
    model = genai.GenerativeModel('gemini-flash-latest')
    response = model.generate_content("Hello")
    print(f"Success with gemini-flash-latest: {response.text}")
except Exception as e:
    print(f"Failed gemini-flash-latest: {e}")
