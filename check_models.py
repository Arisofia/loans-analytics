import google.generativeai as genai
import os

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("❌ API Key not found")
    exit(1)

genai.configure(api_key=api_key)

print(f"🔍 Checking available models for your API key...")
try:
    found = False
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"   ✅ Available: {m.name}")
            found = True
    if not found:
        print("   ⚠️  No models found. Check if the 'Google Generative AI API' is enabled in your console.")
except Exception as e:
    print(f"   ❌ Error: {e}")
