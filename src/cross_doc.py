import json
import re

from src.summarizer import _ask

KEYS = ("common_themes", "differences", "contradictions", "missing_information")


def compare_documents(summaries: dict, out_language: str = "English") -> dict:
    from src.llm import provider
    if provider() == "offline":
        from src.offline import compare_offline
        return compare_offline(summaries)
    joined = "\n\n".join(f"### {n}\n{s}" for n, s in summaries.items())
    raw = _ask(
        f"Compare these document summaries. Reply with ONLY a JSON object with keys {', '.join(KEYS)} "
        f"(each a list of short strings in {out_language}; mention document names; use [] if none). "
        "missing_information: important topics a reader would expect but the documents do not cover. "
        "Do not invent facts.\n\n" + joined, 1500)
    m = re.search(r"\{.*\}", raw, re.S)
    try:
        data = json.loads(m.group(0)) if m else {}
    except json.JSONDecodeError:
        data = {}
    return {k: data.get(k, []) for k in KEYS}
