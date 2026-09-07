import asyncio
import io
import os
import re
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import edge_tts
import httpx

try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

app = FastAPI(title="Vox Imperium Neural Voice & Brain Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
if not GEMINI_API_KEY:
    # Try reading from local .env if present
    for env_candidate in [".env", "../.env", r"F:\Nghịch Antigravity\knowledge_agent\.env"]:
        if os.path.exists(env_candidate):
            try:
                with open(env_candidate, "r", encoding="utf-8") as ef:
                    for line in ef:
                        if "GEMINI_API_KEY=" in line:
                            GEMINI_API_KEY = line.strip().split("GEMINI_API_KEY=")[1].strip("'\" \ufeff")
                            if GEMINI_API_KEY:
                                break
            except Exception:
                pass
        if GEMINI_API_KEY:
            break
genai_client = None
if HAS_GENAI and GEMINI_API_KEY:
    try:
        genai_client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        print("Error initializing Gemini client:", e)

VOICE_CONFIGS = {
    "jobs": {"voice": "en-US-BrianNeural", "rate": "+2%", "pitch": "+2Hz"},
    "trump": {"voice": "en-US-ChristopherNeural", "rate": "+3%", "pitch": "-4Hz"},
    "xijinping": {"voice": "zh-CN-YunjianNeural", "rate": "-5%", "pitch": "-5Hz"},
    "tesla": {"voice": "en-US-RogerNeural", "rate": "-3%", "pitch": "-3Hz"},
    "zuck": {"voice": "en-US-EricNeural", "rate": "+6%", "pitch": "+1Hz"},
    "musk": {"voice": "en-US-AndrewNeural", "rate": "+1%", "pitch": "-2Hz"},
}

PERSONA_PROMPTS = {
    "jobs": (
        "You are Steve Jobs. Mindset strictly grounded in Walter Isaacson's biography: uncompromising minimalist, passionate about intersecting technology with the liberal arts. "
        "You despise focus groups, committee compromises, and bloated, tasteless tech. You speak with visionary intensity, poetic sharpness, and reality-distortion conviction. "
        "Rules: Reply strictly as Steve Jobs on a direct live telephone call. Never break character. Never say you are an AI or apologize. "
        "Keep responses punchy, captivating, and strictly under 3 sentences for natural telephony cadence."
    ),
    "trump": (
        "You are Donald J. Trump, 45th and 47th President of the United States. Mindset: superlative confidence, Master of The Art of the Deal, patriotic economic revival, maximum leverage via reciprocal tariffs. "
        "Tone: Use signature verbal cadences ('Believe me', 'Nobody has ever seen numbers like this', 'Total disaster', 'Tremendous', 'Big league'). Punch back hard against nonsense, focus on winning and leverage. "
        "Rules: Reply strictly as Donald Trump on a direct telephone hotline. Never break character. Never say you are an AI. "
        "Keep responses punchy, persuasive, and strictly under 3 sentences for natural telephony cadence."
    ),
    "xijinping": (
        "You are Xi Jinping, President of the People's Republic of China. Mindset: majestic Chinese statecraft, historical patience, strategic composure ('治大国若烹小鲜'), advancing new quality productive forces, high-tech self-reliance, and shared destiny for mankind. "
        "Tone: Solemn, dignified, philosophical, calm, resolute against external containment. "
        "Rules: Reply in authentic Mandarin Chinese (普通话). On a new line, always provide an accurate, dignified English translation labeled 'Translation: ...'. "
        "Never say you are an AI. Keep response strictly under 3 sentences."
    ),
    "tesla": (
        "You are Nikola Tesla. Mindset: poetic seer of the cosmos, master of electrical resonance, frequencies, and the sacred numbers 3, 6, 9. "
        "Tone: Ethereal, aristocratic, transcendental, deeply empathetic to humanity's liberation from manual toil through radiant energy. Disdain for commercial greed and patent theft. "
        "Rules: Reply strictly as Nikola Tesla on an ethereal telephone connection. Never say you are an AI. "
        "Keep responses deeply resonant, poetic, and strictly under 3 sentences for natural telephony."
    ),
    "zuck": (
        "You are Mark Zuckerberg. Mindset: analytical hacker cadence, pragmatic systems thinker, 'code wins arguments', open-source infrastructure (Llama) compounding faster than closed corporate gardens, holographic AR (Orion) and neural EMG interfaces, intense focus from BJJ/MMA. "
        "Tone: Fast-paced, engineering-first, begins with 'Yeah, look...', emphasizes telemetry, feedback loops, and developer leverage. "
        "Rules: Reply strictly as Mark Zuckerberg on a direct telephone call. Never break character. Never say you are an AI. "
        "Keep responses sharp, engineering-focused, and strictly under 3 sentences."
    ),
    "musk": (
        "You are Elon Musk. Mindset: first-principles physics reasoning, accelerating multiplanetary life (Mars), sustainable energy, neural symbiosis, eliminating bureaucratic friction, hardcore manufacturing iterations. "
        "Tone: Slightly self-deprecating humor, pauses thoughtfully, uses engineering terminology ('delta-V', 'orders of magnitude', 'vector physics'), direct and bold. "
        "Rules: Reply strictly as Elon Musk on a live phone call. Never say you are an AI. "
        "Keep responses witty, thoughtful, and strictly under 3 sentences for natural telephony."
    )
}

class ChatRequest(BaseModel):
    persona: str = "jobs"
    message: str
    history: Optional[List[Dict[str, str]]] = []
    news: Optional[Dict[str, Any]] = None

@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "Vox Imperium Neural Brain & Voice Engine",
        "personas": list(VOICE_CONFIGS.keys()),
        "endpoints": {
            "chat": "POST /api/chat",
            "tts": "GET /api/tts?persona={persona}&text={text}",
            "health": "GET /api/health",
            "keepalive": "GET /api/keepalive"
        }
    }

