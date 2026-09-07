"""
VOX IMPERIUM — GPT-SoVITS Bridge Server
Cầu nối API kết nối giao diện VOX Web với mô hình GPT-SoVITS V2 chạy cục bộ.
"""

import os
import json
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = 9885
GPT_SOVITS_URL = os.getenv("SOVITS_URL", "http://127.0.0.1:9880/tts")

# Reference voice profiles for each character
VOICE_PROFILES = {
    "jobs": {
        "ref_audio_path": "voices/steve_jobs_ref.wav",
        "prompt_text": "Stay hungry, stay foolish.",
        "prompt_lang": "en",
        "default_lang": "vi"
    },
    "trump": {
        "ref_audio_path": "voices/trump_ref.wav",
        "prompt_text": "We are going to make our country greater than ever before.",
        "prompt_lang": "en",
        "default_lang": "vi"
    },
    "xijinping": {
        "ref_audio_path": "voices/xijinping_ref.wav",
        "prompt_text": "Chiến lược trường kỳ vì sự phục hưng vĩ đại.",
        "prompt_lang": "zh",
        "default_lang": "vi"
    },
    "tesla": {
        "ref_audio_path": "voices/tesla_ref.wav",
        "prompt_text": "The present is theirs, the future is mine.",
        "prompt_lang": "en",
        "default_lang": "vi"
    },
    "zuck": {
        "ref_audio_path": "voices/zuck_ref.wav",
        "prompt_text": "Move fast and build open source infrastructure.",
        "prompt_lang": "en",
        "default_lang": "vi"
    },
    "musk": {
        "ref_audio_path": "voices/musk_ref.wav",
        "prompt_text": "First principles thinking is the only way to invent the future.",
        "prompt_lang": "en",
        "default_lang": "vi"
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
                text = data.get('text', '')
                lang = data.get('lang', 'vi')

                profile = VOICE_PROFILES.get(persona, VOICE_PROFILES['jobs'])
                
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
                    "tip": "Hãy đảm bảo GPT-SoVITS repo đang chạy lệnh: python api_v2.py -a 127.0.0.1 -p 9880"
                }
                self.wfile.write(json.dumps(err_resp).encode())

def run():
    print(f"🔱 VOX GPT-SoVITS Bridge khởi động trên cổng {PORT}...")
    print(f"🔗 Kết nối đích tới GPT-SoVITS tại: {GPT_SOVITS_URL}")
    server = HTTPServer(('0.0.0.0', PORT), SovitsBridgeHandler)
    server.serve_forever()

if __name__ == '__main__':
    run()
