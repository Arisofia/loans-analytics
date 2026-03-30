import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def test_gemini():
    print("--- Testing Gemini Connection ---")
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("MISSING: GEMINI_API_KEY")
        return False
    try:
        genai.configure(api_key=api_key)
        # Try a simple model list call
        models = genai.list_models()
        print("SUCCESS: Gemini API connected.")
        return True
    except Exception as e:
        print(f"FAILURE: Gemini API connection failed: {e}")
        return False

if __name__ == "__main__":
    test_gemini()
