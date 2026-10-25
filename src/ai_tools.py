import html as htmllib
import io
import json
import re
import urllib.request
from difflib import HtmlDiff

from src.rag import answer
from src.summarizer import _ask, summarize_document


def _brief(text, lang, n=12000):
    t = text.replace("\f", "\n")
    return t if len(t) <= n else summarize_document(t, lang, "detailed")


def auto_tags(text, lang="English"):
    from src.llm import provider
    if provider() == "offline":
        from src.offline import keywords
        return keywords(text, 5)
    raw = _ask("Give 3-6 short topic tags for this document. Reply with ONLY a JSON list of strings.\n\n"
               + text.replace("\f", "\n")[:4000], 150)
    m = re.search(r"\[.*\]", raw, re.S)
    try:
        return [str(x) for x in json.loads(m.group(0))][:6]
    except Exception:
        return []


def mind_map_dot(text, lang="English"):
    raw = _ask("Create a concept mind map of this content as Graphviz DOT code: start with "
               "'digraph G { rankdir=LR; node [shape=box, style=\"rounded,filled\", fillcolor=\"#f5d0fe\"];', "
               "one central node, 3-6 branches, max 25 nodes, short labels in " + lang +
               ". Reply with ONLY the DOT code.\n\n" + _brief(text, lang), 1500)
    m = re.search(r"digraph.*\}", raw, re.S)
    return m.group(0) if m else ""


def audio_script(texts, lang, lines=14):
    body = "\n\n".join(f"### {n}\n{_brief(t, lang, 8000)}" for n, t in texts.items())
    return _ask(f"Write a lively podcast conversation between two hosts, Alex (A) and Sam (B), explaining the key "
                f"ideas of these documents in {lang}. Exactly {lines} lines, each starting with 'A:' or 'B:', short "
                f"sentences, no stage directions, no markdown. Use only facts from the documents.\n\n{body}", 2000)


def make_audio(script, lang_code):
    from gtts import gTTS                     # needs internet
    code = {"zh-cn": "zh-CN", "roman-ur": "en"}.get(lang_code, lang_code)
    buf = io.BytesIO()
    for line in script.splitlines():
        m = re.match(r"\s*([AB])\s*:\s*(.+)", line)
        if m:
            gTTS(m.group(2), lang=code, tld="com" if m.group(1) == "A" else "co.uk").write_to_fp(buf)
    return buf.getvalue()


def deep_research(index, topic, lang):
    raw = _ask("Break this research topic into 4 specific sub-questions answerable from documents. "
               "Reply with ONLY a JSON list of strings.\nTopic: " + topic, 300)
    m = re.search(r"\[.*\]", raw, re.S)
    try:
        subs = json.loads(m.group(0))[:4]
    except Exception:
        subs = [topic]
    found = []
    for q in subs:
        a, hits = answer(index, q, lang)
        found.append((q, a))
    notes = "\n\n".join(f"Q: {q}\nA: {a}" for q, a in found)
    report = _ask(f"Write a research report in {lang} on '{topic}' from these findings: Executive summary, Key "
                  f"findings, Evidence (keep the [file, p.N] citations), Gaps / what is missing. Use only the "
                  f"findings.\n\n{notes}", 2500)
    return report, found


def diff_matrix(na, ta, nb, tb, lang):
    return _ask(f"Compare these two documents/versions in {lang}. Output a markdown table with columns "
                f"Aspect | {na} | {nb} | Difference (topics, numbers, dates, terms, tone), then 3 bullets on the "
                f"most important changes. Use only the text.\n\n### {na}\n{_brief(ta, lang, 9000)}\n\n"
                f"### {nb}\n{_brief(tb, lang, 9000)}", 2500)


def html_diff(ta, tb):
    a, b = ta.replace("\f", "\n").splitlines()[:400], tb.replace("\f", "\n").splitlines()[:400]
    return HtmlDiff(wrapcolumn=60).make_table(a, b, "Document A", "Document B", context=True, numlines=1)


def fetch_url(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    page = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "ignore")
    page = re.sub(r"(?is)<(script|style|noscript).*?</\1>", " ", page)
    text = htmllib.unescape(re.sub(r"(?s)<[^>]+>", "\n", page))
    return re.sub(r"\n\s*\n+", "\n\n", text).strip()


def send_webhook(url, payload):
    req = urllib.request.Request(url, json.dumps(payload).encode(), {"Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=10)


def find_contradictions(texts, lang):
    body = "\n\n".join(f"### {n}\n{_brief(t, lang, 9000)}" for n, t in texts.items())
    raw = _ask("Find claims that CONFLICT between these documents. Reply with ONLY a JSON list; each item: "
               '{"topic": "...", "claims": [{"document": "...", "claim": "..."}], "possible_reasons": ["..."]}. '
               "Possible reasons can be different datasets, methodology, metrics, time period or conditions. "
               "Do NOT decide which claim is true. Write in " + lang + ". Use [] if there are no conflicts.\n\n" + body, 2500)
    m = re.search(r"\[.*\]", raw, re.S)
    try:
        return json.loads(m.group(0)) if m else []
    except json.JSONDecodeError:
        return []


def send_to_notion(token, page_id, title, text):
    blocks = [{"object": "block", "type": "paragraph",
               "paragraph": {"rich_text": [{"type": "text", "text": {"content": text[i:i + 1900]}}]}}
              for i in range(0, min(len(text), 60000), 1900)][:90]
    body = {"parent": {"page_id": page_id}, "children": blocks,
            "properties": {"title": {"title": [{"text": {"content": title[:100]}}]}}}
    req = urllib.request.Request("https://api.notion.com/v1/pages", json.dumps(body).encode(),
                                 {"Authorization": "Bearer " + token, "Notion-Version": "2022-06-28",
                                  "Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=20)
