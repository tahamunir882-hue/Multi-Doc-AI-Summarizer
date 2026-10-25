"""One place that decides how AI text is produced.
LLM_PROVIDER in .env:  offline (default, no API, no download)  |  ollama (free local AI)  |  anthropic (Claude API)"""
import json
import os
import urllib.request

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class NeedsModel(RuntimeError):
    pass


def provider() -> str:
    return os.getenv("LLM_PROVIDER", "offline").strip().lower()


def label() -> str:
    return {"offline": "Offline (no API)", "ollama": "Local AI (Ollama)", "anthropic": "Claude API"}.get(provider(), provider())


_client = None


def ask_llm(prompt: str, max_tokens: int = 1500) -> str:
    p = provider()
    if p == "ollama":
        body = json.dumps({"model": os.getenv("OLLAMA_MODEL", "qwen2.5:7b"), "prompt": prompt, "stream": False,
                           "options": {"num_predict": max_tokens}}).encode()
        req = urllib.request.Request(os.getenv("OLLAMA_URL", "http://localhost:11434") + "/api/generate", body,
                                     {"Content-Type": "application/json"})
        try:
            return json.loads(urllib.request.urlopen(req, timeout=900).read())["response"].strip()
        except OSError:
            raise NeedsModel("Ollama is not running. Start Ollama and run:  ollama pull qwen2.5:7b")
    if p == "anthropic":
        global _client
        import streamlit as st
        from src.security import rate_limited
        if rate_limited((st.session_state.get("user") or {}).get("id", 0)):
            raise RuntimeError("Too many AI requests. Please wait a minute and try again.")
        if _client is None:
            from anthropic import Anthropic
            _client = Anthropic()
        msg = _client.messages.create(model=os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6"), max_tokens=max_tokens,
                                      messages=[{"role": "user", "content": prompt}])
        return "".join(b.text for b in msg.content if b.type == "text").strip()
    raise NeedsModel("This feature needs an AI model. Install Ollama (free) and set LLM_PROVIDER=ollama in .env "
                     "(see README). Summaries, insights, search and chat passages already work offline.")
