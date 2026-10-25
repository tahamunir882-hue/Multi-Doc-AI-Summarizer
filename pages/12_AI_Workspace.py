from src.ui import setup
import streamlit as st

from db.models import get_documents, get_text
from src.ai_tools import audio_script, deep_research, make_audio, mind_map_dot
from src.auth import require_login
from src.language import LANGUAGES
from src.agents import orchestrate
from src.rag import build_index

setup()
user = require_login()
st.title("🧠 AI Workspace")

docs = get_documents(user["id"])
if not docs:
    st.info("Upload documents first.")
    st.stop()
names = {d["id"]: d["filename"] for d in docs}
chosen = st.multiselect("Documents", list(names), format_func=names.get, default=list(names)[:3])
lang = st.selectbox("Language", list(LANGUAGES.values()))
code = {v: k for k, v in LANGUAGES.items()}[lang]
texts = {names[i]: get_text(i) for i in chosen}
tab1, tab2, tab3, tab4 = st.tabs(["🔬 Deep Research", "🎙️ Audio Overview", "🗺️ Mind Map", "🤖 Agent mode"])

with tab1:
    topic = st.text_input("Research topic / question")
    if st.button("Run deep research", disabled=not (topic and chosen)):
        with st.spinner("Planning, searching and writing..."):
            report, found = deep_research(build_index(texts), topic, lang)
        st.markdown(report)
        with st.expander("Sub-questions investigated"):
            for q, a in found:
                st.markdown(f"**{q}**\n\n{a}")

with tab2:
    st.caption("Two AI hosts discuss your documents. Audio needs an internet connection.")
    if st.button("Generate podcast", disabled=not chosen):
        with st.spinner("Writing script..."):
            script = audio_script(texts, lang)
        st.text_area("Script", script, height=220)
        try:
            with st.spinner("Creating audio..."):
                st.audio(make_audio(script, code), format="audio/mp3")
        except Exception as e:
            st.error(f"Audio failed: {e}")

with tab3:
    if st.button("Create mind map", disabled=not chosen):
        with st.spinner("Drawing..."):
            dot = mind_map_dot("\n\n".join(texts.values())[:30000], lang)
        if dot:
            st.graphviz_chart(dot)
        else:
            st.warning("Could not draw the map, try again.")

with tab4:
    st.caption("An orchestrator picks specialist agents (Document, Research, Data, Conflict), then a Reasoning "
               "agent combines their work and a Citation agent checks the sources.")
    goal = st.text_input("Ask anything about the selected documents", key="agent_goal")
    if st.button("Run agents", disabled=not (goal and chosen)):
        with st.spinner("Agents are working..."):
            final, trace, cites = orchestrate(goal, texts, lang)
        for agent, note in trace:
            st.markdown(f"**{agent}** → {note}")
        st.divider()
        st.markdown(final)
        if cites:
            st.caption("Citations: " + " ".join(cites))
