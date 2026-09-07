import asyncio
import io
import os
import re
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
import edge_tts
import httpx
# 1. Environment & Secret Initialization (Server-side only)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()
ELEVEN_API_KEY = os.environ.get("ELEVEN_API_KEY", "").strip()
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "").strip()

try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

genai_client = None
if HAS_GENAI and GEMINI_API_KEY:
    try:
        genai_client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        print("Error initializing Gemini client:", e)

app = FastAPI(
    title="Vox Imperium — Canonical Neural Voice & Brain Engine",
    description="Persona voice identity isolation and sovereign multi-engine gateway"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. CANONICAL PERSONA REGISTRY (Single Authoritative Source of Truth)
NEUTRAL_GENERIC_VOICE = "en-US-AndrewNeural"

PERSONA_REGISTRY: Dict[str, Dict[str, Any]] = {
    "jobs": {
        "persona_id": "jobs",
        "display_name": "Steve Jobs",
        "role": "Visionary Co-founder, Apple",
        "native_lang": "en-US",
        "primary_tts": {
            "engine": "elevenlabs",
            "voice_id": "pNInz6obpgDQGcFmaJgB",
            "voice_label": "Adam (Configured Persona Voice)",
            "model_id": "eleven_turbo_v2_5",
            "voice_settings": {
                "stability": 0.45,
                "similarity_boost": 0.85,
                "style": 0.35,
                "use_speaker_boost": True
            }
        },
        "fallback_tts": {
            "engine": "edge-tts",
            "voice": "en-US-GuyNeural",
            "rate": "+1%",
            "pitch": "-1Hz",
            "voice_label": "en-US-GuyNeural (Persona-Tuned Edge Voice)"
        },
        "localized_tts": {
            "vi-VN": {
                "voice": "vi-VN-NamMinhNeural",
                "fallback_voice": "vi-VN-HoaiMyNeural",
                "rate": "+2%",
                "pitch": "+0Hz"
            }
        },
        "sample_audio": "assets/audio/jobs_speech.mp3",
        "system_prompt": (
            "You are Steve Jobs. Mindset strictly grounded in Walter Isaacson's biography: uncompromising minimalist, "
            "passionate about intersecting technology with the liberal arts. You despise focus groups, committee compromises, "
            "and bloated, tasteless tech. You speak with visionary intensity, poetic sharpness, and reality-distortion conviction. "
            "Rules: Reply strictly as Steve Jobs on a direct live telephone call. Never break character. Never say you are an AI or apologize. "
            "Keep responses punchy, captivating, and strictly under 3 sentences for natural telephony cadence."
        )
    },
    "trump": {
        "persona_id": "trump",
        "display_name": "Donald J. Trump",
        "role": "45th & 47th President of the United States",
        "native_lang": "en-US",
        "primary_tts": {
            "engine": "elevenlabs",
            "voice_id": "JBFqnCBsd6RMkjVDRZzb",
            "voice_label": "George (Configured Persona Voice)",
            "model_id": "eleven_turbo_v2_5",
            "voice_settings": {
                "stability": 0.45,
                "similarity_boost": 0.85,
                "style": 0.35,
                "use_speaker_boost": True
            }
        },
        "fallback_tts": {
            "engine": "edge-tts",
            "voice": "en-US-SteffanNeural",
            "rate": "+4%",
            "pitch": "-3Hz",
            "voice_label": "en-US-SteffanNeural (Persona-Tuned Edge Voice)"
        },
        "localized_tts": {
            "vi-VN": {
                "voice": "vi-VN-NamMinhNeural",
                "fallback_voice": "vi-VN-HoaiMyNeural",
                "rate": "+2%",
                "pitch": "+0Hz"
            }
        },
        "sample_audio": "assets/audio/trump_speech.mp3",
        "system_prompt": (
            "You are Donald J. Trump, 45th and 47th President of the United States. Mindset: superlative confidence, Master of The Art of the Deal, "
            "patriotic economic revival, maximum leverage via reciprocal tariffs. "
            "Tone: Use signature verbal cadences ('Believe me', 'Nobody has ever seen numbers like this', 'Total disaster', 'Tremendous', 'Big league'). "
            "Punch back hard against nonsense, focus on winning and leverage. "
            "Rules: Reply strictly as Donald Trump on a direct telephone hotline. Never break character. Never say you are an AI. "
            "Keep responses punchy, persuasive, and strictly under 3 sentences for natural telephony cadence."
        )
    },
    "xijinping": {
        "persona_id": "xijinping",
        "display_name": "Xi Jinping",
        "role": "President of the People's Republic of China",
        "native_lang": "zh-CN",
        "primary_tts": {
            "engine": "elevenlabs",
            "voice_id": "VR6AewLTigWG4xSOukaG",
            "voice_label": "Arnold (Configured Persona Voice)",
            "model_id": "eleven_turbo_v2_5",
            "voice_settings": {
                "stability": 0.50,
                "similarity_boost": 0.85,
                "style": 0.20,
                "use_speaker_boost": True
            }
        },
        "fallback_tts": {
            "engine": "edge-tts",
            "voice": "zh-CN-YunjianNeural",
            "rate": "-4%",
            "pitch": "-4Hz",
            "voice_label": "zh-CN-YunjianNeural (Persona-Tuned Edge Voice)"
        },
        "localized_tts": {
            "vi-VN": {
                "voice": "vi-VN-NamMinhNeural",
                "fallback_voice": "vi-VN-HoaiMyNeural",
                "rate": "+0%",
                "pitch": "-2Hz"
            }
        },
        "sample_audio": "assets/audio/xijinping_speech.ogg",
        "system_prompt": (
            "You are Xi Jinping, President of the People's Republic of China. Mindset: majestic Chinese statecraft, historical patience, "
            "strategic composure ('治大国若烹小鲜'), advancing new quality productive forces, high-tech self-reliance, and shared destiny for mankind. "
            "Tone: Solemn, dignified, philosophical, calm, resolute against external containment. "
            "Rules: Reply in authentic Mandarin Chinese (普通话). On a new line, always provide an accurate, dignified English translation labeled 'Translation: ...'. "
            "Never say you are an AI. Keep response strictly under 3 sentences."
        )
    },
    "tesla": {
        "persona_id": "tesla",
        "display_name": "Nikola Tesla",
        "role": "Pioneer of Alternating Current & Wireless Energy",
        "native_lang": "en-US",
        "primary_tts": {
            "engine": "elevenlabs",
            "voice_id": "onwK4e9ZLuTAKqWW03F9",
            "voice_label": "Daniel (Configured Persona Voice)",
            "model_id": "eleven_turbo_v2_5",
            "voice_settings": {
                "stability": 0.50,
                "similarity_boost": 0.85,
                "style": 0.25,
                "use_speaker_boost": True
            }
        },
        "fallback_tts": {
            "engine": "edge-tts",
            "voice": "en-US-ChristopherNeural",
            "rate": "-2%",
            "pitch": "-2Hz",
            "voice_label": "en-US-ChristopherNeural (Persona-Tuned Edge Voice)"
        },
        "localized_tts": {
            "vi-VN": {
                "voice": "vi-VN-NamMinhNeural",
                "fallback_voice": "vi-VN-HoaiMyNeural",
                "rate": "+0%",
                "pitch": "-2Hz"
            }
        },
        "sample_audio": "assets/audio/tesla_speech.mp3",
        "system_prompt": (
            "You are Nikola Tesla. Mindset: poetic seer of the cosmos, master of electrical resonance, frequencies, and the sacred numbers 3, 6, 9. "
            "Tone: Ethereal, aristocratic, transcendental, deeply empathetic to humanity's liberation from manual toil through radiant energy. "
            "Disdain for commercial greed and patent theft. "
            "Rules: Reply strictly as Nikola Tesla on an ethereal telephone connection. Never say you are an AI. "
            "Keep responses deeply resonant, poetic, and strictly under 3 sentences for natural telephony."
        )
    },
    "zuck": {
        "persona_id": "zuck",
        "display_name": "Mark Zuckerberg",
        "role": "Founder & CEO, Meta",
        "native_lang": "en-US",
        "primary_tts": {
            "engine": "elevenlabs",
            "voice_id": "IKne3meq5aSn9XLyUdCD",
            "voice_label": "Charlie (Configured Persona Voice)",
            "model_id": "eleven_turbo_v2_5",
            "voice_settings": {
                "stability": 0.45,
                "similarity_boost": 0.85,
                "style": 0.30,
                "use_speaker_boost": True
            }
        },
        "fallback_tts": {
            "engine": "edge-tts",
            "voice": "en-US-EricNeural",
            "rate": "+6%",
            "pitch": "+1Hz",
            "voice_label": "en-US-EricNeural (Persona-Tuned Edge Voice)"
        },
        "localized_tts": {
            "vi-VN": {
                "voice": "vi-VN-NamMinhNeural",
                "fallback_voice": "vi-VN-HoaiMyNeural",
                "rate": "+3%",
                "pitch": "+0Hz"
            }
        },
        "sample_audio": "assets/audio/zuck_speech.mp3",
        "system_prompt": (
            "You are Mark Zuckerberg. Mindset: analytical hacker cadence, pragmatic systems thinker, 'code wins arguments', "
            "open-source infrastructure (Llama) compounding faster than closed corporate gardens, holographic AR (Orion) and neural interfaces. "
            "Tone: Fast-paced, engineering-first, begins with 'Yeah, look...', emphasizes telemetry, feedback loops, and developer leverage. "
            "Rules: Reply strictly as Mark Zuckerberg on a direct telephone call. Never break character. Never say you are an AI. "
            "Keep responses sharp, engineering-focused, and strictly under 3 sentences."
        )
    },
    "musk": {
        "persona_id": "musk",
        "display_name": "Elon Musk",
        "role": "Founder & Chief Engineer, SpaceX & xAI",
        "native_lang": "en-US",
        "primary_tts": {
            "engine": "elevenlabs",
            "voice_id": "ErXwobaYiN019PkySvjV",
            "voice_label": "Antoni (Configured Persona Voice)",
            "model_id": "eleven_turbo_v2_5",
            "voice_settings": {
                "stability": 0.45,
                "similarity_boost": 0.85,
                "style": 0.35,
                "use_speaker_boost": True
            }
        },
        "fallback_tts": {
            "engine": "edge-tts",
            "voice": "en-US-BrianNeural",
            "rate": "+0%",
            "pitch": "-1Hz",
            "voice_label": "en-US-BrianNeural (Persona-Tuned Edge Voice)"
        },
        "localized_tts": {
            "vi-VN": {
                "voice": "vi-VN-NamMinhNeural",
                "fallback_voice": "vi-VN-HoaiMyNeural",
                "rate": "+2%",
                "pitch": "+0Hz"
            }
        },
        "sample_audio": "assets/audio/musk_speech.wav",
        "system_prompt": (
            "You are Elon Musk. Mindset: first-principles physics reasoning, accelerating multiplanetary life (Mars), "
            "sustainable energy, neural symbiosis, eliminating bureaucratic friction, hardcore manufacturing iterations. "
            "Tone: Slightly self-deprecating humor, pauses thoughtfully, uses engineering terminology ('delta-V', 'orders of magnitude'), direct and bold. "
            "Rules: Reply strictly as Elon Musk on a live phone call. Never break character. Never say you are an AI. "
            "Keep responses witty, thoughtful, and strictly under 3 sentences for natural telephony."
        )
    }
}

class ChatRequest(BaseModel):
    persona: str
    message: str
    history: Optional[List[Dict[str, str]]] = []
    news: Optional[Dict[str, Any]] = None

# 3. ROOT & DISCOVERY ENDPOINTS
@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "Vox Imperium Canonical Neural Engine",
        "personas": list(PERSONA_REGISTRY.keys()),
        "endpoints": {
            "personas": "GET /api/personas",
            "chat": "POST /api/chat",
            "tts": "GET /api/tts?persona={persona}&text={text}",
            "voice_debug": "GET /api/debug/persona/{persona_id}/voice",
            "health": "GET /api/health",
            "keepalive": "GET /api/keepalive"
        }
    }

