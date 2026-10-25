import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.chunker import chunk_text
from src.summarizer import _ask

_model, _tried = None, False


def _dense():
    """Optional multilingual embeddings (pip install sentence-transformers)."""
    global _model, _tried
    if not _tried:
        _tried = True
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        except Exception:
            _model = None
    return _model


def build_index(texts: dict) -> dict:
    """Hybrid index: char n-gram vectors + word keyword (TF-IDF) + dense embeddings when available."""
    items = []
    for name, t in texts.items():
        pages = t.split("\f")
        for no, page in enumerate(pages, 1):
            for ch in chunk_text(page, 1200):
                items.append((name, no if len(pages) > 1 else None, ch))
    idx = {"items": items, "char": None, "word": None, "dense": None}
    if not items:
        return idx
    docs = [c for _, _, c in items]
    idx["char"] = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), sublinear_tf=True).fit(docs)
    idx["char_m"] = idx["char"].transform(docs)
    idx["word"] = TfidfVectorizer(token_pattern=r"(?u)\b\w+\b", sublinear_tf=True).fit(docs)
    idx["word_m"] = idx["word"].transform(docs)
    if m := _dense():
        idx["dense"] = m.encode(docs, normalize_embeddings=True)
    return idx


def search(index: dict, question: str, k: int = 6, files=None):
    """Reciprocal-rank fusion of vector, keyword and dense rankings, with optional file (metadata) filter."""
    if not index["items"]:
        return []
    rankers = [cosine_similarity(index["char"].transform([question]), index["char_m"])[0],
               cosine_similarity(index["word"].transform([question]), index["word_m"])[0]]
    if index["dense"] is not None:
        rankers.append(index["dense"] @ _dense().encode([question], normalize_embeddings=True)[0])
    fused = np.zeros(len(index["items"]))
    for sc in rankers:
        for rank, i in enumerate(np.argsort(-sc)[:50]):
            if sc[i] > 0:
                fused[i] += 1 / (60 + rank)
    if files:
        fused = np.where([it[0] in files for it in index["items"]], fused, 0)
    return [index["items"][i] for i in np.argsort(-fused)[:k] if fused[i] > 0]


def answer(index: dict, question: str, out_language: str = "English", files=None):
    hits = search(index, question, files=files)
    if not hits:
        return "No relevant information found in the documents.", []
    from src.llm import provider
    if provider() == "offline":
        from src.offline import sentences
        cand = [(n, p, x) for n, p, c in hits for x in sentences(c)] or [(n, p, c[:300]) for n, p, c in hits]
        sc = cosine_similarity(index["char"].transform([question]), index["char"].transform([x for _, _, x in cand]))[0]
        best, seen = [], set()
        for i in np.argsort(-sc):
            if cand[i][2] not in seen and len(best) < 4:
                seen.add(cand[i][2])
                best.append(cand[i])
        return "Here is what your documents say (offline mode, no AI model):\n\n" + "\n".join(
            f"- {x} **[{n}{', p.' + str(p) if p else ''}]**" for n, p, x in best), hits
    context = "\n\n".join(f"[{n}{', p.' + str(p) if p else ''}] {c}" for n, p, c in hits)
    reply = _ask(
        f"Answer the question using ONLY the excerpts below. Answer in {out_language}. "
        "After every fact cite the source exactly like [file, p.N] (or [file] if no page). "
        f"If the answer is not in the excerpts, say so.\n\nEXCERPTS:\n{context}\n\nQUESTION: {question}", 1200)
    return reply, hits
