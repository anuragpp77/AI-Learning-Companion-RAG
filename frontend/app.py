"""
  AI-Learn Study Companion – restyled to match screenshot UI
  Keeps all original functionality intact.
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
    page_title="Study Companion",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────

st.markdown("""
<style>
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,600;1,400&family=DM+Sans:wght@300;400;500;600&display=swap');

/* ── Root tokens ── */
:root {
    --bg:           #F0EBE1;
    --bg-sidebar:   #E8E2D8;
    --surface:      #FDFAF6;
    --surface-alt:  #F5F0E8;
    --border:       #D9D2C7;
    --border-light: #EAE4DA;
    --text-primary: #1C1916;
    --text-secondary: #6B6560;
    --text-muted:   #9B958F;
    --accent:       #C94B2D;
    --accent-light: #F2E8E5;
    --accent-hover: #A83A20;
    --success:      #2C7A4B;
    --warning:      #B8860B;
    --radius-sm:    8px;
    --radius-md:    14px;
    --radius-lg:    20px;
    --shadow-sm:    0 1px 3px rgba(0,0,0,0.07);
    --shadow-md:    0 4px 16px rgba(0,0,0,0.08);
}

/* ── Global reset ── */
html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg) !important;
    font-family: 'DM Sans', sans-serif !important;
    color: var(--text-primary) !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background-color: var(--bg-sidebar) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] > div:first-child {
    padding-top: 1.25rem !important;
}
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stCaption {
    color: var(--text-secondary) !important;
}

/* Sidebar title */
[data-testid="stSidebar"] h1 {
    font-family: 'Lora', serif !important;
    font-size: 1.3rem !important;
    color: var(--text-primary) !important;
    letter-spacing: -0.01em !important;
}

/* ── Main area ── */
[data-testid="stMain"], .main .block-container {
    background-color: var(--bg) !important;
    padding-top: 1.5rem !important;
    max-width: 860px !important;
}

/* ── Typography ── */
h1 {
    font-family: 'Lora', serif !important;
    font-size: 2.6rem !important;
    font-weight: 600 !important;
    letter-spacing: -0.03em !important;
    color: var(--text-primary) !important;
    line-height: 1.2 !important;
}
h2, h3 {
    font-family: 'Lora', serif !important;
    color: var(--text-primary) !important;
}
p, li, span {
    font-family: 'DM Sans', sans-serif !important;
    color: var(--text-secondary) !important;
}

/* ── Buttons ── */
.stButton > button {
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.875rem !important;
    border-radius: var(--radius-sm) !important;
    border: 1px solid var(--border) !important;
    background: var(--surface) !important;
    color: var(--text-primary) !important;
    padding: 0.5rem 1rem !important;
    transition: all 0.15s ease !important;
    box-shadow: var(--shadow-sm) !important;
}
.stButton > button:hover {
    background: var(--surface-alt) !important;
    border-color: var(--accent) !important;
    color: var(--accent) !important;
    transform: translateY(-1px) !important;
    box-shadow: var(--shadow-md) !important;
}
.stButton > button:active {
    transform: translateY(0) !important;
}

/* Primary / process button */
.stButton > button[kind="primary"] {
    background: var(--accent) !important;
    color: #fff !important;
    border-color: var(--accent) !important;
}
.stButton > button[kind="primary"]:hover {
    background: var(--accent-hover) !important;
    color: #fff !important;
}

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    background: var(--surface) !important;
    border: 1.5px dashed var(--border) !important;
    border-radius: var(--radius-md) !important;
    padding: 1rem !important;
}
[data-testid="stFileUploader"] label {
    color: var(--text-secondary) !important;
}

/* ── Inputs ── */
.stTextInput > div > div > input,
.stTextArea textarea {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text-primary) !important;
    font-family: 'DM Sans', sans-serif !important;
}
.stTextInput > div > div > input:focus,
.stTextArea textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(201,75,45,0.1) !important;
    outline: none !important;
}

/* ── Selectbox ── */
[data-testid="stSelectbox"] > div > div {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text-primary) !important;
}

