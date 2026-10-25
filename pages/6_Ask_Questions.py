from src.ui import setup
import json

import streamlit as st

from db.models import add_message, get_documents, get_messages, get_text, list_conversations, new_conversation
from src.auth import require_login
from src.language import LANGUAGES
from src.rag import answer, build_index

setup()
user = require_login()
st.title("💬 Chat With Documents")

docs = get_documents(user["id"])
if not docs:
    st.info("Upload documents first.")
    st.stop()

names = {d["id"]: d["filename"] for d in docs}
name2id = {v: k for k, v in names.items()}
if "cid_next" in st.session_state:
    st.session_state["cid_sel"] = st.session_state.pop("cid_next")
cmap = {0: "➕ New chat", **{c["id"]: c["title"][:50] for c in list_conversations(user["id"])}}
c1, c2 = st.columns(2)
cid = c1.selectbox("Saved chats", list(cmap), format_func=cmap.get, key="cid_sel")
lang = c2.selectbox("Answer language", list(LANGUAGES.values()))
chosen = st.multiselect("Search in", list(names), format_func=names.get, default=list(names))
if not chosen:
    st.stop()

if st.session_state.get("loaded_cid") != cid:
    st.session_state["chat"] = [{"role": m["role"], "text": m["content"], "sources": json.loads(m["sources"] or "[]")}
                                for m in get_messages(cid)] if cid else []
    st.session_state["loaded_cid"] = cid
key = tuple(sorted(chosen))
if st.session_state.get("rag_key") != key:
    st.session_state["rag_index"] = build_index({names[i]: get_text(i) for i in chosen})
    st.session_state["rag_key"] = key

for mi, m in enumerate(st.session_state["chat"]):
    with st.chat_message(m["role"]):
        st.write(m["text"])
        if m.get("sources"):
            with st.expander("Sources"):
                for j, (n, pg, ch) in enumerate(m["sources"]):
                    st.caption(f"**{n}**{' · page ' + str(pg) if pg else ''}: {ch[:300]}...")
                    if name2id.get(n) and st.button("📖 Open page", key=f"o{cid}_{mi}_{j}"):
                        st.session_state["view"] = (name2id[n], pg or 1, ch)
                        st.switch_page("pages/16_Document_Viewer.py")

if q := st.chat_input("Ask a question about your documents"):
    if not cid:
        cid = new_conversation(user["id"], q[:60])
        st.session_state["cid_next"] = cid
        st.session_state["loaded_cid"] = cid
    with st.spinner("Thinking..."):
        reply, hits = answer(st.session_state["rag_index"], q, lang)
    src = [list(h) for h in hits]
    add_message(cid, "user", q)
    add_message(cid, "assistant", reply, json.dumps(src))
    st.session_state["chat"] += [{"role": "user", "text": q}, {"role": "assistant", "text": reply, "sources": src}]
    st.rerun()