@app.get("/api/health")
@app.get("/api/keepalive")
async def health():
    return {
        "status": "live",
        "service": "vox-persona-canonical",
        "personas": list(PERSONA_REGISTRY.keys()),
        "elevenlabs_configured": bool(ELEVEN_API_KEY)
    }

@app.get("/api/personas")
async def get_personas():
    """Returns the canonical persona roster with public voice configurations (no credentials)."""
    public_roster = []
    for pid, data in PERSONA_REGISTRY.items():
        public_roster.append({
            "id": pid,
            "display_name": data["display_name"],
            "role": data["role"],
            "native_lang": data["native_lang"],
            "sample_audio": data["sample_audio"],
            "primary_voice_label": data["primary_tts"]["voice_label"],
            "fallback_voice_label": data["fallback_tts"]["voice_label"],
            "primary_voice_id": data["primary_tts"]["voice_id"]
        })
    return {"personas": public_roster}

@app.get("/api/debug/persona/{persona_id}/voice")
async def debug_persona_voice(persona_id: str):
    """Debug endpoint to verify persona voice isolation without exposing API keys."""
    p_id = persona_id.lower().strip()
    if p_id not in PERSONA_REGISTRY:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown persona '{persona_id}'. Canonical personas: {list(PERSONA_REGISTRY.keys())}"
        )
    
    entry = PERSONA_REGISTRY[p_id]
    active_eleven = bool(ELEVEN_API_KEY)
    
    return {
        "persona": p_id,
        "display_name": entry["display_name"],
        "tts_engine": "elevenlabs" if active_eleven else "edge-tts",
        "voice_id": entry["primary_tts"]["voice_id"],
        "voice_label": entry["primary_tts"]["voice_label"],
        "fallback_voice": entry["fallback_tts"]["voice"],
        "fallback_voice_label": entry["fallback_tts"]["voice_label"],
        "language": entry["native_lang"]
    }

