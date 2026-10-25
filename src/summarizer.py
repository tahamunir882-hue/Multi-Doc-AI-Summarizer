from src.chunker import chunk_text
from src.llm import ask_llm, provider

LENGTHS = {
    "quick": "in 5-10 lines",
    "standard": "in 1-2 pages",
    "detailed": "as a full structured explanation with headings and bullet points (key points, dates, names, numbers, action items)",
    "executive": "as an executive summary for business readers: key metrics, risks, recommendations",
    "academic": "in academic style: problem, method, results, limitations",
    "student": "in simple, easy language for a student, explaining key terms",
    "bullet": "as bullet points containing only the important points",
    "tldr": "in 1-2 sentences (TL;DR)",
    "findings": "as a list of only the key findings",
    "actions": "as a list of only the action items (what, who, when if stated)",
    "short": "in 3-5 sentences", "medium": "in 2-3 short paragraphs",   # old history entries
}
MODE_LABELS = {
    "quick": "⚡ Quick (5-10 lines)", "standard": "📄 Standard (1-2 pages)", "detailed": "📚 Detailed",
    "executive": "🏢 Executive", "academic": "🎓 Academic", "student": "🧑‍🎓 Student (easy)",
    "bullet": "• Bullet points", "tldr": "TL;DR", "findings": "🔎 Key findings", "actions": "✅ Action items",
}


def _ask(prompt: str, max_tokens: int = 1500) -> str:
    return ask_llm(prompt, max_tokens)


def summarize_document(text: str, out_language: str, length: str = "medium", tone: str = "") -> str:
    if provider() == "offline":
        from src.offline import extractive_summary
        return extractive_summary(text, length)
    """Map-reduce: summarize each chunk, then summarize the summaries."""
    chunks = chunk_text(text)
    if len(chunks) == 1:
        source = chunks[0]
    else:
        partials = [_ask("Summarize this part of a document in 5-8 bullet points. "
                         "Keep names, dates and numbers.\n\n" + c, 800) for c in chunks]
        source = "\n\n".join(partials)
    return _ask(
        f"Summarize the following document {LENGTHS[length]}. "
        f"Write the summary in {out_language}{(', tone: ' + tone) if tone else ''}. Only use information from the text; "
        f"do not invent facts.\n\n{source}")


def summarize_combined(summaries: dict, out_language: str) -> str:
    if provider() == "offline":
        from src.offline import combined_overview
        return combined_overview(summaries)
    joined = "\n\n".join(f"### {name}\n{s}" for name, s in summaries.items())
    return _ask(
        f"Below are summaries of several documents. Write a combined overview in {out_language}: "
        f"1) overall summary, 2) common themes, 3) differences or contradictions between documents. "
        f"Mention document names where relevant.\n\n{joined}")
