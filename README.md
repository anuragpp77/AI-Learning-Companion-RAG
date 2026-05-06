# 📚 AI Learning Companion
### Multilingual Multi-Agent RAG Tutoring System

A personalized AI tutor built with **CrewAI**, **LangChain**, **FAISS**, **FastAPI**, and **Streamlit**. Upload your notes, ask questions in your language, take quizzes, generate flashcards, and track your progress — all running locally.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Streamlit Frontend                  │
│   Chat UI · Quiz Renderer · Flashcards · Dashboard  │
└────────────────────┬────────────────────────────────┘
                     │ HTTP (httpx)
┌────────────────────▼────────────────────────────────┐
│                 FastAPI Backend                      │
│  /ask  /upload  /stats  /flashcards  /quiz-score    │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│              CrewAI Multi-Agent Pipeline             │
│                                                     │
│   Planner → Retriever → Summarizer → Teacher        │
│                                    └─ Evaluator     │
│                                    └─ Follow-up     │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│            RAG Layer (LangChain + FAISS)             │
│    Ingest : PDF · DOCX · TXT · PPTX · MD            │
│    Embed  : all-MiniLM-L6-v2 (HuggingFace)          │
│    Search : FAISS vector similarity                  │
└─────────────────────────────────────────────────────┘
```

---

## 🤖 Agents

| Agent | Role |
|---|---|
| **Planner** | Designs a teaching plan based on query, mode, and weak topics |
| **Retriever** | Semantically searches the FAISS knowledge base using `@tool` |
| **Summarizer** | Condenses raw retrieved chunks before passing to Teacher |
| **Teacher** | Delivers beginner-friendly or exam-style answers with source citations |
| **Evaluator** | Generates 5 MCQs with answers and explanations |
| **Follow-up** | Produces 3 Socratic next-questions to deepen understanding |

---

## ✨ Features

- 🌐 **Multilingual** — responses in English, Malayalam, and Hindi
- 📄 **Multi-format upload** — PDF, DOCX, PPTX, TXT, Markdown
- 🧠 **Additive knowledge base** — each upload merges into the existing FAISS index
- 📝 **Structured quizzes** — interactive MCQs with radio buttons and score tracking
- 🃏 **Flashcard generation** — Anki-style Q&A pairs saved to SQLite
- 📊 **Progress dashboard** — bar charts of topics studied and quiz scores with weak-topic alerts
- 🔗 **Source citations** — every answer cites the exact document and page
- ❓ **Follow-up questions** — 3 Socratic next-questions after every answer

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Agent framework | CrewAI 0.51 |
| LLM | Groq / OpenAI / Ollama (Mistral) |
| Embeddings | `all-MiniLM-L6-v2` via HuggingFace |
| Vector store | FAISS |
| RAG orchestration | LangChain 0.2 |
| API | FastAPI + Uvicorn |
| Frontend | Streamlit 1.35 |
| Persistence | SQLite (topics, flashcards, files) |
| Charts | Plotly |

---

## 🚀 Quickstart

### 1. Install

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure LLM

```bash
cp .env.example .env
# Edit .env and add one of:
#   GROQ_API_KEY=...
#   OPENAI_API_KEY=...
#   or leave blank for local Ollama
```

### 3. Run

```bash
# Terminal 1 — backend
uvicorn backend.main:app --reload --port 8000

# Terminal 2 — frontend
streamlit run frontend/app.py
```

Open [http://localhost:8501](http://localhost:8501)

---

## 📁 Project Structure

```
ai-learning-companion/
├── requirements.txt
├── .env.example
├── README.md
├── backend/
│   ├── main.py              # FastAPI app
│   ├── crew.py              # Multi-agent orchestration
│   ├── core/
│   │   ├── llm.py           # LLM factory (Groq / OpenAI / Ollama)
│   │   ├── database.py      # SQLite schema and connection
│   │   └── memory.py        # Topic tracking, flashcards, file log
│   ├── agents/
│   │   ├── planner.py
│   │   ├── retriever.py     # @tool-decorated FAISS search
│   │   ├── summarizer.py
│   │   ├── teacher.py
│   │   ├── evaluator.py
│   │   └── followup.py
│   └── rag/
│       ├── ingest.py        # Multi-format loader + FAISS merge
│       └── vectorstore.py   # Load / existence check
└── frontend/
    └── app.py               # Streamlit chat UI
```

---

## 📄 License

MIT License — feel free to use, modify, and distribute.
