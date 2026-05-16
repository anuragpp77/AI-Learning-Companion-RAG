"""
AI Study Companion — Redesigned UI
Warm cream + terracotta palette inspired by Mosey.AI
"""

import json
import re
import time
import os

import httpx
import plotly.graph_objects as go
import streamlit as st

BACKEND = os.getenv("BACKEND_URL", "http://localhost:8000")
TIMEOUT = 180

st.set_page_config(
    page_title="StudyMind AI",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600&family=DM+Sans:wght@300;400;500;600&display=swap');

/* ── Root palette ── */
:root {
    --cream:       #F5EDE2;
    --cream-deep:  #EDE0D0;
    --warm-white:  #FDFAF7;
    --terracotta:  #C4703A;
    --terra-light: #D4895A;
    --terra-deep:  #A3561F;
    --brown-dark:  #2C1A0E;
    --brown-mid:   #6B4C30;
    --brown-light: #9E7A58;
    --border:      #E2D4C0;
    --shadow:      rgba(44, 26, 14, 0.08);
    --shadow-md:   rgba(44, 26, 14, 0.14);
}

/* ── App shell ── */
html, body, [data-testid="stAppViewContainer"], .stApp {
    background-color: var(--cream) !important;
    font-family: 'DM Sans', sans-serif !important;
    color: var(--brown-dark) !important;
}

[data-testid="stAppViewContainer"] > .main {
    background-color: var(--cream) !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background-color: var(--warm-white) !important;
    border-right: 1px solid var(--border) !important;
    box-shadow: 2px 0 20px var(--shadow) !important;
}

[data-testid="stSidebar"] * {
    color: var(--brown-dark) !important;
}

[data-testid="stSidebar"] .stMarkdown h1,
[data-testid="stSidebar"] .stMarkdown h2,
[data-testid="stSidebar"] .stMarkdown h3 {
    font-family: 'Playfair Display', serif !important;
    color: var(--terracotta) !important;
}

/* ── Headings ── */
h1 {
    font-family: 'Playfair Display', serif !important;
    font-weight: 600 !important;
    color: var(--brown-dark) !important;
    letter-spacing: -0.5px !important;
}
h2, h3 {
    font-family: 'Playfair Display', serif !important;
    color: var(--brown-mid) !important;
}

/* ── Sidebar title block ── */
.sidebar-brand {
    padding: 1.2rem 0 0.4rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 1rem;
}
.sidebar-brand .brand-name {
    font-family: 'Playfair Display', serif;
    font-size: 1.5rem;
    font-weight: 600;
    color: var(--terracotta) !important;
    letter-spacing: -0.3px;
}
.sidebar-brand .brand-sub {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.72rem;
    color: var(--brown-light) !important;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-top: 2px;
}

/* ── Status badge ── */
.status-badge {
    background: var(--cream-deep);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 0.65rem 0.9rem;
    font-size: 0.8rem;
    line-height: 1.6;
    color: var(--brown-mid) !important;
    margin: 0.5rem 0 1rem;
}
.status-badge strong { color: var(--terracotta) !important; }

/* ── All buttons ── */
.stButton > button {
    background: var(--warm-white) !important;
    color: var(--brown-dark) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    padding: 0.5rem 1.1rem !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 1px 4px var(--shadow) !important;
}
.stButton > button:hover {
    background: var(--terracotta) !important;
    color: #fff !important;
    border-color: var(--terracotta) !important;
    box-shadow: 0 4px 12px var(--shadow-md) !important;
    transform: translateY(-1px) !important;
}

/* ── Primary-style action button (Process & Index) ── */
.stButton > button[kind="primary"],
div[data-testid="column"] .stButton > button {
    background: var(--terracotta) !important;
    color: #fff !important;
    border-color: var(--terracotta) !important;
}
div[data-testid="column"] .stButton > button:hover {
    background: var(--terra-deep) !important;
    border-color: var(--terra-deep) !important;
}

/* ── Text inputs & selectbox ── */
.stTextInput > div > div > input,
.stSelectbox > div > div {
    background-color: var(--warm-white) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: 12px !important;
    color: var(--brown-dark) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.9rem !important;
    box-shadow: 0 1px 6px var(--shadow) !important;
    transition: border-color 0.2s !important;
}
.stTextInput > div > div > input:focus {
    border-color: var(--terracotta) !important;
    box-shadow: 0 0 0 3px rgba(196, 112, 58, 0.12) !important;
}

/* ── Chat messages ── */
[data-testid="stChatMessage"] {
    background: var(--warm-white) !important;
    border: 1px solid var(--border) !important;
    border-radius: 16px !important;
    padding: 1rem 1.2rem !important;
    margin-bottom: 0.75rem !important;
    box-shadow: 0 2px 10px var(--shadow) !important;
}

[data-testid="stChatMessage"][data-testid*="user"] {
    background: var(--cream-deep) !important;
    border-color: var(--terracotta) !important;
}

/* ── Chat message text — force dark/black ── */
[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] span,
[data-testid="stChatMessage"] li,
[data-testid="stChatMessage"] ol,
[data-testid="stChatMessage"] ul,
[data-testid="stChatMessage"] h1,
[data-testid="stChatMessage"] h2,
[data-testid="stChatMessage"] h3,
[data-testid="stChatMessage"] h4,
[data-testid="stChatMessage"] strong,
[data-testid="stChatMessage"] em,
[data-testid="stChatMessage"] code,
[data-testid="stChatMessage"] .stMarkdown,
[data-testid="stChatMessage"] .stMarkdown * {
    color: #1A1008 !important;
}

/* ── Also fix the main content area markdown text ── */
.main [data-testid="stMarkdownContainer"] p,
.main [data-testid="stMarkdownContainer"] span,
.main [data-testid="stMarkdownContainer"] li,
.main [data-testid="stMarkdownContainer"] strong {
    color: var(--brown-dark) !important;
}

/* ── Info / success / warning ── */
.stAlert {
    border-radius: 12px !important;
    border: 1px solid var(--border) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.85rem !important;
}
div[data-testid="stAlert"][kind="info"] {
    background: rgba(196, 112, 58, 0.08) !important;
    border-color: rgba(196, 112, 58, 0.25) !important;
    color: var(--terra-deep) !important;
}
div[data-testid="stAlert"][kind="success"] {
    background: rgba(60, 140, 80, 0.07) !important;
}

/* ── Expander ── */
.streamlit-expanderHeader {
    background: var(--cream-deep) !important;
    border-radius: 10px !important;
    border: 1px solid var(--border) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.85rem !important;
    color: var(--brown-mid) !important;
}
.streamlit-expanderContent {
    background: var(--warm-white) !important;
    border: 1px solid var(--border) !important;
    border-top: none !important;
    border-radius: 0 0 10px 10px !important;
}

/* ── Divider ── */
hr {
    border-color: var(--border) !important;
    margin: 1rem 0 !important;
}

/* ── Metric cards ── */
[data-testid="stMetric"] {
    background: var(--warm-white) !important;
    border: 1px solid var(--border) !important;
    border-radius: 14px !important;
    padding: 1rem 1.2rem !important;
    box-shadow: 0 2px 8px var(--shadow) !important;
}
[data-testid="stMetricLabel"] {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.78rem !important;
    color: var(--brown-light) !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
}
[data-testid="stMetricValue"] {
    font-family: 'Playfair Display', serif !important;
    color: var(--terracotta) !important;
    font-size: 2rem !important;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    overflow: hidden !important;
}

/* ── Spinner ── */
.stSpinner > div {
    border-color: var(--terracotta) var(--border) var(--border) !important;
}

/* ── Custom page hero ── */
.page-hero {
    padding: 1.8rem 2rem 1.2rem;
    background: linear-gradient(135deg, var(--warm-white) 60%, var(--cream-deep));
    border-radius: 20px;
    border: 1px solid var(--border);
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 20px var(--shadow);
}
.page-hero .hero-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.8rem;
    font-weight: 600;
    color: var(--brown-dark);
    margin-bottom: 0.25rem;
}
.page-hero .hero-sub {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.88rem;
    color: var(--brown-light);
}