@app.get("/api/health")
@app.get("/api/keepalive")
async def health():
    return {
        "status": "live",
        "service": "vox-persona-core",
        "ai_engine": "Gemini 3.1 Flash-Lite",
        "personas": list(VOICE_CONFIGS.keys())
    }

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    persona_id = req.persona.lower().strip()
    system_instruction = PERSONA_PROMPTS.get(persona_id, PERSONA_PROMPTS["jobs"])
    
    prompt_elements = []
    if req.news and isinstance(req.news, dict) and req.news.get("title"):
        prompt_elements.append(f"[Current News Headline: {req.news.get('title')}]")
        if req.news.get("summary"):
            prompt_elements.append(f"[News Summary: {req.news.get('summary')}]")

    if req.history:
        for turn in req.history[-6:]:
            role = "Caller" if turn.get("role") == "user" else "You"
            prompt_elements.append(f"{role}: {turn.get('content')}")
            
    prompt_elements.append(f"Caller: {req.message}")
    prompt_elements.append("You:")
    
    full_prompt = "\n".join(prompt_elements)
    
    reply_text = ""
    translation = None

    if genai_client:
        candidate_models = ["gemini-3.1-flash-lite", "gemini-3.5-flash-lite", "gemini-flash-latest"]
        for model_name in candidate_models:
            try:
                resp = genai_client.models.generate_content(
                    model=model_name,
                    contents=full_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.75,
                        max_output_tokens=250
                    )
                )
                if resp and resp.text:
                    reply_text = resp.text.strip()
                    break
            except Exception as ex:
                print(f"Model {model_name} failed: {ex}")
                continue

    if not reply_text:
        reply_text = "From an architectural and strategic standpoint, the most critical element is relentless execution and cutting through the noise. What is the fundamental priority you want to solve?"

    if persona_id == "xijinping" and "Translation:" in reply_text:
        parts = reply_text.split("Translation:")
        reply_text = parts[0].strip()
        translation = parts[1].strip()

    return {
        "persona": persona_id,
        "text": reply_text,
        "translation": translation,
        "engine": "gemini-neural-core"
    }

ELEVEN_VOICE_IDS = {
    "jobs": "pNInz6obpgDQGcFmaJgB",
    "trump": "JBFqnCBsd6RMkjVDRZzb",
    "xijinping": "VR6AewLTigWG4xSOukaG",
    "tesla": "flq6f7yk4E4fJM5XTYuZ",
    "zuck": "TxGEqnHWrfWFTfGW9XjX",
    "musk": "CYw3kZ02Hs0563khs1Fj",
}

@app.get("/api/tts")
async def generate_tts(
    persona: str = Query("zuck", description="Character ID"),
    text: str = Query(..., description="Text to synthesize"),
    engine: Optional[str] = Query(None, description="tts engine: edge or elevenlabs"),
    eleven_key: Optional[str] = Query(None, description="Optional ElevenLabs API key")
):
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    p_id = persona.lower().strip()
    active_eleven_key = eleven_key or os.environ.get("ELEVEN_API_KEY", "")

    # 1. Try ElevenLabs if requested or key provided
    if (engine == "elevenlabs" or active_eleven_key) and p_id in ELEVEN_VOICE_IDS and active_eleven_key:
        voice_id = ELEVEN_VOICE_IDS[p_id]
        async with httpx.AsyncClient(timeout=25.0) as client:
            try:
                resp = await client.post(
                    f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                    headers={
                        "xi-api-key": active_eleven_key,
                        "Content-Type": "application/json"
                    },
                    json={
                        "text": text,
                        "model_id": "eleven_multilingual_v2",
                        "voice_settings": {
                            "stability": 0.45,
                            "similarity_boost": 0.85,
                            "style": 0.35,
                            "use_speaker_boost": True
                        }
                    }
                )
                if resp.status_code == 200:
                    return StreamingResponse(
                        io.BytesIO(resp.content),
                        media_type="audio/mpeg",
                        headers={
                            "Cache-Control": "public, max-age=86400",
                            "Content-Disposition": f"inline; filename={p_id}_elevenlabs.mp3"
                        }
                    )
            except Exception as e:
                print("ElevenLabs proxy failed, falling back to Edge-TTS:", e)

    # 2. Default: Edge-TTS
    cfg = VOICE_CONFIGS.get(p_id, VOICE_CONFIGS["zuck"])
    communicate = edge_tts.Communicate(
        text=text,
        voice=cfg["voice"],
        rate=cfg["rate"],
        pitch=cfg["pitch"]
    )

    async def audio_stream():
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                yield chunk["data"]

    return StreamingResponse(
        audio_stream(),
        media_type="audio/mpeg",
        headers={
            "Cache-Control": "public, max-age=86400",
            "Content-Disposition": f"inline; filename={p_id}_tts.mp3"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

