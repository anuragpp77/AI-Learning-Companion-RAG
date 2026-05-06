"""
  - Chat interface (st.chat_message / st.chat_input)
  - Sidebar: file upload, mode/language/task settings, uploaded files list
  - Structured MCQ rendering with radio buttons + answer checking
  - Follow-up question chips
  - Source citations display
  - Progress dashboard (topic stats chart)
  - Loading spinners throughout
  - Full error handling on every API call
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
    page_title="AI Study Companion",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

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
    """Render MCQs as interactive radio buttons with answer checking."""
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
    st.title("📚 Study Companion")
    st.caption("Multi-Agent AI Tutor")

    health = check_health()
    provider = health.get("llm_provider", "Unknown")
    kb_status = "✅ Ready" if st.session_state.kb_ready else "⚠️ No documents yet"
    st.info(f"**LLM:** {provider}  \n**Knowledge Base:** {kb_status}")

    st.divider()

    st.subheader("📁 Upload Study Material")
    uploaded = st.file_uploader(
        "PDF, DOCX, TXT, PPTX",
        type=["pdf", "docx", "txt", "md", "pptx"],
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
                st.success(f"✅ **{uploaded.name}** indexed!\n\n{result.get('chunk_count', '?')} chunks added.")
                st.session_state.kb_ready = True
                time.sleep(1)
                st.rerun()

    files_data = api_get("/files")
    if files_data and files_data.get("files"):
        with st.expander("📂 Indexed documents", expanded=False):
            for f in files_data["files"]:
                st.markdown(f"- **{f['original_name']}** ({f['file_type'].upper()}) — {f['chunk_count']} chunks")

    st.divider()

    st.subheader("⚙️ Settings")
    mode      = st.selectbox("Mode",     ["simple", "exam"])
    language  = st.selectbox("Language", ["English", "Malayalam", "Hindi", "Tamil"])
    task_type = st.radio("Task", ["learn", "quiz"])

    st.divider()

    st.subheader("🗂️ Views")
    if st.button("💬 Chat",        use_container_width=True): st.session_state.active_tab = "chat"
    if st.button("🃏 Flashcards",  use_container_width=True): st.session_state.active_tab = "flashcards"
    if st.button("📊 Progress",    use_container_width=True): st.session_state.active_tab = "progress"
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.followup = []
        st.session_state.quiz_state = {}
        st.rerun()


# ── Main area ─────────────────────────────────────────────────────────────────

tab = st.session_state.active_tab

# ── CHAT ─────────────────────────────────────────────────────────────────────
if tab == "chat":
    st.title("💬 Ask Your AI Tutor")

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
        st.markdown("**💡 Suggested next questions:**")
        cols = st.columns(len(st.session_state.followup))
        for i, (col, q) in enumerate(zip(cols, st.session_state.followup)):
            with col:
                if st.button(q, key=f"fu_{i}", use_container_width=True):
                    st.session_state._inject_query = q
                    st.rerun()

    prompt = st.chat_input(
        "Ask anything about your study materials…",
        disabled=not st.session_state.kb_ready,
    )

    if hasattr(st.session_state, "_inject_query"):
        prompt = st.session_state._inject_query
        del st.session_state._inject_query

    if not st.session_state.kb_ready:
        st.info("⬆️ Upload a study document in the sidebar to get started.")

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("🤔 Thinking… (agents are working, this may take 20-40 seconds)"):
                result = api_post("/ask", json={
                    "query": prompt,
                    "mode": mode,
                    "language": language,
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
                    "role": "assistant",
                    "content": response,
                    "sources": sources,
                    "task_type": task_type,
                    "id": msg_id,
                })
                st.session_state.followup = followups
                st.rerun()

# ── FLASHCARDS ────────────────────────────────────────────────────────────────
elif tab == "flashcards":
    st.title("🃏 Flashcards")

    col1, col2 = st.columns([3, 1])
    with col1:
        topic = st.text_input("Topic to generate flashcards for")
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        gen = st.button("Generate", use_container_width=True, disabled=not st.session_state.kb_ready)

    if gen and topic:
        with st.spinner("Generating flashcards…"):
            result = api_post("/flashcards/generate", json={"query": topic, "mode": "simple", "language": "English", "task_type": "learn"})
        if result and result.get("flashcards"):
            st.success(f"Generated {len(result['flashcards'])} flashcards!")

    filter_topic = st.text_input("Filter by topic (optional)")
    fc_data = api_get(f"/flashcards{'?topic=' + filter_topic if filter_topic else ''}")

    if fc_data and fc_data.get("flashcards"):
        cards = fc_data["flashcards"]
        st.markdown(f"**{len(cards)} flashcards**")
        for card in cards:
            label = f"Q: {card['question'][:80]}…" if len(card['question']) > 80 else f"Q: {card['question']}"
            with st.expander(label):
                st.markdown(f"**Answer:** {card['answer']}")
                st.caption(f"Topic: {card['topic']} | Created: {card['created_at'][:10]}")
    else:
        st.info("No flashcards yet. Generate some above!")

# ── PROGRESS ──────────────────────────────────────────────────────────────────
elif tab == "progress":
    st.title("📊 Your Learning Progress")

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

        names  = [t["name"][:30] for t in topics[:10]]
        counts = [t["ask_count"] for t in topics[:10]]
        fig1   = go.Figure(go.Bar(x=names, y=counts, marker_color="#4f8bf9"))
        fig1.update_layout(title="Most Studied Topics", xaxis_title="Topic", yaxis_title="Times Asked", height=350)
        st.plotly_chart(fig1, use_container_width=True)

        quiz_topics = [t for t in topics if t["quiz_attempts"] > 0]
        if quiz_topics:
            q_names  = [t["name"][:30] for t in quiz_topics]
            q_scores = [t["quiz_score"] for t in quiz_topics]
            colors   = ["#e74c3c" if s < 50 else "#f39c12" if s < 75 else "#2ecc71" for s in q_scores]
            fig2     = go.Figure(go.Bar(x=q_names, y=q_scores, marker_color=colors))
            fig2.update_layout(title="Quiz Scores by Topic", xaxis_title="Topic", yaxis_title="Score (%)", yaxis_range=[0, 100], height=350)
            st.plotly_chart(fig2, use_container_width=True)

        with st.expander("📋 Full topic table"):
            st.dataframe(topics, use_container_width=True)

        weak = [t for t in topics if t["quiz_attempts"] > 0 and t["quiz_score"] < 60]
        if weak:
            st.warning(
                "**📌 Topics to review:**  \n"
                + "  \n".join(f"- **{t['name']}** (score: {t['quiz_score']:.0f}%)" for t in weak[:5])
            )