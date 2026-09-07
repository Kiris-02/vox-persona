import os
import json
import urllib.request
import urllib.error
from dotenv import load_dotenv

load_dotenv()

key = os.environ.get("GEMINI_API_KEY", "").strip()

if not key:
    print("[SKIP] GEMINI_API_KEY not set in environment or local .env file.")
    exit(0)

masked_key = f"{key[:6]}...{key[-4:]}" if len(key) > 10 else "***"
print(f"Testing GEMINI_API_KEY: {masked_key}")

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}"
payload = {
    "contents": [{"parts": [{"text": "Say 'Neural core ready' in 3 words"}]}]
}
req = urllib.request.Request(
    url,
    headers={"Content-Type": "application/json"},
    data=json.dumps(payload).encode("utf-8")
)

try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        reply = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        print(f"GEMINI SUCCESS: {reply}")
except urllib.error.HTTPError as e:
    print(f"GEMINI HTTP ERROR ({e.code}): {e.reason}")
except Exception as e:
    print(f"GEMINI CONNECTION ERROR: {e}")