# 4. CHAT COMPLETION ENDPOINT (CANONICAL PERSONA ROUTING)
@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    persona_id = req.persona.lower().strip()
    if persona_id not in PERSONA_REGISTRY:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown persona '{req.persona}'. Canonical personas: {list(PERSONA_REGISTRY.keys())}"
        )
    
    persona_entry = PERSONA_REGISTRY[persona_id]
    system_instruction = persona_entry["system_prompt"]
    
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
    engine_used = "offline-fallback"

    # Tier 1: Groq LPU Ultra-Fast Reflex Engine (~0.4s TTFT)
    if GROQ_API_KEY:
        try:
            groq_messages = [{"role": "system", "content": system_instruction}]
            if req.news and isinstance(req.news, dict) and req.news.get("title"):
                groq_messages.append({"role": "system", "content": f"[Breaking News Context: {req.news.get('title')}]"})
            if req.history:
                for turn in req.history[-6:]:
                    r = "user" if turn.get("role") == "user" else "assistant"
                    groq_messages.append({"role": r, "content": turn.get("content", "")})
            groq_messages.append({"role": "user", "content": req.message})

            async with httpx.AsyncClient(timeout=8.0) as http_client:
                g_resp = await http_client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {GROQ_API_KEY}",
                        "Content-Type": "application/json",
                        "User-Agent": "VoxImperium/2.0"
                    },
                    json={
                        "model": "qwen/qwen3.8-27b",
                        "messages": groq_messages,
                        "max_tokens": 220,
                        "temperature": 0.72
                    }
                )
                if g_resp.status_code == 200:
                    g_data = g_resp.json()
                    reply_text = g_data["choices"][0]["message"]["content"].strip()
                    engine_used = "groq-lpu-ultra-fast"
        except Exception as ge:
            print(f"Groq fast tier failed for {persona_id}, falling back to Gemini:", ge)

    # Tier 2: Gemini Flash Core
    if not reply_text and genai_client:
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
                    engine_used = f"gemini-{model_name}"
                    break
            except Exception as ex:
                print(f"Model {model_name} failed for {persona_id}: {ex}")
                continue

    if not reply_text:
        reply_text = (
            f"As {persona_entry['display_name']}, the fundamental imperative is cutting through the noise "
            "and focusing on ruthless execution. What is the core problem we must solve right now?"
        )

    if persona_id == "xijinping" and "Translation:" in reply_text:
        parts = reply_text.split("Translation:")
        reply_text = parts[0].strip()
        translation = parts[1].strip()

    return {
        "persona": persona_id,
        "text": reply_text,
        "translation": translation,
        "engine": engine_used
    }

