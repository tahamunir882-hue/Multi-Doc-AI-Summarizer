from src.ui import setup
import streamlit as st

from db.models import PLANS, add_document, add_summary, daily_count, get_setting, project_labels, save_text, set_tags
from src.ai_tools import auto_tags, fetch_url, send_webhook
from src.auth import require_login
from src.extractor import SUPPORTED, extract_text
from src.security import audit, validate_file
from src.language import LANGUAGES, detect_language, language_name
from src.summarizer import MODE_LABELS, summarize_combined, summarize_document
from src.translator import t

setup()
user = require_login()
st.title(t("upload_title"))

TONES = ["Default", "Professional", "Friendly", "Very simple", "Academic", "Persuasive", "Humorous"]
pmap = {0: "— No project —", **project_labels(user["id"])}
files = st.file_uploader("PDF, DOCX, PPTX, TXT, CSV, XLSX, images, audio (MP3/WAV/M4A) or video (MP4). Select many files.",
                         type=SUPPORTED, accept_multiple_files=True)
url = st.text_input("🔗 Or paste a web link (URL)")
c1, c2, c3, c4 = st.columns(4)
pid = c1.selectbox("Project", list(pmap), format_func=pmap.get)
mode = c2.selectbox(t("summary_length"), list(MODE_LABELS), index=1, format_func=MODE_LABELS.get)
out_choice = c3.selectbox(t("summary_language"), ["same"] + list(LANGUAGES),
                          format_func=lambda c: t("same_as_doc") if c == "same" else LANGUAGES[c])
tone = c4.selectbox("Tone / persona", TONES)
tone = "" if tone == "Default" else tone

sources = [(f.name, f) for f in files] + ([(url.strip(), None)] if url.strip() else [])
plan = get_setting(user["id"], "plan", "free")
used, limit = daily_count(user["id"]), PLANS[plan]
st.caption(f"Plan: {plan.title()} · {used}/{limit if limit else 'unlimited'} documents today")
over = limit is not None and used + len(sources) > limit
if over and sources:
    st.error(f"Daily limit reached ({limit} documents per day on the {plan.title()} plan). Upgrade on the Plans page or try again tomorrow.")
if st.button(t("summarize"), type="primary", disabled=not sources or over):
    results, per_doc = [], {}
    hook = get_setting(user["id"], "webhook")
    bar = st.progress(0.0)
    for i, (name, f) in enumerate(sources):
        label = name[:60]
        with st.spinner(f"{label} ..."):
            try:
                data = None if f is None else f.read()
                if data is not None:
                    validate_file(name, data)
                text = fetch_url(name) if data is None else extract_text(name, data)
                if not text.strip():
                    st.warning(f"{label}: no text found.")
                    continue
                lang = detect_language(text)
                out_lang = language_name(lang if out_choice == "same" else out_choice)
                summary = summarize_document(text, out_lang, mode, tone)
                doc_id = add_document(user["id"], label, lang, len(text), pid or None)
                save_text(doc_id, text)
                audit(user["id"], "upload", label)
                add_summary(user["id"], doc_id, out_lang, mode, summary)
                set_tags(doc_id, ", ".join(auto_tags(text)))
                per_doc[label] = summary
                results.append({"name": label, "lang": language_name(lang), "summary": summary})
                if hook:
                    try:
                        send_webhook(hook, {"document": label, "language": out_lang, "summary": summary})
                    except Exception:
                        st.warning("Webhook failed (check the URL in Settings).")
            except Exception as e:
                st.error(f"{label}: {e}")
        bar.progress((i + 1) / len(sources))

    combined = None
    if len(per_doc) > 1:
        with st.spinner(t("combined")):
            out_lang = "English" if out_choice == "same" else LANGUAGES[out_choice]
            combined = summarize_combined(per_doc, out_lang)
            add_summary(user["id"], None, out_lang, mode, combined)

    st.session_state["results"] = {"docs": results, "combined": combined}
    if results:
        st.switch_page("pages/4_Summary_Results.py")
