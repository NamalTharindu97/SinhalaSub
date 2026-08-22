"""Local browser workspace for reviewing subtitle text."""

import argparse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
from typing import Any, Dict
import webbrowser

from .subtitles import Cue, SubtitleDocument, SubtitleError, SubtitleFormat, parse_subtitle, serialize_subtitle
from .translation import prepare_document
from .quality import check_document


WEB_ROOT = Path(__file__).with_name("web_assets")
MAX_REQUEST_BYTES = 2 * 1024 * 1024


def parse_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    subtitle_format = SubtitleFormat(payload["format"])
    document = parse_subtitle(str(payload["content"]), subtitle_format)
    return {
        "format": document.format.value,
        "header": list(document.header),
        "webvtt_description": document.webvtt_description,
        "cues": [
            {
                "id": cue.id,
                "index": cue.index,
                "start_ms": cue.start_ms,
                "end_ms": cue.end_ms,
                "text": cue.text,
                "target_text": cue.text,
                "settings": cue.settings,
            }
            for cue in document.cues
        ],
    }


def export_payload(payload: Dict[str, Any]) -> str:
    document = _document_from_payload(payload, "target_text")
    return serialize_subtitle(document)


def prepare_translation_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    document = _document_from_payload(payload, "text")
    names = tuple(str(name).strip() for name in payload.get("confirmed_names", []) if str(name).strip())
    cues, blocks = prepare_document(document, confirmed_names=names)
    protected_by_cue = {
        cue.id: [
            {"placeholder": item.placeholder, "value": item.value, "kind": item.kind}
            for item in cue.protected_values
        ]
        for cue in cues
    }
    return {
        "blocks": [
            {
                "id": block.id,
                "cue_ids": list(block.cue_ids),
                "context_before": list(block.context_before),
                "context_after": list(block.context_after),
            }
            for block in blocks
        ],
        "protected_by_cue": protected_by_cue,
        "protected_count": sum(len(values) for values in protected_by_cue.values()),
    }


def quality_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    warnings = check_document(_document_from_payload(payload, "target_text"))
    by_cue: Dict[str, Any] = {}
    counts = {"high": 0, "medium": 0, "low": 0}
    for warning in warnings:
        by_cue.setdefault(warning.cue_id, []).append(
            {"code": warning.code, "severity": warning.severity, "message": warning.message}
        )
        counts[warning.severity] += 1
    return {"warnings_by_cue": by_cue, "counts": counts, "total": len(warnings)}


def _document_from_payload(payload: Dict[str, Any], text_field: str) -> SubtitleDocument:
    subtitle_format = SubtitleFormat(payload["format"])
    cues = tuple(
        Cue(
            id=str(raw["id"]),
            index=int(raw["index"]),
            start_ms=int(raw["start_ms"]),
            end_ms=int(raw["end_ms"]),
            text=str(raw[text_field]),
            settings=str(raw.get("settings", "")),
        )
        for raw in payload["cues"]
    )
    return SubtitleDocument(
        format=subtitle_format,
        cues=cues,
        header=tuple(str(line) for line in payload.get("header", [])),
        webvtt_description=str(payload.get("webvtt_description", "")),
    )


class WorkspaceHandler(BaseHTTPRequestHandler):
    server_version = "SinhalaSubLocal/0.1"

    def do_GET(self) -> None:
        if self.path == "/api/health":
            self._send_json({"status": "ok"})
            return

        path = "/index.html" if self.path == "/" else self.path.split("?", 1)[0]
        candidate = (WEB_ROOT / path.lstrip("/")).resolve()
        if WEB_ROOT.resolve() not in candidate.parents or not candidate.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        content_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
        body = candidate.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self'; script-src 'self'")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        routes = {
            "/api/parse": parse_payload,
            "/api/prepare-translation": prepare_translation_payload,
            "/api/qa": quality_payload,
            "/api/export": export_payload,
        }
        action = routes.get(self.path)
        if action is None:
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > MAX_REQUEST_BYTES:
                raise SubtitleError("INVALID_SIZE", "Request must be between 1 byte and 2 MiB.")
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            result = action(payload)
        except (KeyError, TypeError, ValueError, UnicodeError, json.JSONDecodeError) as error:
            code = error.code if isinstance(error, SubtitleError) else "INVALID_REQUEST"
            self._send_json({"error": code, "message": str(error)}, HTTPStatus.BAD_REQUEST)
            return

        if isinstance(result, str):
            self._send_json({"content": result})
        else:
            self._send_json(result)

    def _send_json(self, payload: Dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, message_format: str, *args: Any) -> None:
        print(f"[{self.log_date_time_string()}] {message_format % args}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the local SinhalaSub review workspace.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--open", action="store_true", dest="open_browser")
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), WorkspaceHandler)
    url = f"http://{args.host}:{server.server_port}"
    print(f"SinhalaSub workspace running at {url}")
    print("Press Ctrl+C to stop.")
    if args.open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping workspace.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
