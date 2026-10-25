import json
import os

import streamlit as st

UI_LANGS = {"en": "English", "ur": "اردو", "hi": "हिन्दी"}
_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "locales")


@st.cache_data
def _load(code: str) -> dict:
    with open(os.path.join(_DIR, f"{code}.json"), encoding="utf-8") as f:
        return json.load(f)


def t(key: str) -> str:
    code = st.session_state.get("ui_lang", "en")
    return _load(code).get(key) or _load("en").get(key, key)


def language_selector():
    """Sidebar UI-language switcher + RTL for Urdu. Call on every page."""
    code = st.sidebar.selectbox(
        "Language / زبان", list(UI_LANGS), format_func=UI_LANGS.get,
        index=list(UI_LANGS).index(st.session_state.get("ui_lang", "en")))
    st.session_state["ui_lang"] = code
    if code == "ur":
        st.markdown("<style>.stApp{direction:rtl;text-align:right;}</style>", unsafe_allow_html=True)
