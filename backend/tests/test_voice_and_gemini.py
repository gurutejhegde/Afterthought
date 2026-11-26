import base64
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings
from app.services.voice_service import VoiceService


def test_voice_clean_text_and_fallback_endpoints(monkeypatch):
    monkeypatch.setattr(settings, "ELEVENLABS_API_KEY", "")
    monkeypatch.setattr(settings, "FORCE_OFFLINE_AI", True)

    cleaned = VoiceService.clean_text_for_speech("📅 **Daily Briefing**\n• Verify `slide 5`")
    assert "Daily Briefing" in cleaned
    assert "*" not in cleaned
    assert "`" not in cleaned

    with TestClient(app) as client:
        status = client.get("/api/voice/status")
        assert status.status_code == 200
        assert status.json()["elevenlabs_configured"] is False
        assert status.json()["tts_provider"] == "web_speech_fallback"

        voices = client.get("/api/voice/voices")
        assert voices.status_code == 200
        assert len(voices.json()["voices"]) >= 3

        synth = client.post("/api/voice/synthesize", json={"text": "Hello **team**!"})
        assert synth.status_code == 200
        assert synth.json()["provider"] == "web_speech_fallback"
        assert synth.json()["speech_text"] == "Hello team!"

        voice_turn = client.post("/api/voice/chat", data={"transcript": "Give me my daily briefing"})
        assert voice_turn.status_code == 200
        body = voice_turn.json()
        assert body["tts_provider"] == "web_speech_fallback"
        assert "Daily Briefing" in body["response"]


def test_voice_elevenlabs_tts_and_stt_mocked(monkeypatch):
    monkeypatch.setattr(settings, "ELEVENLABS_API_KEY", "test-el-key")
    monkeypatch.setattr(settings, "FORCE_OFFLINE_AI", True)

    mock_tts_resp = MagicMock()
    mock_tts_resp.content = b"FAKE_MP3_BYTES"
    mock_tts_resp.raise_for_status = MagicMock()

    mock_stt_resp = MagicMock()
    mock_stt_resp.json.return_value = {"text": "Give me my daily briefing", "language_code": "eng"}
    mock_stt_resp.raise_for_status = MagicMock()

    async def fake_post(self, url, **kwargs):
        if "speech-to-text" in url:
            return mock_stt_resp
        return mock_tts_resp

    with patch("httpx.AsyncClient.post", new=fake_post):
        with TestClient(app) as client:
            synth = client.post("/api/voice/synthesize", json={"text": "Testing audio"})
            assert synth.status_code == 200
            assert synth.headers["content-type"] == "audio/mpeg"
            assert synth.content == b"FAKE_MP3_BYTES"

            voice_chat = client.post(
                "/api/voice/chat",
                files={"audio": ("clip.webm", b"WEBM_DATA", "audio/webm")},
            )
            assert voice_chat.status_code == 200
            body = voice_chat.json()
            assert body["transcript"] == "Give me my daily briefing"
            assert body["stt_provider"] == "elevenlabs_scribe"
            assert body["tts_provider"] == "elevenlabs"
            assert base64.b64decode(body["audio_base64"]) == b"FAKE_MP3_BYTES"


def test_gemini_multi_round_tool_calling(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setattr(settings, "FORCE_OFFLINE_AI", False)

    fake_call = SimpleNamespace(
        name="stage_organize_drive_file",
        args={
            "file_id": "drive-01",
            "target_folder": "/Hackathon/Submissions",
            "summary": "Move Nebula_Track1_Pitch.pptx to /Hackathon/Submissions",
        },
    )
    round_1 = SimpleNamespace(
        candidates=[SimpleNamespace(content=SimpleNamespace(role="model", parts=[]))],
        function_calls=[fake_call],
        text="",
    )
    round_2 = SimpleNamespace(
        candidates=[SimpleNamespace(content=SimpleNamespace(role="model", parts=[]))],
        function_calls=[],
        text="I staged moving Nebula_Track1_Pitch.pptx for your approval.",
    )

    mock_generate = AsyncMock(side_effect=[round_1, round_2])
    fake_client = MagicMock()
    fake_client.aio.models.generate_content = mock_generate

    with patch("google.genai.Client", return_value=fake_client):
        with TestClient(app) as client:
            res = client.post("/api/chat", json={"message": "Move my pitch deck to Submissions"})
            assert res.status_code == 200
            data = res.json()
            assert "approval" in data["response"].lower()
            assert data["action_required"]["tool_name"] == "organize_drive_file"
            assert "Gemini" in data["sources_checked"]
            assert mock_generate.await_count == 2
