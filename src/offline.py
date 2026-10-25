"""No-API engine: extractive summaries (TextRank), rule-based insights, keywords."""
import re
from collections import Counter

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

SENT = re.compile(r"(?<=[.!?۔।؟])\s+|\n+")
COUNTS = {"quick": 5, "standard": 10, "detailed": 20, "executive": 8, "academic": 10, "student": 8, "bullet": 8,
          "tldr": 2, "findings": 6, "actions": 6, "short": 4, "medium": 8}
ACTION = re.compile(r"\b(should|must|need to|needs to|required|deadline|action|todo|please|ensure|submit|"
                    r"recommend\w*)\b|ضروری|چاہیے|ہوگا|करना|जरूरी", re.I)
RISK = re.compile(r"\b(risk\w*|penalt\w*|fine[sd]?|delay\w*|loss|fail\w*|breach|violation|terminat\w*|liabilit\w*|"
                  r"warning|danger\w*)\b|خطرہ|جرمانہ|नुकसान|जोखिम", re.I)
MONTH = r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?"
DATE = re.compile(rf"\b\d{{1,2}}[/-]\d{{1,2}}[/-]\d{{2,4}}\b|\b\d{{4}}-\d{{2}}-\d{{2}}\b|\b{MONTH} \d{{1,2}}(?:, \d{{4}})?\b|\b\d{{1,2}} {MONTH} \d{{4}}\b")
NUM = re.compile(r"[$€£₹]\s?\d[\d,.]*(?:\s?(?:million|billion|k|m))?|\b\d[\d,.]*\s?%|\b\d{1,3}(?:,\d{3})+\b")
ORG = re.compile(r"\b(?:[A-Z][\w&]+ ){1,4}(?:Inc|Ltd|LLC|Corp|Corporation|University|Company|Bank|Institute|Foundation|Ministry|Department)\b")
PERSON = re.compile(r"\b[A-Z][a-z]+(?: [A-Z][a-z]+){1,2}\b")
STOP = set("this that with from have were been their there which would about these those than then them they your "
           "will also into more some such only other when what where while shall could should".split())
NOTE = "\n\n_(Offline mode: key sentences are picked from the document, in its own language.)_"


def sentences(text):
    return [s.strip() for s in SENT.split(text.replace("\f", "\n")) if len(s.strip()) >= 25]


def _rank(sents):
    if len(sents) <= 1:
        return list(range(len(sents)))
    try:
        m = TfidfVectorizer(token_pattern=r"(?u)\b\w\w+\b").fit_transform(sents)
    except ValueError:
        return list(range(len(sents)))
    sim = (m @ m.T).toarray()
    np.fill_diagonal(sim, 0)
    sim = sim / np.where(sim.sum(1) == 0, 1, sim.sum(1))[:, None]
    score = np.ones(len(sents)) / len(sents)
    for _ in range(30):
        score = 0.15 / len(sents) + 0.85 * sim.T @ score
    return list(np.argsort(-score))


def top_sentences(text, n):
    s = sentences(text)
    return [s[i] for i in sorted(_rank(s)[:n])]


def extractive_summary(text, mode="standard"):
    s = sentences(text)
    if not s:
        return text.strip()[:600] or "(no text)"
    n = COUNTS.get(mode, 8)
    picks = [i for i, x in enumerate(s) if ACTION.search(x)][:n] if mode == "actions" else []
    picks = picks or sorted(_rank(s)[:n])
    body = [s[i] for i in picks]
    out = "\n".join("- " + x for x in body) if mode in ("bullet", "findings", "actions") else " ".join(body)
    return out + NOTE


def keywords(text, n=8):
    words = [w for w in re.findall(r"\w{4,}", text.lower()) if w not in STOP and not w.isdigit()]
    return [w for w, _ in Counter(words).most_common(n)]


def _uniq(items, n=15):
    return list(dict.fromkeys(i.strip() for i in items))[:n]


def simple_insights(text):
    t = text.replace("\f", "\n")
    s = sentences(t)
    orgs = _uniq(ORG.findall(t), 10)
    people = [p for p in _uniq([p for p, _ in Counter(PERSON.findall(t)).most_common(25)], 10)
              if not any(p in o for o in orgs)]
    return {"key_points": top_sentences(t, 5), "action_items": [x for x in s if ACTION.search(x)][:6],
            "dates": _uniq(DATE.findall(t)), "people": people, "organizations": orgs,
            "numbers": _uniq(NUM.findall(t)), "risks": [x for x in s if RISK.search(x)][:6]}


def compare_offline(summaries):
    kws = {n: keywords(s, 12) for n, s in summaries.items()}
    common = set.intersection(*[set(v) for v in kws.values()]) if kws else set()
    return {"common_themes": sorted(common) or ["No shared keywords found"],
            "differences": [f"{n}: " + ", ".join([w for w in v if w not in common][:6]) for n, v in kws.items()],
            "contradictions": [], "missing_information": ["Contradiction and gap detection need an AI model (see README: Ollama)."]}


def combined_overview(summaries):
    common = compare_offline(summaries)["common_themes"]
    lines = ["**Combined overview (offline mode)**", "", "Common keywords: " + ", ".join(common), ""]
    lines += [f"- **{n}**: " + " ".join(sentences(s.replace(NOTE, ""))[:2])[:300] for n, s in summaries.items()]
    return "\n".join(lines)
