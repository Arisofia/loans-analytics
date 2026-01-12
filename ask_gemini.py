import google.generativeai as genai
import os
import sys

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    sys.exit("❌ Error: GEMINI_API_KEY not set.")

genai.configure(api_key=api_key)

# UPDATED: Using a model confirmed to be in your list
model_name = 'gemini-2.5-flash' 

model = genai.GenerativeModel(model_name)

prompt = " ".join(sys.argv[1:]) or "Hello! Tell me a one-sentence fun fact."
print(f"🤖 Asking Gemini ({model_name}): '{prompt}'...\n")

try:
    response = model.generate_content(prompt)
    print(response.text)
except Exception as e:
    print(f"❌ Error: {e}")
    print("\n💡 Tip: Run 'python3 check_models.py' to see which models your key can access.")
