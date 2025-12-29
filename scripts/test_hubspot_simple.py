import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("Testing API Keys from .env")
print("=" * 60)

keys = {
    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
    "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
    "HUBSPOT_API_KEY": os.getenv("HUBSPOT_API_KEY"),
}

for name, value in keys.items():
    if value:
        masked = value[:10] + "..." + value[-10:] if len(value) > 20 else value
        print(f"✅ {name}: {masked}")
    else:
        print(f"❌ {name}: NOT FOUND")

print("=" * 60)
