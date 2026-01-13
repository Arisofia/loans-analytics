from google import genai
import os
import sys

# 1. Setup Client
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    sys.exit("❌ Error: GEMINI_API_KEY environment variable not set.")

client = genai.Client(api_key=api_key)

# 2. Get Prompt
prompt = " ".join(sys.argv[1:])
if not prompt:
    prompt = "Hello! Tell me a fun fact about software engineering."

# 3. Generate Content
# We use 'gemini-2.5-flash' as confirmed by your check_models.py
model_id = "gemini-2.5-flash"

print(f"🤖 Asking Gemini ({model_id})...\n")

try:
    response = client.models.generate_content(
        model=model_id,
        contents=prompt
    )
    print(response.text)

except Exception as e:
    print(f"❌ Error: {e}")
