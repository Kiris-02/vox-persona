import os
import json
import urllib.request
import urllib.error
from dotenv import load_dotenv

load_dotenv()

groq_key = os.environ.get("GROQ_API_KEY", "").strip()

if not groq_key:
    print("[SKIP] GROQ_API_KEY not set in environment or local .env file.")
    exit(0)

masked_key = f"{groq_key[:6]}...{groq_key[-4:]}" if len(groq_key) > 10 else "***"
print(f"Testing GROQ_API_KEY: {masked_key}")

url = "https://api.groq.com/openai/v1/chat/completions"
payload = {
    "model": "qwen/qwen3.8-27b",
    "messages": [{"role": "user", "content": "Say 'LPU reflex online' in 3 words"}],
    "max_tokens": 30
}
req = urllib.request.Request(
    url,
    headers={
        "Authorization": f"Bearer {groq_key}",
        "Content-Type": "application/json",
        "User-Agent": "VoxImperium/2.0"
    },
    data=json.dumps(payload).encode("utf-8")
)

try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        reply = data["choices"][0]["message"]["content"].strip()
        print(f"GROQ API SUCCESS: {reply}")
except urllib.error.HTTPError as e:
    print(f"GROQ HTTP ERROR ({e.code}): {e.reason}")
except Exception as e:
    print(f"GROQ CONNECTION ERROR: {e}")
