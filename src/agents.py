import json
import re

from src.ai_tools import deep_research, find_contradictions
from src.rag import answer, build_index
from src.summarizer import _ask, summarize_document


def orchestrate(question, texts, lang):
    """Orchestrator -> specialist agents -> Reasoning agent -> Citation agent."""
    raw = _ask('You are an orchestrator. Choose the agents needed for the request: "document" (summarize each '
               'document), "research" (multi-step evidence search), "data" (numbers, tables, statistics), '
               '"conflict" (find contradictions between documents). Reply ONLY with a JSON list of agent names.\n'
               "Request: " + question, 100)
    m = re.search(r"\[.*\]", raw, re.S)
    try:
        plan = [a for a in json.loads(m.group(0)) if a in ("document", "research", "data", "conflict")]
    except Exception:
        plan = []
    plan = plan or ["research"]
    trace, ctx, index = [("Orchestrator", "Plan: " + " → ".join(plan))], [], build_index(texts)
    if "document" in plan:
        s = {n: summarize_document(t, lang, "quick") for n, t in texts.items()}
        ctx.append("DOCUMENT AGENT\n" + "\n".join(f"{n}: {v}" for n, v in s.items()))
        trace.append(("Document Agent", f"Summarised {len(s)} document(s)"))
    if "research" in plan:
        report, found = deep_research(index, question, lang)
        ctx.append("RESEARCH AGENT\n" + report)
        trace.append(("Research Agent", f"Investigated {len(found)} sub-question(s)"))
    if "data" in plan:
        a, _ = answer(index, question + " numbers statistics totals figures", lang)
        ctx.append("DATA AGENT\n" + a)
        trace.append(("Data Agent", "Extracted figures and statistics"))
    if "conflict" in plan and len(texts) > 1:
        c = find_contradictions(texts, lang)
        ctx.append("CONFLICT AGENT\n" + json.dumps(c, ensure_ascii=False))
        trace.append(("Conflict Agent", f"{len(c)} conflict(s) found"))
    final = _ask(f"You are the reasoning agent. Answer the request in {lang} using ONLY the agent outputs below. "
                 "Keep the [file, p.N] citations. If sources disagree, show both sides instead of choosing.\n"
                 f"Request: {question}\n\n" + "\n\n".join(ctx), 2000)
    trace.append(("Reasoning Agent", "Combined the findings"))
    cites = sorted(set(re.findall(r"\[[^\[\]]+\]", final)))
    trace.append(("Citation Agent", f"{len(cites)} distinct citation(s) listed"))
    return final, trace, cites
