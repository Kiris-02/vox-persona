import urllib.request
import json
import os

groq_key = None
env_path = r'F:\Nghịch Antigravity\ai-agent-hub\.env'
with open(env_path, 'r', encoding='utf-8') as f:
    for line in f:
        if 'GROQ_API_KEY=' in line:
            groq_key = line.strip().split('GROQ_API_KEY=')[1].strip('\'" \ufeff')

print("Testing key:", groq_key[:12] if groq_key else "None")

req = urllib.request.Request(
    'https://api.groq.com/openai/v1/chat/completions',
    headers={
        'Authorization': f'Bearer {groq_key}',
        'Content-Type': 'application/json'
    },
    data=json.dumps({
        'model': 'llama-3.3-70b-versatile',
        'messages': [{'role': 'user', 'content': 'Say hi in 5 words as Steve Jobs'}],
        'max_tokens': 30
    }).encode()
)

try:
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        print("GROQ API SUCCESS:")
        print(data['choices'][0]['message']['content'])
except Exception as e:
    print("GROQ API ERROR:", e)