/* ── Follow-up chips ── */
.followup-wrap {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin: 0.75rem 0;
}
.followup-label {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.78rem;
    color: var(--brown-light);
    margin-bottom: 0.4rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

/* ── Nav buttons in sidebar ── */
[data-testid="stSidebar"] .stButton > button {
    text-align: left !important;
    justify-content: flex-start !important;
    padding: 0.6rem 1rem !important;
    width: 100% !important;
    border-radius: 10px !important;
    background: transparent !important;
    border-color: transparent !important;
    box-shadow: none !important;
    color: var(--brown-mid) !important;
    font-size: 0.88rem !important;
    font-weight: 400 !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: var(--cream-deep) !important;
    color: var(--terracotta) !important;
    border-color: transparent !important;
    box-shadow: none !important;
    transform: none !important;
}

/* ── Caption / small text ── */
.stCaption, .caption {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.78rem !important;
    color: var(--brown-light) !important;
}

/* ── Chat input footer bar (the dark strip at the bottom) ── */
[data-testid="stBottom"],
[data-testid="stBottom"] > div,
[data-testid="stBottom"] > div > div,
.stBottom,
.stBottom > div,
[data-testid="stChatInputContainer"],
[data-testid="stChatInputContainer"] > div,
div[class*="chatInputContainer"],
div[class*="stChatInput"] {
    background-color: var(--cream) !important;
    border-top: 1px solid var(--border) !important;
    box-shadow: none !important;
}

/* ── Chat input textarea itself ── */
[data-testid="stChatInput"] textarea,
[data-testid="stChatInputContainer"] textarea {
    background-color: var(--warm-white) !important;
    color: var(--brown-dark) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: 12px !important;
    caret-color: var(--terracotta) !important;
}
[data-testid="stChatInput"] textarea:focus,
[data-testid="stChatInputContainer"] textarea:focus {
    border-color: var(--terracotta) !important;
    box-shadow: 0 0 0 3px rgba(196,112,58,0.12) !important;
}

/* ── Chat send button ── */
[data-testid="stChatInputContainer"] button,
[data-testid="stChatInput"] button {
    background-color: var(--terracotta) !important;
    color: #fff !important;
    border-radius: 10px !important;
    border: none !important;
}
[data-testid="stChatInputContainer"] button:hover,
[data-testid="stChatInput"] button:hover {
    background-color: var(--terra-deep) !important;
}

/* ── File uploader — force white bg, remove dark overlay ── */
[data-testid="stFileUploader"],
[data-testid="stFileUploader"] > div,
[data-testid="stFileUploader"] section,
[data-testid="stFileUploader"] section > div,
[data-testid="stFileUploaderDropzone"],
[data-testid="stFileUploaderDropzone"] > div {
    background-color: var(--warm-white) !important;
    border: 1.5px dashed var(--border) !important;
    border-radius: 12px !important;
    color: var(--brown-mid) !important;
}
[data-testid="stFileUploader"] span,
[data-testid="stFileUploader"] p,
[data-testid="stFileUploader"] small {
    color: var(--brown-light) !important;
}
[data-testid="stFileUploaderDropzone"]:hover {
    border-color: var(--terracotta) !important;
    background-color: var(--cream-deep) !important;
}
/* Upload button inside the dropzone */
[data-testid="stFileUploaderDropzone"] button {
    background-color: var(--warm-white) !important;
    border: 1.5px solid var(--border) !important;
    color: var(--brown-dark) !important;
    border-radius: 8px !important;
}
[data-testid="stFileUploaderDropzone"] button:hover {
    background-color: var(--terracotta) !important;
    color: #fff !important;
    border-color: var(--terracotta) !important;
}

/* ── Radio buttons ── */
/* Unselected circle */
[data-testid="stRadio"] input[type="radio"] + div,
.stRadio [data-testid="stMarkdownContainer"] + div {
    border-color: var(--border) !important;
}
/* Selected circle fill */
[data-testid="stRadio"] label[data-baseweb="radio"] > div:first-child {
    border-color: var(--terracotta) !important;
    background-color: var(--terracotta) !important;
}
/* Radio label text */
[data-testid="stRadio"] label span {
    color: var(--brown-mid) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.88rem !important;
}
/* BaseWeb radio override */
[role="radio"] {
    border-color: var(--border) !important;
}
[role="radio"][aria-checked="true"] {
    background-color: var(--terracotta) !important;
    border-color: var(--terracotta) !important;
}

/* ── Selectbox dropdown panel & all options ── */
div[data-baseweb="popover"],
div[data-baseweb="popover"] > div,
div[data-baseweb="popover"] > div > div,
div[data-baseweb="popover"] > div > div > div,
div[data-baseweb="menu"],
div[data-baseweb="menu"] > ul,
div[data-baseweb="menu"] > div,
ul[role="listbox"],
ul[role="listbox"] > li,
li[role="option"],
li[role="option"] > div,
li[role="option"] > div > div,
li[role="option"] span {
    background-color: #FFFFFF !important;
    background: #FFFFFF !important;
    color: #1A1008 !important;
    border-color: #E2D4C0 !important;
}

/* Hover state */
li[role="option"]:hover,
li[role="option"]:hover > div,
li[role="option"]:hover span {
    background-color: #EDE0D0 !important;
    background: #EDE0D0 !important;
    color: #C4703A !important;
}

/* Selected / highlighted option */
li[aria-selected="true"],
li[aria-selected="true"] > div,
li[aria-selected="true"] span {
    background-color: #F5EDE2 !important;
    background: #F5EDE2 !important;
    color: #C4703A !important;
    font-weight: 600 !important;
}

/* Selectbox trigger box */
div[data-baseweb="select"] > div,
div[data-baseweb="select"] > div > div,
div[data-baseweb="select"] span,
[data-testid="stSelectbox"] > div > div {
    background-color: #FDFAF7 !important;
    color: #1A1008 !important;
    border-color: #E2D4C0 !important;
}

/* Dropdown arrow */
div[data-baseweb="select"] svg {
    fill: #9E7A58 !important;
    color: #9E7A58 !important;
}

/* ── Any remaining dark backgrounds ── */
div[class*="block-container"],
section[class*="main"] > div {
    background-color: transparent !important;
}

/* ── Tooltip / popover dark overrides ── */
div[data-baseweb="tooltip"],
div[data-baseweb="tooltip"] * {
    background-color: var(--brown-dark) !important;
    color: var(--warm-white) !important;
    border-radius: 8px !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--cream); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: var(--terracotta); }

