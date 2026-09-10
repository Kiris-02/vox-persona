import json
import os
import unittest

class TestSovitsBridge(unittest.TestCase):
    def test_notebook_json_validity(self):
        """Verify vox_gpt_sovits_colab.ipynb is valid JSON and contains required cells."""
        with open("vox_gpt_sovits_colab.ipynb", "r", encoding="utf-8") as f:
            nb = json.load(f)
        self.assertEqual(nb["nbformat"], 4)
        self.assertGreaterEqual(len(nb["cells"]), 8)

        # Check Cell 7 has the pycloudflared installation and try_cloudflare
        launcher_src = "".join(nb["cells"][7]["source"])
        self.assertIn("pip install -q pycloudflared", launcher_src)
        self.assertIn("try_cloudflare", launcher_src)
        self.assertIn("http://127.0.0.1:8000/synthesize", launcher_src)

    def test_audio_references_present(self):
        """Verify all 6 canonical reference audio files exist locally and are non-empty."""
        expected_files = [
            "jobs_speech.mp3",
            "trump_speech.mp3",
            "musk_speech.wav",
            "zuck_speech.mp3",
            "tesla_speech.mp3",
            "xijinping_speech.ogg"
        ]
        for f in expected_files:
            path = os.path.join("assets", "audio", f)
            self.assertTrue(os.path.exists(path), f"Missing audio file {f}")
            self.assertGreater(os.path.getsize(path), 50000, f"Audio file {f} is suspiciously small")

    def test_frontend_sovits_routing(self):
        """Verify index.html contains correct endpoint query format and test handler."""
        with open("index.html", "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("vox_use_sovits", content)
        self.assertIn("vox_sovits_endpoint", content)
        self.assertIn("testSovitsKey", content)
        self.assertIn("你好，这是由 GPT-SoVITS 驱动的习近平真实声音克隆。", content)

if __name__ == "__main__":
    unittest.main()
