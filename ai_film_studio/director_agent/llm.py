"""Ollama LLM client (local). Uses /api/chat with JSON output."""
import json
import re
import sys
import urllib.request


class LLMError(RuntimeError):
    pass


def _extract_json(text):
    """Robust: find first { ... } balanced block and parse it."""
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    start = text.find("{")
    if start == -1:
        raise LLMError(f"No JSON object found in LLM reply: {text[:300]}")
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:i + 1])
                except Exception as e:
                    raise LLMError(f"JSON parse failed: {e} :: {text[start:i+1][:300]}")
    raise LLMError("Unbalanced JSON in LLM reply")


class LLM:
    def __init__(self, base_url, model, temperature=0.7, timeout=600):
        self.base = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.timeout = timeout

    def chat_json(self, system, user):
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "format": "json",
            "options": {"temperature": self.temperature},
        }
        req = urllib.request.Request(
            self.base + "/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            raise LLMError(f"Ollama request failed ({self.base}): {e}")
        content = (data.get("message") or {}).get("content", "")
        if not content:
            raise LLMError(f"Empty LLM response: {str(data)[:300]}")
        return _extract_json(content)

    def chat_text(self, system, user):
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "options": {"temperature": self.temperature},
        }
        req = urllib.request.Request(
            self.base + "/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return (data.get("message") or {}).get("content", "")


def ping(base_url):
    try:
        with urllib.request.urlopen(base_url.rstrip("/") + "/api/tags", timeout=5) as r:
            tags = json.loads(r.read().decode("utf-8"))
        return [t.get("name") for t in tags.get("models", [])]
    except Exception as e:
        print(f"[llm] Ollama not reachable at {base_url}: {e}")
        return []
