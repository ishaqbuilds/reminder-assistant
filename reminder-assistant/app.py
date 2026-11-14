
import json
import re
import time as _time
from datetime import date as _date, datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import os

import extract

ROOT = Path(__file__).parent
REMINDERS = ROOT / "reminders.json"
LOG = ROOT / "interaction_log.jsonl"
CONFIDENCE_THRESHOLD = 0.80  


MISHEARINGS = [
    (r"\b3:15\b", "3:50"), (r"\bfifteen\b", "fifty"), (r"\b(\d{1,2}):15\b", r"\1:50"),
    (r"\bmum\b", "mom"), (r"\bdentist\b", "dentist's"),
]


def simulate_hearing(text, mishear):
    words = []
    heard_text = text
    changed = set()
    if mishear:
        for pattern, repl in MISHEARINGS:
            new = re.sub(pattern, repl, heard_text, count=1, flags=re.I)
            if new != heard_text:
                changed.update(re.sub(pattern, repl, m.group(0), flags=re.I)
                               for m in re.finditer(pattern, heard_text, re.I))
                heard_text = new
                break  # one mishearing per request
    for w in heard_text.split():
        conf = 0.55 if w.strip(".,!?") in changed else 0.95
        words.append({"word": w, "confidence": conf})
    return heard_text, words


# --- Validation: the code checks what the model proposed --------------------
def validate(fields):
    problems = []
    if not fields.get("task"):
        problems.append({"field": "task", "message": "I didn't catch what to remind you about."})
    t = fields.get("time")
    if not t:
        problems.append({"field": "time", "message": "I didn't catch a time."})
    else:
        try:
            datetime.strptime(t, "%H:%M")
        except ValueError:
            problems.append({"field": "time", "message": f"'{t}' isn't a valid time."})
    d = fields.get("date")
    if d not in ("today", "tomorrow"):
        try:
            datetime.strptime(d or "", "%Y-%m-%d")
        except ValueError:
            problems.append({"field": "date", "message": "I didn't catch which day."})
    if d == "today" and t and not problems:
        now = datetime.now().strftime("%H:%M")
        if t < now:
            problems.append({"field": "time", "message": f"{t} today has already passed."})
    return problems


def overall_confidence(words, route):
    lowest = min((w["confidence"] for w in words), default=0.0)
    return round(lowest if route == "llm" else min(lowest, 0.9), 2)


def log(event, **data):
    with LOG.open("a") as f:
        f.write(json.dumps({"ts": datetime.now().isoformat(timespec="seconds"),
                            "event": event, **data}) + "\n")


def load_reminders():
    return json.loads(REMINDERS.read_text()) if REMINDERS.exists() else []


# --- HTTP ----------------------------------------------------------------------
class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            return self._send(200, (ROOT / "static" / "index.html").read_bytes(), "text/html")
        if self.path == "/reminders":
            return self._send(200, load_reminders())
        self._send(404, {"error": "not found"})

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])) or "{}")

        if self.path == "/parse":
            heard, words = simulate_hearing(body.get("text", ""), body.get("mishear", False))
            fields, route = extract.parse(heard)
            if fields.get("out_of_scope"):
                result = {"heard": heard, "words": words, "route": route,
                          "out_of_scope": True, "reason": fields.get("reason")}
            else:
                fields = {k: fields.get(k) for k in ("task", "time", "date")}
                problems = validate(fields)
                conf = overall_confidence(words, route)
                result = {"heard": heard, "words": words, "route": route,
                          "out_of_scope": False, "fields": fields, "problems": problems,
                          "confidence": conf,
                          "must_confirm": bool(problems) or conf < CONFIDENCE_THRESHOLD}
            log("parse", request=body.get("text"), **result)
            return self._send(200, result)

        if self.path == "/validate":
            fields = body.get("fields", {})
            return self._send(200, {"problems": validate(fields)})

        if self.path == "/save":
            fields = body.get("fields", {})
            problems = validate(fields)
            if problems:  # never save something the validator rejects
                log("save_refused", fields=fields, problems=problems)
                return self._send(400, {"problems": problems})
            reminders = load_reminders()
            item = {"id": int(_time.time() * 1000), **fields,
                    "confirmed_by_user": body.get("confirmed", False),
                    "edits": body.get("edits", [])}
            reminders.append(item)
            REMINDERS.write_text(json.dumps(reminders, indent=2))
            log("save", **item)
            return self._send(200, item)

        if self.path == "/undo":
            reminders = [r for r in load_reminders() if r["id"] != body.get("id")]
            REMINDERS.write_text(json.dumps(reminders, indent=2))
            log("undo", id=body.get("id"))
            return self._send(200, {"ok": True})

        if self.path == "/cancel":
            log("cancel", fields=body.get("fields"))
            return self._send(200, {"ok": True})

        self._send(404, {"error": "not found"})

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    has_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    print("Parser:", "LLM" if has_key else "rule-based stand-in (no API key set)")
    print("Open http://localhost:8000  (Ctrl+C to stop)")
    HTTPServer(("127.0.0.1", 8000), Handler).serve_forever()
