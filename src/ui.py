import html

import streamlit as st

from src.translator import language_selector

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
html, body, .stApp, [class*="css"] { font-family: 'Poppins', sans-serif; }
.stApp {
  background:
    radial-gradient(1000px 520px at 88% -8%, rgba(217,70,239,.38), transparent 60%),
    radial-gradient(800px 480px at -8% 12%, rgba(124,58,237,.38), transparent 60%),
    #0b0614;
}
header[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 2.2rem; max-width: 1180px; }
[data-testid="stSidebar"] { background: rgba(18,8,32,.94); border-right: 1px solid rgba(217,70,239,.25); }
h1 { background: linear-gradient(90deg,#fff,#f0abfc 55%,#c084fc); -webkit-background-clip: text;
     -webkit-text-fill-color: transparent; font-weight: 700 !important; }
h2, h3 { color: #f5d0fe !important; }

/* buttons + page links */
.stButton > button, .stDownloadButton > button, [data-testid="stPageLink-NavLink"] {
  background: linear-gradient(90deg,#7c3aed,#d946ef); color: #fff !important; border: none;
  border-radius: 999px; padding: .55rem 1.4rem; font-weight: 600;
  box-shadow: 0 6px 24px rgba(217,70,239,.35); transition: transform .15s, box-shadow .15s;
}
.stButton > button:hover, .stDownloadButton > button:hover, [data-testid="stPageLink-NavLink"]:hover {
  transform: translateY(-2px); box-shadow: 0 10px 32px rgba(217,70,239,.55); color: #fff !important; }
.stButton > button:disabled { opacity: .45; }

/* inputs */
.stTextInput input, .stTextArea textarea, [data-baseweb="select"] > div {
  background: rgba(255,255,255,.06) !important; border: 1px solid rgba(217,70,239,.3) !important;
  border-radius: 12px !important; color: #fff !important; }
button[data-baseweb="tab"] { font-weight: 600; }
[data-testid="stFileUploaderDropzone"] { background: rgba(255,255,255,.04);
  border: 2px dashed rgba(217,70,239,.55); border-radius: 18px; }
[data-testid="stExpander"], [data-testid="stMetric"] {
  background: rgba(255,255,255,.05); border: 1px solid rgba(217,70,239,.25);
  border-radius: 16px; backdrop-filter: blur(8px); }
[data-testid="stMetric"] { padding: 14px 18px; }
[data-testid="stMetricValue"] { color: #f0abfc; }

/* landing page */
.hero { display: flex; flex-wrap: wrap; align-items: center; gap: 32px; margin: 8px 0 28px; }
.hero-l { flex: 1 1 420px; } .hero-r { flex: 1 1 320px; display: flex; justify-content: center; }
.badge { display: inline-block; padding: 6px 16px; border-radius: 999px; font-size: .85rem;
  background: rgba(217,70,239,.15); border: 1px solid rgba(217,70,239,.5); color: #f5d0fe; margin-bottom: 18px; }
.h-title { font-size: 3.1rem; line-height: 1.12; font-weight: 700; color: #fff; }
.h-title span { background: linear-gradient(90deg,#c084fc,#f0abfc,#e879f9); -webkit-background-clip: text;
  -webkit-text-fill-color: transparent; }
.h-sub { margin-top: 16px; font-size: 1.1rem; color: #d8b4fe; max-width: 520px; }
.orb { position: relative; width: 330px; height: 330px; }
.orb .core { position: absolute; inset: 95px; border-radius: 50%; display: flex; align-items: center;
  justify-content: center; font-size: 2.6rem; font-weight: 700; color: #fff;
  background: radial-gradient(circle at 30% 30%, #f0abfc, #a21caf 60%, #4c1d95);
  box-shadow: 0 0 80px rgba(217,70,239,.7); animation: pulse 3s ease-in-out infinite; }
.orb .ring { position: absolute; border-radius: 50%; border: 1px dashed rgba(240,171,252,.5); animation: spin 18s linear infinite; }
.orb .r1 { inset: 40px; } .orb .r2 { inset: 0; animation-duration: 28s; animation-direction: reverse; }
.orb .doc { position: absolute; padding: 8px 14px; border-radius: 12px; font-size: .85rem; font-weight: 600;
  background: rgba(21,10,36,.9); border: 1px solid rgba(217,70,239,.6); color: #fff;
  box-shadow: 0 6px 20px rgba(0,0,0,.4); animation: float 4s ease-in-out infinite; }
.orb .d1 { top: 10px; left: 20px; } .orb .d2 { top: 60px; right: 0; animation-delay: 1s; }
.orb .d3 { bottom: 20px; left: 40px; animation-delay: 2s; } .orb .d4 { bottom: 70px; right: 10px; animation-delay: 1.5s; }
@keyframes spin { to { transform: rotate(360deg); } }
@keyframes float { 50% { transform: translateY(-10px); } }
@keyframes pulse { 50% { box-shadow: 0 0 120px rgba(217,70,239,.95); } }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 18px; margin: 14px 0 30px; }
.card { background: rgba(255,255,255,.05); border: 1px solid rgba(217,70,239,.25); border-radius: 18px;
  padding: 22px; backdrop-filter: blur(8px); transition: transform .2s, border-color .2s, box-shadow .2s; }
.card:hover { transform: translateY(-6px); border-color: #e879f9; box-shadow: 0 14px 40px rgba(217,70,239,.25); }
.card .ic { font-size: 1.9rem; width: 54px; height: 54px; display: flex; align-items: center; justify-content: center;
  border-radius: 14px; background: linear-gradient(135deg,#7c3aed,#d946ef); margin-bottom: 14px; }
.card .ct { font-weight: 600; font-size: 1.05rem; color: #fff; margin-bottom: 6px; }
.card .cx { color: #d8b4fe; font-size: .92rem; }
.stat { text-align: center; padding: 20px 10px; border-radius: 18px; background: linear-gradient(160deg,rgba(124,58,237,.35),rgba(217,70,239,.18));
  border: 1px solid rgba(217,70,239,.35); }
.stat .sn { font-size: 2.4rem; font-weight: 700; color: #fff; } .stat .sl { color: #e9d5ff; font-size: .9rem; }
.step .num { font-size: 1.1rem; font-weight: 700; color: #fff; width: 38px; height: 38px; border-radius: 50%;
  background: linear-gradient(135deg,#7c3aed,#d946ef); display: flex; align-items: center; justify-content: center; margin-bottom: 10px; }
.sec-title { font-size: 1.7rem; font-weight: 700; color: #fff; margin: 26px 0 4px; }
.sec-sub { color: #c4b5fd; margin-bottom: 6px; }
[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] { background: transparent; box-shadow: none; border-radius: 10px; padding: .3rem .7rem; font-weight: 500; color: #e9d5ff !important; }
[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"]:hover { background: rgba(217,70,239,.2); transform: none; box-shadow: none; }
[data-testid="stSidebar"] { background: linear-gradient(180deg,#160b2b 0%,#0b0614 100%); }
[data-testid="stSidebar"] > div:first-child { padding-top: .5rem; }
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: .08rem; }
[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] { font-size: .9rem; border-left: 3px solid transparent; }
[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"][aria-current="page"] { background: linear-gradient(90deg,rgba(124,58,237,.55),rgba(217,70,239,.3)); border-left: 3px solid #f0abfc; color: #fff !important; }
[data-testid="stSidebar"] .stButton > button { background: rgba(255,255,255,.07); box-shadow: none; border: 1px solid rgba(217,70,239,.3); font-weight: 500; }
.sb-logo { display: flex; gap: 12px; align-items: center; padding: 6px 4px 14px; }
.sb-ic { width: 42px; height: 42px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 1.4rem; background: linear-gradient(135deg,#7c3aed,#d946ef); box-shadow: 0 6px 18px rgba(217,70,239,.45); }
.sb-name { font-weight: 700; font-size: 1.1rem; color: #fff; } .sb-tag { font-size: .68rem; color: #c4b5fd; line-height: 1.25; }
.sb-user { display: flex; gap: 10px; align-items: center; background: rgba(255,255,255,.06); border: 1px solid rgba(217,70,239,.25); border-radius: 14px; padding: 10px 12px; margin-bottom: 6px; }
.sb-av { width: 36px; height: 36px; border-radius: 50%; background: linear-gradient(135deg,#d946ef,#7c3aed); display: flex; align-items: center; justify-content: center; font-weight: 700; color: #fff; }
.sb-un { font-weight: 600; color: #fff; font-size: .92rem; } .sb-plan { font-size: .72rem; color: #f0abfc; }
.sb-cap { font-size: .66rem; letter-spacing: .12em; text-transform: uppercase; color: #a78bfa; margin: 14px 6px 2px; font-weight: 600; }
.sb-sep { height: 1px; background: rgba(217,70,239,.2); margin: 12px 4px; } .sb-mode { font-size: .74rem; color: #a78bfa; margin: 2px 6px 8px; }
.foot { text-align: center; color: #a78bfa; font-size: .85rem; margin: 40px 0 10px; }
"""


def setup(title="Multi-Doc AI Summarizer"):
    """First call on every page: page config, theme CSS, language switcher."""
    st.set_page_config(page_title=title, page_icon="📄", layout="wide")
    st.markdown("<style>" + CSS + "</style>", unsafe_allow_html=True)
    _sidebar()


def hero():
    st.markdown(
        '<div class="hero"><div class="hero-l">'
        '<div class="badge">✨ AI · Documents · Insights</div>'
        '<div class="h-title">Universal <span>Multilingual Document Intelligence</span></div>'
        '<div class="h-sub">Upload 1 or 100 documents in different languages: summarize, compare, find contradictions '
        'and chat with page-level citations.</div></div>'
        '<div class="hero-r"><div class="orb"><div class="ring r1"></div><div class="ring r2"></div>'
        '<div class="doc d1">📄 PDF</div><div class="doc d2">📝 DOCX</div>'
        '<div class="doc d3">🖼 OCR</div><div class="doc d4">💬 Q&amp;A</div>'
        '<div class="core">AI</div></div></div></div>', unsafe_allow_html=True)


def stats(items):
    cols = st.columns(len(items))
    for col, (n, label) in zip(cols, items):
        col.markdown(f'<div class="stat"><div class="sn">{n}</div><div class="sl">{label}</div></div>',
                     unsafe_allow_html=True)


def section(title, sub=""):
    st.markdown(f'<div class="sec-title">{title}</div><div class="sec-sub">{sub}</div>', unsafe_allow_html=True)


def cards(items, step=False):
    html = '<div class="grid">'
    for i, (icon, title, text) in enumerate(items, 1):
        head = f'<div class="num">{i}</div>' if step else f'<div class="ic">{icon}</div>'
        html += f'<div class="card{" step" if step else ""}">{head}<div class="ct">{title}</div><div class="cx">{text}</div></div>'
    st.markdown(html + '</div>', unsafe_allow_html=True)


def footer():
    st.markdown('<div class="foot">Multi-Document AI Summarizer · Built with Streamlit &amp; Claude</div>',
                unsafe_allow_html=True)


import streamlit.components.v1 as components

NAV = [
    ("Home", [("app.py", "🏠 Home"), ("pages/2_Dashboard.py", "📊 Dashboard")]),
    ("Documents", [("pages/3_Upload_Documents.py", "⬆️ Upload"), ("pages/10_Projects.py", "📁 My Documents & Projects"),
                   ("pages/16_Document_Viewer.py", "📖 Document viewer"), ("pages/4_Summary_Results.py", "📄 Latest results"), ("pages/7_History.py", "🕘 History")]),
    ("AI Workspace", [("pages/12_AI_Workspace.py", "🧠 Research · Audio · Mind map"),
                      ("pages/9_Study_Modes.py", "🎯 Student · Business · Contract"),
                      ("pages/14_Reports.py", "📑 Report generator"), ("pages/15_Data_Analysis.py", "📈 Data analysis")]),
    ("Discovery", [("pages/6_Ask_Questions.py", "💬 Chat with documents"), ("pages/13_Compare.py", "📊 Compare documents"),
                   ("pages/17_Contradictions.py", "🚨 Contradictions"),
                   ("pages/5_Insights.py", "💡 Insights")]),
    ("System", [("pages/11_Settings.py", "⚙️ Settings & Privacy"), ("pages/18_Plans.py", "💎 Plans"), ("pages/8_About.py", "ℹ️ About")]),
]
KEY_JS = """<script>
const d = window.parent.document;
if (!window.parent.__ck) {
  window.parent.__ck = 1;
  d.addEventListener('keydown', e => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault();
      const i = d.querySelector('input[aria-label*="Quick search"]');
      if (i) i.focus();
    }
  });
}
</script>"""


def _sidebar():
    from src.llm import label
    st.markdown("<style>[data-testid='stSidebarNav']{display:none}</style>", unsafe_allow_html=True)
    user = st.session_state.get("user")
    with st.sidebar:
        st.markdown('<div class="sb-logo"><div class="sb-ic">📄</div><div><div class="sb-name">Universal AI</div>'
                    '<div class="sb-tag">Upload Anything. Understand Everything.</div></div></div>', unsafe_allow_html=True)
        if user:
            from db.models import get_setting
            plan = get_setting(user["id"], "plan", "free").title()
            st.markdown(f'<div class="sb-user"><div class="sb-av">{html.escape(user["name"][:1].upper())}</div><div>'
                        f'<div class="sb-un">{html.escape(user["name"])}</div><div class="sb-plan">{plan} plan</div></div></div>',
                        unsafe_allow_html=True)
        else:
            st.page_link("pages/1_Login.py", label="🔐 Login / Sign up")
        for group, links in NAV:
            st.markdown(f'<div class="sb-cap">{group}</div>', unsafe_allow_html=True)
            for path, text in links:
                st.page_link(path, label=text)
        st.markdown('<div class="sb-sep"></div>', unsafe_allow_html=True)
        q = st.text_input("🔎 Quick search (Ctrl+K)", key="qs")
        if q and user:
            from db.models import search_summaries
            for r in search_summaries(user["id"], q)[:5]:
                st.caption(f"📄 **{r['title']}**: {r['content'][:90]}...")
        st.markdown(f'<div class="sb-mode">🧠 AI mode: {label()}</div>', unsafe_allow_html=True)
        if user and st.button("🚪 Logout", key="sb_logout", use_container_width=True):
            from src.auth import logout
            logout()
            st.switch_page("app.py")
    language_selector()
    components.html(KEY_JS, height=0)
