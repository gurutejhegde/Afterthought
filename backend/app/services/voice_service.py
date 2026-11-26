import base64
import re
from typing import Dict, Any, List, Optional
import httpx
from app.config import settings


DEFAULT_VOICES = [
    {"voice_id": "21m00Tcm4TlvDq8ikWAM", "name": "Rachel (Calm Assistant)", "category": "premade"},
    {"voice_id": "EXAVITQu4vr4xnSDxMaL", "name": "Sarah (Warm & Clear)", "category": "premade"},
    {"voice_id": "onwK4e9ZLuTAKqWW03F9", "name": "Daniel (Crisp Briefing)", "category": "premade"},
]


class VoiceService:
    """
    ElevenLabs Voice Engine supporting Text-to-Speech (TTS), Speech-to-Text (Scribe STT),
    and voice profile listing, with clean fallback signaling for Web Speech API when no key is set.
    """

    ELEVENLABS_BASE = "https://api.elevenlabs.io/v1"

    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        configured = settings.elevenlabs_enabled
        return {
            "elevenlabs_configured": configured,
            "tts_provider": "elevenlabs" if configured else "web_speech_fallback",
            "stt_provider": "elevenlabs_scribe" if configured else "web_speech_fallback",
            "voice_id": settings.ELEVENLABS_VOICE_ID,
            "tts_model": settings.ELEVENLABS_MODEL_ID,
            "stt_model": settings.ELEVENLABS_STT_MODEL_ID,
        }

    @classmethod
    def clean_text_for_speech(cls, text: str) -> str:
        """Strip markdown symbols and decorative bullets so TTS sounds natural."""
        cleaned = re.sub(r"[*_`#>]+", "", text)
        cleaned = re.sub(r"•\s*", "", cleaned)
        cleaned = re.sub(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]+", "", cleaned)
        cleaned = re.sub(r"\n{2,}", ". ", cleaned)
        cleaned = re.sub(r"\n", ". ", cleaned)
        cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
        return cleaned[:1500]

    @classmethod
    async def list_voices(cls) -> Dict[str, Any]:
        if not settings.elevenlabs_enabled:
            return {
                "provider": "web_speech_fallback",
                "voices": DEFAULT_VOICES,
            }

        headers = {"xi-api-key": settings.ELEVENLABS_API_KEY}
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(f"{cls.ELEVENLABS_BASE}/voices", headers=headers)
            response.raise_for_status()
            data = response.json()
            voices: List[Dict[str, Any]] = [
                {
                    "voice_id": v.get("voice_id"),
                    "name": v.get("name"),
                    "category": v.get("category", "custom"),
                }
                for v in data.get("voices", [])
            ]
            return {"provider": "elevenlabs", "voices": voices or DEFAULT_VOICES}

    @classmethod
    async def synthesize_speech(
        cls, text: str, voice_id: Optional[str] = None
    ) -> Optional[bytes]:
        """Generate MP3 speech audio via ElevenLabs, or return None if no API key is configured."""
        if not settings.elevenlabs_enabled:
            return None

        speech_text = cls.clean_text_for_speech(text)
        if not speech_text:
            return None

        target_voice = voice_id or settings.ELEVENLABS_VOICE_ID
        url = f"{cls.ELEVENLABS_BASE}/text-to-speech/{target_voice}"
        headers = {
            "xi-api-key": settings.ELEVENLABS_API_KEY,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }
        payload = {
            "text": speech_text,
            "model_id": settings.ELEVENLABS_MODEL_ID,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
            },
        }

        async with httpx.AsyncClient(timeout=25.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.content

    @classmethod
    async def synthesize_speech_base64(
        cls, text: str, voice_id: Optional[str] = None
    ) -> Optional[str]:
        audio = await cls.synthesize_speech(text, voice_id=voice_id)
        if audio is None:
            return None
        return base64.b64encode(audio).decode("ascii")

    @classmethod
    async def transcribe_audio(
        cls,
        audio_bytes: bytes,
        filename: str = "audio.webm",
        content_type: str = "audio/webm",
    ) -> Dict[str, Any]:
        """Transcribe uploaded audio using ElevenLabs Scribe STT API."""
        if not settings.elevenlabs_enabled:
            return {
                "provider": "web_speech_fallback",
                "transcript": None,
                "message": "ELEVENLABS_API_KEY not configured; use browser Web Speech recognition.",
            }

        url = f"{cls.ELEVENLABS_BASE}/speech-to-text"
        headers = {"xi-api-key": settings.ELEVENLABS_API_KEY}
        files = {"file": (filename, audio_bytes, content_type)}
        data = {"model_id": settings.ELEVENLABS_STT_MODEL_ID}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, files=files, data=data)
            response.raise_for_status()
            body = response.json()
            return {
                "provider": "elevenlabs_scribe",
                "transcript": body.get("text", "").strip(),
                "language_code": body.get("language_code"),
            }
