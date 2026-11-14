"""Turns a request like "remind me to call mum at 3:15 tomorrow" into fields.

Two routes:
  - llm_parse(): calls an LLM and asks for JSON (used if an API key is set)
  - rule_parse(): a simple built-in parser, used as a stand-in when no key is set

Both return the same shape:
  {"task": str|None, "time": "HH:MM"|None, "date": "today"|"tomorrow"|"YYYY-MM-DD"|None,
   "out_of_scope": bool, "reason": str|None}
"""
import json
import os
import re
import urllib.error
import urllib.request

SCHEMA_HINT = (
    'Return ONLY a JSON object with keys: '
    '"task" (string or null), "time" (24h "HH:MM" or null), '
    '"date" ("today", "tomorrow", "YYYY-MM-DD" or null), '
    '"out_of_scope" (true if the request is not a time-based reminder, '
    'e.g. location-based, recurring, or not a reminder at all), '
    '"reason" (short string if out_of_scope, else null). '
    'Use null when the request does not say something. Never guess a time.'
)

SYSTEM = (
    "You extract reminder details from a user's spoken request. "
    "You only support one-off reminders at a specific time. " + SCHEMA_HINT
)


def _post(url, headers, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def _extract_json(text):
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("model did not return JSON")
    return json.loads(m.group(0))


def _openai_compatible(base_url, key, model, text):
    """One call to any OpenAI-compatible chat endpoint (OpenAI, Gemini, Groq, Ollama)."""
    body = {"model": model,
            "response_format": {"type": "json_object"},
            "messages": [{"role": "system", "content": SYSTEM},
                         {"role": "user", "content": text}]}
    headers = {"Authorization": "Bearer " + key, "Content-Type": "application/json"}
    url = base_url.rstrip("/") + "/chat/completions"
    try:
        out = _post(url, headers, body)
    except urllib.error.HTTPError as e:
        if e.code != 400:
            raise
        body.pop("response_format")  # some providers reject it; the prompt still asks for JSON
        out = _post(url, headers, body)
    return _extract_json(out["choices"][0]["message"]["content"])


def provider():
    """Which LLM will be used, based on the environment. None means the rule-based stand-in."""
    if os.environ.get("GEMINI_API_KEY"):
        return "Gemini (" + os.environ.get("MODEL", "gemini-2.5-flash") + ")"
    if os.environ.get("OPENAI_API_KEY"):
        return "OpenAI (" + os.environ.get("MODEL", "gpt-4o-mini") + ")"
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "Anthropic (" + os.environ.get("MODEL", "claude-haiku-4-5") + ")"
    return None


def llm_parse(text):
    """Calls Gemini, OpenAI or Anthropic depending on which key is set. Returns None if no key."""
    if os.environ.get("GEMINI_API_KEY"):
        return _openai_compatible(
            "https://generativelanguage.googleapis.com/v1beta/openai/",
            os.environ["GEMINI_API_KEY"], os.environ.get("MODEL", "gemini-2.5-flash"), text)
    if os.environ.get("OPENAI_API_KEY"):
        out = _post(
            "https://api.openai.com/v1/chat/completions",
            {"Authorization": "Bearer " + os.environ["OPENAI_API_KEY"],
             "Content-Type": "application/json"},
            {"model": os.environ.get("MODEL", "gpt-4o-mini"),
             "response_format": {"type": "json_object"},
             "messages": [{"role": "system", "content": SYSTEM},
                          {"role": "user", "content": text}]},
        )
        return _extract_json(out["choices"][0]["message"]["content"])
    if os.environ.get("ANTHROPIC_API_KEY"):
        out = _post(
            "https://api.anthropic.com/v1/messages",
            {"x-api-key": os.environ["ANTHROPIC_API_KEY"],
             "anthropic-version": "2023-06-01",
             "content-type": "application/json"},
            {"model": os.environ.get("MODEL", "claude-haiku-4-5"),
             "max_tokens": 300, "system": SYSTEM,
             "messages": [{"role": "user", "content": text}]},
        )
        return _extract_json(out["content"][0]["text"])
    return None


WORD_NUMS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
    "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
    "fifteen": 15, "thirty": 30, "forty five": 45, "fifty": 50,
}

OUT_OF_SCOPE = [
    (r"\bwhen i (get|arrive|leave|reach)\b|\bwhen i'm (at|home)\b", "location-based reminders"),
    (r"\bevery (day|week|morning|monday|tuesday|wednesday|thursday|friday)\b|\bdaily\b|\bweekly\b",
     "repeating reminders"),
]


def rule_parse(text):
    """Stand-in parser (no AI). Handles common phrasings only."""
    t = text.lower().strip()
    for pattern, what in OUT_OF_SCOPE:
        if re.search(pattern, t):
            return {"task": None, "time": None, "date": None,
                    "out_of_scope": True, "reason": what}
    if "remind" not in t:
        return {"task": None, "time": None, "date": None,
                "out_of_scope": True, "reason": "requests that are not reminders"}

    # spoken numbers -> digits ("three fifteen" -> "3 15")
    for w, n in sorted(WORD_NUMS.items(), key=lambda kv: -len(kv[0])):
        t = re.sub(r"\b" + w + r"\b", str(n), t)

    time = None
    m = re.search(r"\bat (\d{1,2})(?:[:. ](\d{2}))?\s*(am|pm|a\.m\.|p\.m\.)?", t)
    if m:
        h, mins, ap = int(m.group(1)), int(m.group(2) or 0), (m.group(3) or "")
        if ap.startswith("p") and h < 12:
            h += 12
        if ap.startswith("a") and h == 12:
            h = 0
        if not ap and 1 <= h <= 7:  # "at 3" in conversation usually means afternoon
            h += 12
        time = f"{h:02d}:{mins:02d}"

    date = "tomorrow" if "tomorrow" in t else ("today" if "today" in t or time else None)

    task = None
    m = re.search(r"remind me (?:to )?(.*?)(?:\s+at\s+\d|\s+tomorrow|\s+today|$)", t)
    if m and m.group(1).strip():
        task = m.group(1).strip()

    return {"task": task, "time": time, "date": date, "out_of_scope": False, "reason": None}


def parse(text):
    """Returns (fields, route) where route says which parser ran."""
    try:
        fields = llm_parse(text)
        if fields is not None:
            return fields, "llm"
    except Exception as e:  # network or format problem: fall back, and say so
        print("LLM call failed, using rule parser:", e)
        return rule_parse(text), "rules (LLM failed)"
    return rule_parse(text), "rules"