/* ── Radio ── */
[data-testid="stRadio"] > label {
    color: var(--text-secondary) !important;
}
[data-testid="stRadio"] span {
    color: var(--text-primary) !important;
}

/* ── Info / success / error ── */
.stInfo, [data-testid="stAlert"][data-baseweb="notification"] {
    background: var(--accent-light) !important;
    border: 1px solid #DDB5A8 !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text-primary) !important;
}
.stSuccess {
    background: #E8F5ED !important;
    border-color: #A8D4B8 !important;
}
.stError {
    background: #FBEAEA !important;
}

/* ── Chat messages ── */
[data-testid="stChatMessage"] {
    background: var(--surface) !important;
    border: 1px solid var(--border-light) !important;
    border-radius: var(--radius-md) !important;
    padding: 1rem 1.25rem !important;
    margin-bottom: 0.75rem !important;
    box-shadow: var(--shadow-sm) !important;
}
[data-testid="stChatMessage"][data-testid*="user"] {
    background: var(--accent-light) !important;
    border-color: #DDB5A8 !important;
}

/* ── Chat input ── */
[data-testid="stChatInput"] > div {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-lg) !important;
    box-shadow: var(--shadow-md) !important;
}
[data-testid="stChatInput"] textarea {
    background: transparent !important;
    color: var(--text-primary) !important;
    font-family: 'DM Sans', sans-serif !important;
}
[data-testid="stChatInput"] textarea::placeholder {
    color: var(--text-muted) !important;
}

/* ── Expander ── */
[data-testid="stExpander"] {
    background: var(--surface) !important;
    border: 1px solid var(--border-light) !important;
    border-radius: var(--radius-sm) !important;
}
[data-testid="stExpander"] summary {
    color: var(--text-secondary) !important;
    font-size: 0.875rem !important;
}

/* ── Divider ── */
hr {
    border-color: var(--border) !important;
    margin: 1rem 0 !important;
}

/* ── Metric cards ── */
[data-testid="stMetric"] {
    background: var(--surface) !important;
    border: 1px solid var(--border-light) !important;
    border-radius: var(--radius-md) !important;
    padding: 1rem 1.25rem !important;
    box-shadow: var(--shadow-sm) !important;
}
[data-testid="stMetricLabel"] {
    color: var(--text-secondary) !important;
    font-size: 0.8rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
}
[data-testid="stMetricValue"] {
    font-family: 'Lora', serif !important;
    color: var(--text-primary) !important;
    font-size: 2rem !important;
}

/* ── Spinner ── */
.stSpinner > div {
    border-top-color: var(--accent) !important;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    border-radius: var(--radius-sm) !important;
    border: 1px solid var(--border) !important;
    overflow: hidden !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }

/* ── Custom welcome screen cards ── */
.quick-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin: 1.5rem 0;
}
.quick-card {
    background: var(--surface);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-md);
    padding: 1.1rem 1.25rem;
    cursor: pointer;
    transition: all 0.18s ease;
    box-shadow: var(--shadow-sm);
    text-align: left;
}
.quick-card:hover {
    border-color: var(--accent);
    box-shadow: var(--shadow-md);
    transform: translateY(-2px);
}
.quick-card .icon {
    font-size: 1.3rem;
    margin-bottom: 0.4rem;
    display: block;
}
.quick-card .label {
    font-family: 'DM Sans', sans-serif;
    font-weight: 600;
    font-size: 0.9rem;
    color: var(--text-primary);
    display: block;
}
.quick-card .sublabel {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.78rem;
    color: var(--text-muted);
    display: block;
    margin-top: 0.15rem;
}

/* ── Status pill ── */
.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 999px;
    padding: 0.3rem 1rem;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--text-secondary);
    margin-bottom: 1.25rem;
}
.status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--accent);
    animation: pulse 2s ease-in-out infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50%       { opacity: 0.6; transform: scale(0.85); }
}

