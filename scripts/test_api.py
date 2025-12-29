import os
from openai import OpenAI
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Tries to load from local .env and secret .env
load_dotenv(os.path.join(BASE_DIR, ".env")) 
load_dotenv("/Users/jasonjia/Documents/industry_policy/secret/.env")

print(f"Checking for DEEPSEEK_API_KEY...")
API_KEY = os.getenv("DEEPSEEK_API_KEY")
print(f"DeepSeek API Key present: {bool(API_KEY)}")

if not API_KEY:
    print("Error: DEEPSEEK_API_KEY is missing.")
    exit(1)

client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")

try:
    print("Sending request to DeepSeek...")
    response = client.chat.completions.create(
        model="deepseek-reasoner",
        messages=[{"role": "user", "content": "Hello, say hi!"}],
        temperature=0 # Setting to 0 as requested, though 'reasoner' might ignore it or require specific values, usually 0 is fine.
    )
    print("Success:")
    print(response.choices[0].message.content)
except Exception as e:
    print(f"Error: {e}")
