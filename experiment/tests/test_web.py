from http import HTTPStatus
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import sys
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sinhalasub.web import (  # noqa: E402
    WorkspaceHandler,
    export_payload,
    parse_payload,
    prepare_translation_payload,
)


SRT = "1\n00:00:01,000 --> 00:00:02,500\nHello there.\n"


class PayloadTests(unittest.TestCase):
    def test_parse_and_export_preserve_structure_with_edited_text(self) -> None:
        payload = parse_payload({"format": "srt", "content": SRT})
        payload["cues"][0]["target_text"] = "ආයුබෝවන්."

        exported = export_payload(payload)
        reparsed = parse_payload({"format": "srt", "content": exported})

        self.assertEqual("1", reparsed["cues"][0]["id"])
        self.assertEqual(1000, reparsed["cues"][0]["start_ms"])
        self.assertEqual(2500, reparsed["cues"][0]["end_ms"])
        self.assertEqual("ආයුබෝවන්.", reparsed["cues"][0]["text"])

    def test_export_rejects_empty_target(self) -> None:
        payload = parse_payload({"format": "srt", "content": SRT})
        payload["cues"][0]["target_text"] = ""

        with self.assertRaisesRegex(ValueError, "EMPTY_CUE"):
            export_payload(payload)

    def test_prepares_context_and_confirmed_names(self) -> None:
        payload = parse_payload({"format": "srt", "content": SRT.replace("Hello", "Will has 2")})
        payload["confirmed_names"] = ["Will"]

        prepared = prepare_translation_payload(payload)

        self.assertEqual(1, len(prepared["blocks"]))
        self.assertEqual(2, prepared["protected_count"])
        self.assertEqual(("NAME", "NUMBER"), tuple(item["kind"] for item in prepared["protected_by_cue"]["1"]))


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), WorkspaceHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def test_serves_workspace_and_health(self) -> None:
        with urlopen(f"{self.base_url}/", timeout=2) as response:
            self.assertEqual(HTTPStatus.OK, response.status)
            self.assertIn(b"SinhalaSub Review Workspace", response.read())

        with urlopen(f"{self.base_url}/api/health", timeout=2) as response:
            self.assertEqual({"status": "ok"}, json.load(response))

    def test_parse_endpoint_returns_canonical_cues(self) -> None:
        result = self._post("/api/parse", {"format": "srt", "content": SRT})

        self.assertEqual("srt", result["format"])
        self.assertEqual("Hello there.", result["cues"][0]["target_text"])

    def test_prepare_endpoint_returns_context_blocks(self) -> None:
        parsed = self._post("/api/parse", {"format": "srt", "content": SRT})
        parsed["confirmed_names"] = []

        result = self._post("/api/prepare-translation", parsed)

        self.assertEqual(["1"], result["blocks"][0]["cue_ids"])

    def test_parse_endpoint_returns_structured_error(self) -> None:
        request = Request(
            f"{self.base_url}/api/parse",
            data=json.dumps({"format": "srt", "content": "broken"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with self.assertRaises(HTTPError) as raised:
            urlopen(request, timeout=2)

        self.assertEqual(HTTPStatus.BAD_REQUEST, raised.exception.code)
        self.assertEqual("MALFORMED_CUE", json.load(raised.exception)["error"])

    def _post(self, path: str, payload: object) -> object:
        request = Request(
            f"{self.base_url}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=2) as response:
            return json.load(response)


if __name__ == "__main__":
    unittest.main()
