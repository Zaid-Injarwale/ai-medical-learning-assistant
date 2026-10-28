import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

print("API key loaded:", bool(api_key))

client = genai.Client(api_key=api_key)

print("Testing Gemini...")

response = client.models.generate_content(
    model="gemini-3.5-flash-lite",
    contents="Say only: Gemini is working."
)

print("SUCCESS!")
print(response.text)