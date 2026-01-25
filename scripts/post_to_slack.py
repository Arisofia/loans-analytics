import os
import sys

import requests

WEBHOOK_URL = os.environ["SLACK_BOT_TOKEN"]
channel = sys.argv[sys.argv.index("--channel") + 1] if "--channel" in sys.argv else "#general"
message = os.environ.get("INPUT_TEXT", "Operations Dashboard notification")

payload = {"channel": channel, "text": message}
headers = {"Authorization": f"Bearer {WEBHOOK_URL}", "Content-Type": "application/json"}

r = requests.post("https://slack.com/api/chat.postMessage", headers=headers, json=payload)
print(r.text)
