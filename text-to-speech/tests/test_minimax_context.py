from __future__ import annotations

import asyncio
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "text_to_speech.py"
SPEC = importlib.util.spec_from_file_location("text_to_speech", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def make_tts(engine: str = "minimax"):
    tts = MODULE.TextToSpeech.__new__(MODULE.TextToSpeech)
    tts.engine = engine
    tts.config = {
        "minimax_tts": {
            "api_key_env": "MINIMAX_API_KEY",
            "endpoint": "https://example.invalid/v1/t2a_v2",
            "model": "speech-2.8-hd",
            "voice_id": "Chinese (Mandarin)_Reliable_Executive",
            "speed": 1.0,
            "volume": 1.0,
            "pitch": 0,
            "context_adaptation": {
                "enabled": True,
                "default_context": "explanation",
                "limits": {
                    "speed_min": 0.8,
                    "speed_max": 1.2,
                    "volume_min": 0.8,
                    "volume_max": 1.2,
                    "pitch_min": -2,
                    "pitch_max": 2,
                },
                "profiles": {
                    "explanation": {
                        "speed_multiplier": 0.96,
                        "volume_multiplier": 1.0,
                        "pitch_offset": 0,
                    },
                    "instruction": {
                        "speed_multiplier": 0.93,
                        "volume_multiplier": 1.02,
                        "pitch_offset": 0,
                    },
                    "warning": {
                        "speed_multiplier": 0.9,
                        "volume_multiplier": 1.08,
                        "pitch_offset": -1,
                    },
                    "neutral": {
                        "speed_multiplier": 0.97,
                        "volume_multiplier": 1.0,
                        "pitch_offset": 0,
                    },
                },
                "rules": [
                    {"context": "warning", "keywords": ["注意", "不要"]},
                    {"context": "instruction", "keywords": ["点击", "打开"]},
                ],
            },
            "sample_rate": 32000,
            "bitrate": 128000,
            "format": "mp3",
            "channel": 1,
            "timeout": 5,
        }
    }
    return tts


class MiniMaxContextTests(unittest.TestCase):
    def test_auto_context_uses_rule_priority(self):
        tts = make_tts()
        name, _ = tts._resolve_minimax_context("点击打开设置，但注意不要关闭网络")
        self.assertEqual(name, "warning")

    def test_explicit_context_overrides_text_inference(self):
        tts = make_tts()
        name, _ = tts._resolve_minimax_context("注意这里有风险", "instruction")
        self.assertEqual(name, "instruction")

    def test_minimax_context_modifies_only_minimax_payload(self):
        tts = make_tts()

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return json.dumps({
                    "data": {"audio": "00"},
                    "base_resp": {"status_code": 0},
                }).encode("utf-8")

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "warning.mp3"
            with (
                mock.patch.dict(os.environ, {"MINIMAX_API_KEY": "test-key"}),
                mock.patch.object(MODULE.urllib.request, "urlopen", return_value=Response()) as urlopen,
            ):
                result = asyncio.run(tts.synthesize_minimax("注意不要跳过这一步", str(output)))

        self.assertEqual(result, str(output))
        request = urlopen.call_args.args[0]
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(payload["voice_setting"]["voice_id"], "Chinese (Mandarin)_Reliable_Executive")
        self.assertEqual(payload["voice_setting"]["speed"], 0.9)
        self.assertEqual(payload["voice_setting"]["vol"], 1.08)
        self.assertEqual(payload["voice_setting"]["pitch"], -1)
        self.assertNotIn("emotion", payload["voice_setting"])

    def test_edge_does_not_resolve_minimax_context(self):
        tts = make_tts("edge")
        with (
            mock.patch.object(tts, "_resolve_minimax_context", side_effect=AssertionError("must not run")),
            mock.patch.object(tts, "synthesize_edge", new=mock.AsyncMock(return_value="edge.mp3")) as edge,
        ):
            result = asyncio.run(tts.synthesize("注意", "edge.mp3", context="warning"))
        self.assertEqual(result, "edge.mp3")
        edge.assert_awaited_once()

    def test_kokoro_does_not_resolve_minimax_context(self):
        tts = make_tts("kokoro")
        with (
            mock.patch.object(tts, "_resolve_minimax_context", side_effect=AssertionError("must not run")),
            mock.patch.object(tts, "synthesize_kokoro", new=mock.AsyncMock(return_value="kokoro.mp3")) as kokoro,
        ):
            result = asyncio.run(tts.synthesize("注意", "kokoro.mp3", context="warning"))
        self.assertEqual(result, "kokoro.mp3")
        kokoro.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