/* ── Quiz cards ── */
.quiz-card {
    background: var(--warm-white);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 1rem;
    box-shadow: 0 2px 10px var(--shadow);
}

/* ── Plotly charts ── */
.js-plotly-plot .plotly {
    border-radius: 14px !important;
}

/* ── Section label ── */
.section-label {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--brown-light);
    margin-bottom: 0.4rem;
}

/* ── Upload success pill ── */
.stSuccess {
    background: rgba(60,140,80,0.07) !important;
    border: 1px solid rgba(60,140,80,0.2) !important;
    border-radius: 12px !important;
}
.stError {
    border-radius: 12px !important;
}
.stWarning {
    background: rgba(196,112,58,0.07) !important;
    border: 1px solid rgba(196,112,58,0.2) !important;
    border-radius: 12px !important;
    color: var(--terra-deep) !important;
}

/* ── Subheader ── */
.stSubheader {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.72rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
    color: var(--brown-light) !important;
    margin-bottom: 0.5rem !important;
}

/* Hide Streamlit branding */
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "messages"   not in st.session_state: st.session_state.messages   = []
if "followup"   not in st.session_state: st.session_state.followup   = []
if "quiz_state" not in st.session_state: st.session_state.quiz_state = {}
if "active_tab" not in st.session_state: st.session_state.active_tab = "chat"
if "kb_ready"   not in st.session_state: st.session_state.kb_ready   = False


