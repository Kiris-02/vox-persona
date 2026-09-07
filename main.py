import asyncio
import io
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import edge_tts

app = FastAPI(title="Vox Imperium Neural Voice Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

VOICE_CONFIGS = {
    "jobs": {"voice": "en-US-BrianNeural", "rate": "+2%", "pitch": "+2Hz"},
    "trump": {"voice": "en-US-ChristopherNeural", "rate": "+3%", "pitch": "-4Hz"},
    "xijinping": {"voice": "zh-CN-YunjianNeural", "rate": "-5%", "pitch": "-5Hz"},
    "tesla": {"voice": "en-US-RogerNeural", "rate": "-3%", "pitch": "-3Hz"},
    "zuck": {"voice": "en-US-EricNeural", "rate": "+6%", "pitch": "+1Hz"},
    "musk": {"voice": "en-US-AndrewNeural", "rate": "+1%", "pitch": "-2Hz"},
}

@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "Vox Imperium Neural Voice Engine",
        "personas": list(VOICE_CONFIGS.keys()),
        "endpoints": {
            "tts": "/api/tts?persona={persona}&text={text}",
            "health": "/api/health"
        }
    }

@app.get("/api/health")
async def health():
    return {"status": "live", "service": "vox-persona-core", "personas": list(VOICE_CONFIGS.keys())}

@app.get("/api/tts")
async def generate_tts(
    persona: str = Query("zuck", description="Character ID"),
    text: str = Query(..., description="Text to synthesize")
):
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    cfg = VOICE_CONFIGS.get(persona.lower(), VOICE_CONFIGS["zuck"])
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
            "Content-Disposition": f"inline; filename={persona}_tts.mp3"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
