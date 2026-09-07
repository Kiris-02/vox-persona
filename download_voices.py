import urllib.request
import urllib.parse
import json
import ssl
import os
import time

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

os.makedirs('assets/audio', exist_ok=True)

files_map = {
    'trump_speech': 'File:Audio_deepfake_of_Donald_Trump.mp3',
    'xijinping_speech': "File:Xi's_voice_2021.ogg",
    'musk_speech': 'File:Elon_Musk_on_Narendra_Modi.wav'
}

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

for key, title in files_map.items():
    time.sleep(3)
    query_params = urllib.parse.urlencode({
        'action': 'query',
        'titles': title,
        'prop': 'imageinfo',
        'iiprop': 'url',
        'format': 'json'
    })
    api_url = f'https://commons.wikimedia.org/w/api.php?{query_params}'
    try:
        req = urllib.request.Request(api_url, headers=headers)
        with urllib.request.urlopen(req, context=ctx) as r:
            data = json.loads(r.read().decode('utf-8'))
            pages = data.get('query', {}).get('pages', {})
            for pid, page in pages.items():
                if 'imageinfo' in page and page['imageinfo']:
                    raw_url = page['imageinfo'][0]['url']
                    clean_url = raw_url.split('?')[0]
                    ext = clean_url.split('.')[-1].lower()
                    dest_file = f'assets/audio/{key}.{ext}'
                    print(f'Fetching {key} from {clean_url} -> {dest_file}')
                    dl_req = urllib.request.Request(raw_url, headers=headers)
                    with urllib.request.urlopen(dl_req, context=ctx) as audio_resp:
                        with open(dest_file, 'wb') as out_f:
                            out_f.write(audio_resp.read())
                    print(f'SUCCESS: {dest_file} ({os.path.getsize(dest_file)} bytes)')
    except Exception as e:
        print(f'Failed {key}: {e}')