# ── Helpers ───────────────────────────────────────────────────────────────────
def api_get(path):
    try:
        r = httpx.get(f"{BACKEND}{path}", timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API error: {e}")
        return None


def api_post(path, **kwargs):
    try:
        r = httpx.post(f"{BACKEND}{path}", timeout=TIMEOUT, **kwargs)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPStatusError as e:
        detail = e.response.json().get("detail", str(e))
        st.error(f"❌ {detail}")
        return None
    except Exception as e:
        st.error(f"❌ Connection error: {e}")
        return None


def check_health():
    data = api_get("/health")
    if data:
        st.session_state.kb_ready = data.get("kb_ready", False)
        return data
    return {}


def parse_mcqs(raw):
    questions = []
    blocks = re.split(r"\n(?=Q\d+:)", raw.strip())
    for block in blocks:
        lines = [l.strip() for l in block.strip().splitlines() if l.strip()]
        if not lines:
            continue
        q = {"question": "", "options": {}, "answer": "", "explanation": ""}
        for line in lines:
            if re.match(r"Q\d+:", line):
                q["question"] = re.sub(r"Q\d+:\s*", "", line)
            elif re.match(r"^[ABCD]\)", line):
                q["options"][line[0]] = line[3:].strip()
            elif line.lower().startswith("answer:"):
                q["answer"] = line.split(":", 1)[1].strip().upper()
            elif line.lower().startswith("explanation:"):
                q["explanation"] = line.split(":", 1)[1].strip()
        if q["question"] and q["options"]:
            questions.append(q)
    return questions


def _render_quiz(questions, prefix="q"):
    st.markdown('<div class="section-label">📝 Quiz</div>', unsafe_allow_html=True)
    for i, q in enumerate(questions):
        with st.container():
            st.markdown(f'<div class="quiz-card">', unsafe_allow_html=True)
            st.markdown(f"**Q{i+1}. {q['question']}**")
            key = f"{prefix}_q{i}"
            choice = st.radio(
                f"Q{i+1}",
                options=list(q["options"].keys()),
                format_func=lambda k, opts=q["options"]: f"{k})  {opts[k]}",
                key=key,
                label_visibility="collapsed",
            )
            check_key = f"{key}_checked"
            col_btn, _ = st.columns([1, 5])
            with col_btn:
                if st.button("Check", key=f"{key}_btn"):
                    st.session_state.quiz_state[check_key] = choice
            if st.session_state.quiz_state.get(check_key):
                submitted = st.session_state.quiz_state[check_key]
                correct = q.get("answer", "")
                if submitted == correct:
                    st.success(f"✅ Correct! {q.get('explanation', '')}")
                else:
                    st.error(f"❌ Incorrect. Correct answer: **{correct})**  \n{q.get('explanation', '')}")
            st.markdown('</div>', unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    # Brand
    st.markdown("""
    <div class="sidebar-brand">
        <div class="brand-name">StudyMind AI</div>
        <div class="brand-sub">Multi-Agent Learning Companion</div>
    </div>
    """, unsafe_allow_html=True)

    # Health / status
    health   = check_health()
    provider = health.get("llm_provider", "—")
    kb_status = "✅ Ready" if st.session_state.kb_ready else "⚠️ No documents yet"
    st.markdown(f"""
    <div class="status-badge">
        <strong>LLM</strong> {provider}<br>
        <strong>Knowledge Base</strong> {kb_status}
    </div>
    """, unsafe_allow_html=True)

    # Upload
    st.markdown('<div class="section-label">📁 Upload Study Material</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader(
        "PDF, DOCX, TXT, PPTX",
        type=["pdf", "docx", "txt", "md", "pptx"],
        help="Your notes are embedded locally — not sent to any cloud.",
        label_visibility="collapsed",
    )
    if uploaded:
        if st.button("⬆️  Process & Index", use_container_width=True):
            with st.spinner(f"Indexing {uploaded.name}…"):
                result = api_post(
                    "/upload",
                    files={"file": (uploaded.name, uploaded.getvalue(), uploaded.type)},
                )
            if result:
                st.success(f"**{uploaded.name}** indexed — {result.get('chunk_count', '?')} chunks added.")
                st.session_state.kb_ready = True
                time.sleep(1)
                st.rerun()

    files_data = api_get("/files")
    if files_data and files_data.get("files"):
        with st.expander("📂 Indexed documents"):
            for f in files_data["files"]:
                st.markdown(f"- **{f['original_name']}** ({f['file_type'].upper()}) — {f['chunk_count']} chunks")

    st.divider()

    # Settings
    st.markdown('<div class="section-label">⚙️ Settings</div>', unsafe_allow_html=True)
    mode      = st.selectbox("Mode",     ["simple", "exam"], label_visibility="collapsed")
    language  = st.selectbox("Language", ["English", "Malayalam", "Hindi", "Tamil"], label_visibility="collapsed")

    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown('<div class="section-label">Task</div>', unsafe_allow_html=True)
    task_type = st.radio("Task", ["learn", "quiz"], horizontal=True, label_visibility="collapsed")

    st.divider()

    # Navigation
    st.markdown('<div class="section-label">Views</div>', unsafe_allow_html=True)
    if st.button("💬  Chat",         use_container_width=True): st.session_state.active_tab = "chat"
    if st.button("🃏  Flashcards",   use_container_width=True): st.session_state.active_tab = "flashcards"
    if st.button("📊  Progress",     use_container_width=True): st.session_state.active_tab = "progress"
    if st.button("🗑️  Clear Chat",  use_container_width=True):
        st.session_state.messages  = []
        st.session_state.followup  = []
        st.session_state.quiz_state = {}
        st.rerun()


# ── Main area ─────────────────────────────────────────────────────────────────
tab = st.session_state.active_tab

# ────────────────────────────────────────────────────────────────── CHAT ──────
if tab == "chat":
    st.markdown("""
    <div class="page-hero">
        <div class="hero-title">Ask Your AI Tutor</div>
        <div class="hero-sub">Upload study material, then ask anything — explanations, quizzes, summaries.</div>
    </div>
    """, unsafe_allow_html=True)

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant" and msg.get("task_type") == "quiz":
                questions = parse_mcqs(msg["content"])
                if questions:
                    _render_quiz(questions, prefix=msg.get("id", "q"))
                else:
                    st.markdown(msg["content"])
            else:
                st.markdown(msg["content"])
            if msg.get("sources"):
                with st.expander("📄 Sources"):
                    for s in msg["sources"]:
                        st.markdown(f"- {s}")

    if st.session_state.followup:
        st.markdown('<div class="followup-label">💡 Suggested follow-ups</div>', unsafe_allow_html=True)
        cols = st.columns(len(st.session_state.followup))
        for i, (col, q) in enumerate(zip(cols, st.session_state.followup)):
            with col:
                if st.button(q, key=f"fu_{i}", use_container_width=True):
                    st.session_state._inject_query = q
                    st.rerun()

    if not st.session_state.kb_ready:
        st.info("📁 Upload a study document in the sidebar to begin.")

    prompt = st.chat_input(
        "Ask anything about your study materials…",
        disabled=not st.session_state.kb_ready,
    )

    if hasattr(st.session_state, "_inject_query"):
        prompt = st.session_state._inject_query
        del st.session_state._inject_query

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking… agents are working, this may take 20–40 s"):
                result = api_post("/ask", json={
                    "query":     prompt,
                    "mode":      mode,
                    "language":  language,
                    "task_type": task_type,
                })

            if result:
                response  = result.get("response", "")
                followups = result.get("followup", [])
                sources   = result.get("sources", [])
                msg_id    = f"msg_{len(st.session_state.messages)}"

                if task_type == "quiz":
                    questions = parse_mcqs(response)
                    if questions:
                        _render_quiz(questions, prefix=msg_id)
                    else:
                        st.markdown(response)
                else:
                    st.markdown(response)

                if sources:
                    with st.expander("📄 Sources"):
                        for s in sources:
                            st.markdown(f"- {s}")

                st.session_state.messages.append({
                    "role":      "assistant",
                    "content":   response,
                    "sources":   sources,
                    "task_type": task_type,
                    "id":        msg_id,
                })
                st.session_state.followup = followups
                st.rerun()


# ──────────────────────────────────────────────────────────────── FLASHCARDS ──
elif tab == "flashcards":
    st.markdown("""
    <div class="page-hero">
        <div class="hero-title">Flashcards</div>
        <div class="hero-sub">Auto-generate and review spaced-repetition cards from your material.</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([4, 1])
    with col1:
        topic = st.text_input("Topic", placeholder="e.g. Photosynthesis, Python decorators…", label_visibility="collapsed")
    with col2:
        gen = st.button("Generate ✨", use_container_width=True, disabled=not st.session_state.kb_ready)

    if gen and topic:
        with st.spinner("Generating flashcards…"):
            result = api_post("/flashcards/generate", json={
                "query": topic, "mode": "simple", "language": "English", "task_type": "learn"
            })
        if result and result.get("flashcards"):
            st.success(f"Generated {len(result['flashcards'])} flashcards for **{topic}**!")

    filter_topic = st.text_input("Filter by topic", placeholder="Leave blank to show all…", label_visibility="collapsed")
    fc_data = api_get(f"/flashcards{'?topic=' + filter_topic if filter_topic else ''}")

    if fc_data and fc_data.get("flashcards"):
        cards = fc_data["flashcards"]
        st.markdown(f'<div class="section-label">{len(cards)} flashcards</div>', unsafe_allow_html=True)
        for card in cards:
            label = f"Q: {card['question'][:80]}…" if len(card['question']) > 80 else f"Q: {card['question']}"
            with st.expander(label):
                st.markdown(f"**Answer:** {card['answer']}")
                st.caption(f"Topic: {card['topic']} · Created: {card['created_at'][:10]}")
    else:
        st.info("No flashcards yet — generate some above!")


# ────────────────────────────────────────────────────────────────── PROGRESS ──
elif tab == "progress":
    st.markdown("""
    <div class="page-hero">
        <div class="hero-title">Learning Progress</div>
        <div class="hero-sub">Track what you've studied and where you need more practice.</div>
    </div>
    """, unsafe_allow_html=True)

    stats_data = api_get("/stats")

    if not stats_data or not stats_data.get("topics"):
        st.info("No study data yet. Start asking questions!")
    else:
        topics = stats_data["topics"]

        total_topics  = len(topics)
        total_queries = sum(t["ask_count"] for t in topics)
        avg_score     = (
            sum(t["quiz_score"] for t in topics if t["quiz_attempts"] > 0)
            / max(1, sum(1 for t in topics if t["quiz_attempts"] > 0))
        )

        c1, c2, c3 = st.columns(3)
        c1.metric("Topics Studied",  total_topics)
        c2.metric("Total Questions", total_queries)
        c3.metric("Avg Quiz Score",  f"{avg_score:.1f}%")

        st.divider()

        # Chart styling to match palette
        CHART_BG  = "rgba(0,0,0,0)"
        FONT      = dict(family="DM Sans", color="#6B4C30")
        GRIDCOLOR = "#E2D4C0"

        names  = [t["name"][:30] for t in topics[:10]]
        counts = [t["ask_count"] for t in topics[:10]]
        fig1   = go.Figure(go.Bar(
            x=names, y=counts,
            marker=dict(color="#C4703A", opacity=0.85, line=dict(color="#A3561F", width=1)),
        ))
        fig1.update_layout(
            title=dict(text="Most Studied Topics", font=dict(family="Playfair Display", size=16, color="#2C1A0E")),
            xaxis=dict(title="Topic", tickfont=FONT, gridcolor=GRIDCOLOR),
            yaxis=dict(title="Times Asked", tickfont=FONT, gridcolor=GRIDCOLOR),
            paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG,
            height=340, margin=dict(l=20, r=20, t=50, b=20),
        )
        st.plotly_chart(fig1, use_container_width=True)

        quiz_topics = [t for t in topics if t["quiz_attempts"] > 0]
        if quiz_topics:
            q_names  = [t["name"][:30] for t in quiz_topics]
            q_scores = [t["quiz_score"] for t in quiz_topics]
            colors   = ["#e07070" if s < 50 else "#D4895A" if s < 75 else "#5aab6d" for s in q_scores]
            fig2     = go.Figure(go.Bar(
                x=q_names, y=q_scores,
                marker=dict(color=colors, opacity=0.9, line=dict(color="#2C1A0E", width=0.5)),
            ))
            fig2.update_layout(
                title=dict(text="Quiz Scores by Topic", font=dict(family="Playfair Display", size=16, color="#2C1A0E")),
                xaxis=dict(title="Topic", tickfont=FONT, gridcolor=GRIDCOLOR),
                yaxis=dict(title="Score (%)", tickfont=FONT, gridcolor=GRIDCOLOR, range=[0, 100]),
                paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG,
                height=340, margin=dict(l=20, r=20, t=50, b=20),
            )
            st.plotly_chart(fig2, use_container_width=True)

        with st.expander("📋 Full topic table"):
            st.dataframe(topics, use_container_width=True)

        weak = [t for t in topics if t["quiz_attempts"] > 0 and t["quiz_score"] < 60]
        if weak:
            st.warning(
                "**📌 Topics needing review:**  \n"
                + "  \n".join(f"- **{t['name']}** (score: {t['quiz_score']:.0f}%)" for t in weak[:5])
            )
