import urllib.request
import json
import os

keys = []
for p in [r'F:\Nghịch Antigravity\knowledge_agent\.env', r'F:\Nghịch Antigravity\trident\.env', r'F:\Nghịch Antigravity\ai-agent-hub\.env']:
    if os.path.exists(p):
        with open(p, 'r', encoding='utf-8') as f:
            for l in f:
                if 'GEMINI_API_KEY=' in l:
                    k = l.strip().split('GEMINI_API_KEY=')[1].strip('\'" \ufeff')
                    if k: keys.append(k)

for k in set(keys):
    print("Testing key:", k[:8] + "...")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={k}"
    req = urllib.request.Request(
        url,
        headers={'Content-Type': 'application/json'},
        data=json.dumps({
            "contents": [{"parts": [{"text": "Say hi as Steve Jobs in 5 words"}]}]
        }).encode()
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            print("GEMINI SUCCESS:", data['candidates'][0]['content']['parts'][0]['text'].strip())
            with open('.valid_gemini_key', 'w', encoding='utf-8') as out:
                out.write(k)
    except Exception as e:
        print("GEMINI FAILED:", e)
