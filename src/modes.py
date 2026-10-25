from src.summarizer import _ask, summarize_document

MODES = {
    "🎓 Student": {
        "Important topics": "List the important topics with a one-line explanation each.",
        "Short & long questions": "Write 10 short-answer and 5 long-answer exam questions with model answers.",
        "MCQs (20)": "Create 20 multiple-choice questions (4 options each) and give an answer key.",
        "Definitions": "List all key terms with clear definitions.",
        "Easy explanation": "Explain the content in very simple language with examples.",
        "Exam important questions": "List the most likely exam questions and briefly how to answer each.",
        "Viva questions": "Write 15 likely viva (oral exam) questions with short model answers.",
        "Flashcards": "Create 20 flashcards in the format 'Q: ... / A: ...'.",
    },
    "📖 Research": {
        "Paper breakdown": "For each document give: Title, Authors, Abstract, Research problem, Objectives, Methodology, "
                           "Dataset, Algorithms, Results, Accuracy/metrics, Limitations, Research gap, Future work, References.",
        "Research gaps": "Identify the research gaps across the documents: what is missing, untested or contradictory, and suggest future research directions.",
        "Literature review": "Write a literature review across ALL documents: themes, agreements, gaps, "
                             "and how each paper contributes. Cite document names.",
    },
    "🏢 Business": {
        "Executive 1-pager": "Write a one-page executive brief: purpose, key facts, decisions needed, next steps.",
        "SWOT analysis": "Create a SWOT analysis (Strengths, Weaknesses, Opportunities, Threats) as a table-like list.",
        "KPI & financial parser": "Extract every KPI and financial figure (revenue, cost, profit, growth, dates) into a markdown table with the source document.",
        "Business report": "Produce: Executive summary, Key metrics, Financial highlights, Risks, "
                           "Opportunities, Problems, Recommendations, Action items.",
    },
    "⚖️ Contract": {
        "Red flags & penalty risks": "List red flags, one-sided clauses, penalties, auto-renewals and hidden risks. Rate each High/Medium/Low and explain why.",
        "Plain-English translation": "Rewrite the important clauses in plain simple language anyone can understand. Keep clause numbers.",
        "Contract analysis": "Extract: Parties, Agreement duration, Payment terms, Obligations, Termination, "
                             "Penalties, Risks, Important clauses. Quote clause numbers if present.",
    },
}


def run_task(texts: dict, instruction: str, lang: str, tone: str = "") -> str:
    budget = 40000 // max(len(texts), 1)
    parts = []
    for name, t in texts.items():
        t = t.replace("\f", "\n")
        if len(t) > budget:                       # long document -> condense first
            t = summarize_document(t, lang, "detailed")
        parts.append(f"### {name}\n{t}")
    return _ask(f"{instruction}\nWrite in {lang}{(', tone: ' + tone) if tone else ''}. Use ONLY the documents below; write 'Not found' "
                "for anything missing. Do not invent facts.\n\n" + "\n\n".join(parts), 3500)
