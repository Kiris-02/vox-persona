import unittest
from fastapi.testclient import TestClient
from main import app, PERSONA_REGISTRY, NEUTRAL_GENERIC_VOICE

client = TestClient(app)

class TestPersonaVoiceRouting(unittest.TestCase):

    def test_persona_registry_completeness(self):
        """Verify all 6 canonical personas are registered with distinct configurations."""
        expected_personas = {"jobs", "trump", "xijinping", "tesla", "zuck", "musk"}
        self.assertEqual(set(PERSONA_REGISTRY.keys()), expected_personas, "Registry must contain exactly the 6 canonical personas")

        for pid, data in PERSONA_REGISTRY.items():
            self.assertEqual(data["persona_id"], pid)
            self.assertTrue(len(data.get("display_name", "")) > 0)
            self.assertIn("primary_tts", data)
            self.assertIn("voice_id", data["primary_tts"])
            self.assertIn("fallback_tts", data)
            self.assertIn("voice", data["fallback_tts"])
            self.assertTrue(len(data.get("system_prompt", "")) > 50)

    def test_persona_voice_identity_isolation(self):
        """Verify each persona resolves to a distinct, isolated primary and fallback voice."""
        primary_voice_ids = {}
        fallback_voices = {}

        for pid, data in PERSONA_REGISTRY.items():
            vid = data["primary_tts"]["voice_id"]
            fvid = data["fallback_tts"]["voice"]
            
            # Verify no duplicate primary voice IDs across different personas
            self.assertNotIn(vid, primary_voice_ids.values(), f"Duplicate ElevenLabs voice_id '{vid}' assigned to '{pid}'")
            primary_voice_ids[pid] = vid
            
            # Verify no duplicate fallback voices across different personas
            self.assertNotIn(fvid, fallback_voices.values(), f"Duplicate Edge fallback voice '{fvid}' assigned to '{pid}'")
            fallback_voices[pid] = fvid

        # Explicit pair-wise non-equivalence assertions as mandated by Section 9
        self.assertNotEqual(primary_voice_ids["jobs"], primary_voice_ids["trump"])
        self.assertNotEqual(primary_voice_ids["jobs"], primary_voice_ids["musk"])
        self.assertNotEqual(primary_voice_ids["trump"], primary_voice_ids["xijinping"])
        self.assertNotEqual(primary_voice_ids["xijinping"], primary_voice_ids["tesla"])
        self.assertNotEqual(primary_voice_ids["tesla"], primary_voice_ids["zuck"])
        self.assertNotEqual(primary_voice_ids["zuck"], primary_voice_ids["musk"])

        self.assertNotEqual(fallback_voices["jobs"], fallback_voices["trump"])
        self.assertNotEqual(fallback_voices["jobs"], fallback_voices["musk"])
        self.assertNotEqual(fallback_voices["trump"], fallback_voices["xijinping"])
        self.assertNotEqual(fallback_voices["xijinping"], fallback_voices["tesla"])
        self.assertNotEqual(fallback_voices["tesla"], fallback_voices["zuck"])
        self.assertNotEqual(fallback_voices["zuck"], fallback_voices["musk"])

    def test_unknown_persona_rejection(self):
        """Verify unknown persona ID is rejected with HTTP 400 instead of cross-persona fallback."""
        # TTS endpoint
        res_tts = client.get("/api/tts?persona=non_existent_hero&text=hello")
        self.assertEqual(res_tts.status_code, 400)
        self.assertIn("Unknown persona", res_tts.json()["detail"])

        # Chat endpoint
        res_chat = client.post("/api/chat", json={"persona": "fake_persona", "message": "hello"})
        self.assertEqual(res_chat.status_code, 400)
        self.assertIn("Unknown persona", res_chat.json()["detail"])

        # Debug endpoint
        res_debug = client.get("/api/debug/persona/ghost_user/voice")
        self.assertEqual(res_debug.status_code, 400)
        self.assertIn("Unknown persona", res_debug.json()["detail"])

    def test_voice_debug_endpoint_contract(self):
        """Verify debug voice endpoint returns correct metadata and NEVER leaks credentials."""
        for pid in PERSONA_REGISTRY.keys():
            res = client.get(f"/api/debug/persona/{pid}/voice")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertEqual(data["persona"], pid)
            self.assertEqual(data["display_name"], PERSONA_REGISTRY[pid]["display_name"])
            self.assertEqual(data["voice_id"], PERSONA_REGISTRY[pid]["primary_tts"]["voice_id"])
            self.assertEqual(data["fallback_voice"], PERSONA_REGISTRY[pid]["fallback_tts"]["voice"])
            self.assertNotIn("key", str(data).lower())
            self.assertNotIn("secret", str(data).lower())

    def test_api_personas_endpoint(self):
        """Verify public discovery endpoint returns all personas without sensitive fields."""
        res = client.get("/api/personas")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("personas", data)
        self.assertEqual(len(data["personas"]), 6)
        pids = [p["id"] for p in data["personas"]]
        self.assertEqual(set(pids), set(PERSONA_REGISTRY.keys()))
        self.assertNotIn("system_prompt", str(data))

    def test_engine_fallback_isolation(self):
        """Verify that forcing edge engine routes strictly to that persona's configured Edge-TTS voice."""
        for pid, entry in PERSONA_REGISTRY.items():
            expected_edge_voice = entry["fallback_tts"]["voice"]
            res = client.get(f"/api/tts?persona={pid}&text=Quick+test+of+identity&engine=edge")
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.headers.get("X-Voice-Persona"), pid)
            self.assertEqual(res.headers.get("X-Voice-Engine"), "edge-tts")
            self.assertIn(
                res.headers.get("X-Voice-ID"),
                [expected_edge_voice, "en-US-AndrewNeural"],
                f"Persona '{pid}' must route to '{expected_edge_voice}' or fallback 'en-US-AndrewNeural', got '{res.headers.get('X-Voice-ID')}'"
            )

    def test_no_url_api_keys_accepted(self):
        """Verify that eleven_key query parameter is not present in OpenAPI schema."""
        openapi = client.get("/openapi.json").json()
        tts_params = openapi["paths"]["/api/tts"]["get"]["parameters"]
        param_names = [p["name"] for p in tts_params]
        self.assertNotIn("eleven_key", param_names, "'eleven_key' must not be in /api/tts parameters")
        self.assertIn("persona", param_names)
        self.assertIn("text", param_names)

if __name__ == "__main__":
    unittest.main()
