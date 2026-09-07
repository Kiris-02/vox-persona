"""
VOX IMPERIUM — GPT-SoVITS Bridge Server
API bridge connecting VOX Web Studio with local GPT-SoVITS V2 model.
Each persona speaks in their authentic mother tongue (Xi Jinping in Chinese, others in English).
"""

import os
import json
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = 9885
GPT_SOVITS_URL = os.getenv("SOVITS_URL", "http://127.0.0.1:9880/tts")

# Reference voice profiles for each character with their authentic native languages
VOICE_PROFILES = {
    "jobs": {
        "ref_audio_path": "voices/steve_jobs_ref.wav",
        "prompt_text": "Stay hungry, stay foolish.",
        "prompt_lang": "en",
        "default_lang": "en"
    },
    "trump": {
        "ref_audio_path": "voices/trump_ref.wav",
        "prompt_text": "We are going to make our country greater than ever before.",
        "prompt_lang": "en",
        "default_lang": "en"
    },
    "xijinping": {
        "ref_audio_path": "voices/xijinping_ref.wav",
        "prompt_text": "坚定不移推进中华民族伟大复兴历史进程。",
        "prompt_lang": "zh",
        "default_lang": "zh"
    },
    "tesla": {
        "ref_audio_path": "voices/tesla_ref.wav",
        "prompt_text": "The present is theirs, the future for which I worked is mine.",
        "prompt_lang": "en",
        "default_lang": "en"
    },
    "zuck": {
        "ref_audio_path": "voices/zuck_ref.wav",
        "prompt_text": "Move fast and build open source infrastructure for everyone.",
        "prompt_lang": "en",
        "default_lang": "en"
    },
    "musk": {
        "ref_audio_path": "voices/musk_ref.wav",
        "prompt_text": "First principles physics is the only framework to invent the future.",
        "prompt_lang": "en",
        "default_lang": "en"
    }
}

class SovitsBridgeHandler(BaseHTTPRequestHandler):
    def _set_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def do_GET(self):
        if self.path == '/status':
            self.send_response(200)
            self._set_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {
                "status": "online",
                "bridge_port": PORT,
                "target_sovits": GPT_SOVITS_URL,
                "supported_personas": list(VOICE_PROFILES.keys())
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/synthesize':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            try:
                data = json.loads(body)
                persona = data.get('persona', 'jobs')
                profile = VOICE_PROFILES.get(persona, VOICE_PROFILES['jobs'])
                
                text = data.get('text', '')
                lang = data.get('lang', profile.get('default_lang', 'en'))

                payload = {
                    "text": text,
                    "text_lang": lang,
                    "ref_audio_path": profile["ref_audio_path"],
                    "prompt_text": profile["prompt_text"],
                    "prompt_lang": profile["prompt_lang"],
                    "speed_factor": 1.0
                }

                # Forward to local GPT-SoVITS
                req = urllib.request.Request(
                    GPT_SOVITS_URL,
                    data=json.dumps(payload).encode('utf-8'),
                    headers={'Content-Type': 'application/json'}
                )

                with urllib.request.urlopen(req, timeout=15) as resp:
                    audio_data = resp.read()
                    self.send_response(200)
                    self._set_cors_headers()
                    self.send_header('Content-Type', 'audio/wav')
                    self.end_headers()
                    self.wfile.write(audio_data)

            except Exception as e:
                self.send_response(502)
                self._set_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                err_resp = {
                    "error": "GPT-SoVITS Server Not Reachable",
                    "details": str(e),
                    "tip": "Ensure GPT-SoVITS is running: python api_v2.py -a 127.0.0.1 -p 9880"
                }
                self.wfile.write(json.dumps(err_resp).encode())

def run():
    print(f"🔱 VOX GPT-SoVITS Bridge running on port {PORT}...")
    print(f"🔗 Target GPT-SoVITS at: {GPT_SOVITS_URL}")
    server = HTTPServer(('0.0.0.0', PORT), SovitsBridgeHandler)
    server.serve_forever()

if __name__ == '__main__':
    run()