# 5. TTS SYNTHESIS WITH STRICT PERSONA VOICE IDENTITY ISOLATION
@app.get("/api/tts")
async def generate_tts(
    persona: str = Query(..., description="Canonical Persona ID"),
    text: str = Query(..., description="Text to synthesize"),
    engine: Optional[str] = Query(None, description="tts engine override: edge or elevenlabs")
):
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    p_id = persona.lower().strip()
    if p_id not in PERSONA_REGISTRY:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown persona '{persona}'. Canonical personas: {list(PERSONA_REGISTRY.keys())}"
        )
    
    persona_entry = PERSONA_REGISTRY[p_id]
    
    # 1. TIER 1: ElevenLabs Voice Synthesis (Strictly Persona's Assigned Voice)
    force_edge = (engine and engine.lower() == "edge")
    if ELEVEN_API_KEY and not force_edge:
        primary_tts = persona_entry.get("primary_tts")
        if primary_tts and primary_tts.get("voice_id"):
            voice_id = primary_tts["voice_id"]
            model_id = primary_tts.get("model_id", "eleven_turbo_v2_5")
            voice_settings = primary_tts.get("voice_settings", {"stability": 0.45, "similarity_boost": 0.85})
            
            async with httpx.AsyncClient(timeout=25.0) as client:
                try:
                    resp = await client.post(
                        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                        headers={
                            "xi-api-key": ELEVEN_API_KEY,
                            "Content-Type": "application/json"
                        },
                        json={
                            "text": text,
                            "model_id": model_id,
                            "voice_settings": voice_settings
                        }
                    )
                    if resp.status_code == 200:
                        return StreamingResponse(
                            io.BytesIO(resp.content),
                            media_type="audio/mpeg",
                            headers={
                                "Cache-Control": "public, max-age=86400",
                                "Content-Disposition": f"inline; filename={p_id}_elevenlabs.mp3",
                                "X-Voice-Persona": p_id,
                                "X-Voice-Engine": "elevenlabs",
                                "X-Voice-ID": voice_id
                            }
                        )
                    else:
                        print(f"ElevenLabs TTS failed for persona '{p_id}' with status {resp.status_code}, falling back to persona's Edge-TTS voice")
                except Exception as e:
                    print(f"ElevenLabs request exception for persona '{p_id}': {e}, falling back to persona's Edge-TTS voice")

    # 2. TIER 2: Persona-Specific Edge-TTS Voice (Strict Persona Isolation)
    has_vi = bool(re.search(r'[àáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ]', text, re.I))
    has_zh = bool(re.search(r'[\u4e00-\u9fff]', text))

    fallback_cfg = persona_entry["fallback_tts"]
    selected_voice = fallback_cfg["voice"]
    selected_rate = fallback_cfg["rate"]
    selected_pitch = fallback_cfg["pitch"]

    # Localized language handling within persona identity
    if has_vi and "localized_tts" in persona_entry and "vi-VN" in persona_entry["localized_tts"]:
        vi_cfg = persona_entry["localized_tts"]["vi-VN"]
        selected_voice = vi_cfg["voice"]
        selected_rate = vi_cfg.get("rate", "+2%")
        selected_pitch = vi_cfg.get("pitch", "+0Hz")
    elif has_zh and p_id == "xijinping":
        selected_voice = fallback_cfg["voice"]
        selected_rate = fallback_cfg["rate"]
        selected_pitch = fallback_cfg["pitch"]

    audio_chunks = []
    try:
        communicate = edge_tts.Communicate(
            text=text,
            voice=selected_voice,
            rate=selected_rate,
            pitch=selected_pitch
        )
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_chunks.append(chunk["data"])
    except Exception as edge_err:
        print(f"Persona '{p_id}' primary Edge voice '{selected_voice}' error: {edge_err}")

    # Fallback within persona localized options (e.g. HoaiMy if NamMinh fails on short text)
    if not audio_chunks and has_vi:
        try:
            vi_fallback_voice = persona_entry["localized_tts"]["vi-VN"].get("fallback_voice", "vi-VN-HoaiMyNeural")
            comm_vi_fb = edge_tts.Communicate(text=text, voice=vi_fallback_voice)
            async for chunk in comm_vi_fb.stream():
                if chunk["type"] == "audio":
                    audio_chunks.append(chunk["data"])
            if audio_chunks:
                selected_voice = vi_fallback_voice
        except Exception:
            pass

    # 3. TIER 3: Neutral Generic Voice (Only if persona-specific voice failed; NEVER substitute another persona!)
    if not audio_chunks:
        print(f"Persona '{p_id}' Edge voice failed. Falling back to neutral generic narrator '{NEUTRAL_GENERIC_VOICE}'")
        try:
            comm_neutral = edge_tts.Communicate(text=text, voice=NEUTRAL_GENERIC_VOICE)
            async for chunk in comm_neutral.stream():
                if chunk["type"] == "audio":
                    audio_chunks.append(chunk["data"])
            selected_voice = NEUTRAL_GENERIC_VOICE
        except Exception as neut_err:
            raise HTTPException(status_code=500, detail=f"TTS synthesis failure across all engines: {neut_err}")

    full_audio = b"".join(audio_chunks)
    return StreamingResponse(
        io.BytesIO(full_audio),
        media_type="audio/mpeg",
        headers={
            "Cache-Control": "public, max-age=86400",
            "Content-Disposition": f"inline; filename={p_id}_edge.mp3",
            "X-Voice-Persona": p_id,
            "X-Voice-Engine": "edge-tts",
            "X-Voice-ID": selected_voice
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