/* ── Sidebar file list ── */
.kb-file {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 0.65rem 0.75rem;
    background: var(--surface);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-sm);
    margin-bottom: 8px;
}
.kb-file .fi-icon {
    font-size: 1.1rem;
    margin-top: 1px;
    flex-shrink: 0;
}
.kb-file .fi-name {
    font-size: 0.82rem;
    font-weight: 600;
    color: var(--text-primary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 160px;
    display: block;
}
.kb-file .fi-meta {
    font-size: 0.72rem;
    color: var(--text-muted);
    display: block;
}

/* ── Section subheader ── */
.section-label {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 0.5rem;
    display: flex;
    justify-content: space-between;
}

/* ── Context banner ── */
.ctx-banner {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 0.35rem 0.85rem;
    font-size: 0.82rem;
    color: var(--text-secondary);
    margin-bottom: 1.5rem;
}
.ctx-banner span { font-weight: 500; color: var(--text-primary); }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────

if "messages"   not in st.session_state: st.session_state.messages   = []
if "followup"   not in st.session_state: st.session_state.followup   = []
if "quiz_state" not in st.session_state: st.session_state.quiz_state = {}
if "active_tab" not in st.session_state: st.session_state.active_tab = "chat"
if "kb_ready"   not in st.session_state: st.session_state.kb_ready   = False
if "files_list" not in st.session_state: st.session_state.files_list = []


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


def _file_icon(ftype: str) -> str:
    icons = {"pdf": "📄", "docx": "📝", "pptx": "📊", "txt": "📃", "md": "📃"}
    return icons.get(ftype.lower(), "📁")


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
    st.markdown("### 📝 Quiz")
    for i, q in enumerate(questions):
        st.markdown(f"**Q{i+1}. {q['question']}**")
        key = f"{prefix}_q{i}"
        choice = st.radio(
            f"Q{i+1}",
            options=list(q["options"].keys()),
            format_func=lambda k, opts=q["options"]: f"{k}) {opts[k]}",
            key=key,
            label_visibility="collapsed",
        )
        check_key = f"{key}_checked"
        if st.button("Check answer", key=f"{key}_btn"):
            st.session_state.quiz_state[check_key] = choice
        if st.session_state.quiz_state.get(check_key):
            submitted = st.session_state.quiz_state[check_key]
            correct = q.get("answer", "")
            if submitted == correct:
                st.success(f"✅ Correct! {q.get('explanation', '')}")
            else:
                st.error(f"❌ Incorrect. Correct answer: **{correct})**  \n{q.get('explanation', '')}")
        st.markdown("---")


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("# 📚 Study Companion")
    st.caption("Multi-Agent AI Tutor")

    health      = check_health()
    provider    = health.get("llm_provider", "Unknown")
    files_data  = api_get("/files")
    files_list  = (files_data or {}).get("files", [])

    # ── Upload area ──
    st.markdown('<div class="section-label">Upload Material</div>', unsafe_allow_html=True)

    upload_container = st.container()
    with upload_container:
        uploaded = st.file_uploader(
            "PDF, DOCX, PPTX, TXT",
            type=["pdf", "docx", "txt", "md", "pptx"],
            label_visibility="collapsed",
            help="Your notes are embedded locally — not sent to any cloud.",
        )
        if uploaded:
            if st.button("⬆️ Process & Index", use_container_width=True):
                with st.spinner(f"Indexing {uploaded.name}…"):
                    result = api_post(
                        "/upload",
                        files={"file": (uploaded.name, uploaded.getvalue(), uploaded.type)},
                    )
                if result:
                    st.success(f"✅ **{uploaded.name}** indexed — {result.get('chunk_count', '?')} chunks.")
                    st.session_state.kb_ready = True
                    time.sleep(1)
                    st.rerun()

    # ── Knowledge base file list ──
    if files_list:
        st.markdown("")
        n = len(files_list)
        st.markdown(
            f'<div class="section-label"><span>Knowledge Base</span><span>{n} File{"s" if n != 1 else ""}</span></div>',
            unsafe_allow_html=True,
        )
        for f in files_list:
            icon  = _file_icon(f.get("file_type", ""))
            name  = f.get("original_name", "Unknown")
            ftype = f.get("file_type", "").upper()
            chunks = f.get("chunk_count", "?")
            st.markdown(
                f"""
                <div class="kb-file">
                    <span class="fi-icon">{icon}</span>
                    <div>
                        <span class="fi-name" title="{name}">{name}</span>
                        <span class="fi-meta">{ftype} &middot; {chunks} chunks</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-label">Views</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("💬 Chat",       use_container_width=True): st.session_state.active_tab = "chat"
        if st.button("📊 Progress",   use_container_width=True): st.session_state.active_tab = "progress"
    with c2:
        if st.button("🃏 Flashcards", use_container_width=True): st.session_state.active_tab = "flashcards"
        if st.button("🗑️ Clear",      use_container_width=True):
            st.session_state.messages   = []
            st.session_state.followup   = []
            st.session_state.quiz_state = {}
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-label">⚙️ Settings</div>', unsafe_allow_html=True)
    mode      = st.selectbox("Mode",     ["simple", "exam"], label_visibility="collapsed")
    language  = st.selectbox("Language", ["English", "Malayalam", "Hindi", "Tamil"], label_visibility="collapsed")
    task_type = st.radio("Task", ["learn", "quiz"], horizontal=True, label_visibility="collapsed")


# ── Main area ─────────────────────────────────────────────────────────────────

tab = st.session_state.active_tab

# ── CHAT ──────────────────────────────────────────────────────────────────────
if tab == "chat":

    # Context banner (if files loaded, show first active file like screenshot)
    if files_list:
        active_file = files_list[0].get("original_name", "")
        icon        = _file_icon(files_list[0].get("file_type", ""))
        st.markdown(
            f'<div class="ctx-banner">{icon} Context: <span>{active_file}</span></div>',
            unsafe_allow_html=True,
        )

    # Welcome screen when no messages yet
    if not st.session_state.messages:

        # Status pill
        if st.session_state.kb_ready:
            st.markdown(
                '<div style="text-align:center"><span class="status-pill"><span class="status-dot"></span>System Ready</span></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div style="text-align:center"><span class="status-pill" style="color:var(--text-muted)">⚠️ No documents yet</span></div>',
                unsafe_allow_html=True,
            )

        st.markdown(
            '<h1 style="text-align:center;margin:0.5rem 0 0.25rem">What shall we learn today?</h1>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<p style="text-align:center;color:var(--text-muted);margin-bottom:0.25rem">Your knowledge base is loaded and indexed. Choose a quick action below or type a question to begin your session.</p>',
            unsafe_allow_html=True,
        )

        # Quick action cards (inject into chat input on click)
        quick_actions = [
            ("🔍", "Summarize key concepts", f"from {files_list[0]['original_name'] if files_list else 'my notes'}"),
            ("📝", "Generate a 5-question quiz", "to test my knowledge"),
            ("🔎", "Find explanations", "for the main topic in my notes"),
            ("✨", "Explain like I'm 5", "the core ideas in Chapter 1"),
        ]

        st.markdown('<div class="quick-grid">', unsafe_allow_html=True)
        cols = st.columns(2)
        for idx, (icon, label, sub) in enumerate(quick_actions):
            with cols[idx % 2]:
                if st.button(
                    f"{icon} **{label}**\n\n{sub}",
                    key=f"qk_{idx}",
                    use_container_width=True,
                ):
                    st.session_state._inject_query = label
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    else:
        # Render conversation history
        st.markdown('<h2 style="font-size:1.4rem;margin-bottom:1rem">💬 Chat</h2>', unsafe_allow_html=True)
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

    # Follow-up chips
    if st.session_state.followup:
        st.markdown("**💡 Suggested next questions:**")
        fup_cols = st.columns(len(st.session_state.followup))
        for i, (col, q) in enumerate(zip(fup_cols, st.session_state.followup)):
            with col:
                if st.button(q, key=f"fu_{i}", use_container_width=True):
                    st.session_state._inject_query = q
                    st.rerun()

    # Chat input
    prompt = st.chat_input(
        "Ask a question about your materials…",
        disabled=not st.session_state.kb_ready,
    )

    if hasattr(st.session_state, "_inject_query"):
        prompt = st.session_state._inject_query
        del st.session_state._inject_query

    if not st.session_state.kb_ready and not st.session_state.messages:
        st.info("⬆️ Upload a study document in the sidebar to get started.")

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("🤔 Thinking… agents are working, this may take 20–40 s"):
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


# ── FLASHCARDS ────────────────────────────────────────────────────────────────
elif tab == "flashcards":
    st.markdown('<h1 style="font-size:2rem;margin-bottom:1.5rem">🃏 Flashcards</h1>', unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])
    with col1:
        topic = st.text_input("Topic to generate flashcards for", placeholder="e.g. Laws of Thermodynamics")
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        gen = st.button("Generate", use_container_width=True, disabled=not st.session_state.kb_ready)

    if gen and topic:
        with st.spinner("Generating flashcards…"):
            result = api_post("/flashcards/generate", json={
                "query": topic, "mode": "simple", "language": "English", "task_type": "learn"
            })
        if result and result.get("flashcards"):
            st.success(f"Generated {len(result['flashcards'])} flashcards!")

    filter_topic = st.text_input("Filter by topic (optional)", placeholder="Filter…")
    fc_data = api_get(f"/flashcards{'?topic=' + filter_topic if filter_topic else ''}")

    if fc_data and fc_data.get("flashcards"):
        cards = fc_data["flashcards"]
        st.markdown(f"**{len(cards)} flashcard{'s' if len(cards) != 1 else ''}**")
        for card in cards:
            label = f"Q: {card['question'][:80]}…" if len(card['question']) > 80 else f"Q: {card['question']}"
            with st.expander(label):
                st.markdown(f"**Answer:** {card['answer']}")
                st.caption(f"Topic: {card['topic']} | Created: {card['created_at'][:10]}")
    else:
        st.info("No flashcards yet. Generate some above!")


# ── PROGRESS ──────────────────────────────────────────────────────────────────
elif tab == "progress":
    st.markdown('<h1 style="font-size:2rem;margin-bottom:1.5rem">📊 Learning Progress</h1>', unsafe_allow_html=True)

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

        # Chart colours matching the cream theme
        CHART_BG   = "rgba(0,0,0,0)"
        CHART_BLUE = "#C94B2D"
        FONT_COLOR = "#6B6560"
        GRID_COLOR = "#D9D2C7"

        names  = [t["name"][:30] for t in topics[:10]]
        counts = [t["ask_count"] for t in topics[:10]]
        fig1   = go.Figure(go.Bar(x=names, y=counts, marker_color=CHART_BLUE, marker_line_width=0))
        fig1.update_layout(
            title="Most Studied Topics",
            paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG,
            font=dict(family="DM Sans", color=FONT_COLOR),
            xaxis=dict(gridcolor=GRID_COLOR, tickfont=dict(size=11)),
            yaxis=dict(gridcolor=GRID_COLOR, title="Times Asked"),
            height=340,
        )
        st.plotly_chart(fig1, use_container_width=True)

        quiz_topics = [t for t in topics if t["quiz_attempts"] > 0]
        if quiz_topics:
            q_names  = [t["name"][:30] for t in quiz_topics]
            q_scores = [t["quiz_score"] for t in quiz_topics]
            colors   = ["#C94B2D" if s < 50 else "#D4960A" if s < 75 else "#2C7A4B" for s in q_scores]
            fig2     = go.Figure(go.Bar(x=q_names, y=q_scores, marker_color=colors, marker_line_width=0))
            fig2.update_layout(
                title="Quiz Scores by Topic",
                paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG,
                font=dict(family="DM Sans", color=FONT_COLOR),
                xaxis=dict(gridcolor=GRID_COLOR),
                yaxis=dict(gridcolor=GRID_COLOR, title="Score (%)", range=[0, 100]),
                height=340,
            )
            st.plotly_chart(fig2, use_container_width=True)

        with st.expander("📋 Full topic table"):
            st.dataframe(topics, use_container_width=True)

        weak = [t for t in topics if t["quiz_attempts"] > 0 and t["quiz_score"] < 60]
        if weak:
            st.warning(
                "**📌 Topics to review:**  \n"
                + "  \n".join(f"- **{t['name']}** (score: {t['quiz_score']:.0f}%)" for t in weak[:5])
            )