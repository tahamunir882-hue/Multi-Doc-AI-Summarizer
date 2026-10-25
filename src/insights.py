import json
import re

from src.chunker import chunk_text
from src.summarizer import _ask

FIELDS = ["key_points", "action_items", "dates", "people", "organizations", "numbers", "risks"]


def _parse(raw: str) -> dict:
    m = re.search(r"\{.*\}", raw, re.S)
    try:
        return json.loads(m.group(0)) if m else {}
    except json.JSONDecodeError:
        return {}


def extract_insights(text: str, out_language: str = "English") -> dict:
    from src.llm import provider
    if provider() == "offline":
        from src.offline import simple_insights
        return simple_insights(text)
    """Run on up to 6 chunks, merge and de-duplicate."""
    merged = {f: [] for f in FIELDS}
    for chunk in chunk_text(text, 12000)[:6]:
        raw = _ask(
            "Extract insights from the text. Reply with ONLY a JSON object with these keys, "
            f"each a list of short strings written in {out_language}: {', '.join(FIELDS)}. "
            "key_points: main ideas; action_items: tasks/decisions needed; dates: every date or "
            "deadline with its context; people; organizations; numbers: important figures with "
            "meaning; risks: problems, risks or red flags. Use ONLY facts in the text; "
            "use [] if nothing found.\n\nTEXT:\n" + chunk, 1500)
        data = _parse(raw)
        for f in FIELDS:
            for item in data.get(f, []):
                if isinstance(item, str) and item not in merged[f]:
                    merged[f].append(item)
    return merged
