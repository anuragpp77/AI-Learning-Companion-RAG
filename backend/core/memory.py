"""
backend/core/memory.py
──────────────────────
Topic tracking backed by SQLite.

FIX (original bug #5 + #6):
  • Old code:  in-memory defaultdict — reset on every restart, tracked
               frequency instead of quiz performance.
  • New code:  SQLite-backed; tracks both ask_count AND quiz_score so
               get_weak_topics() returns topics the student actually
               struggles with (low score + high attempt count).
"""

from backend.core.database import get_connection


# ── Query tracking ────────────────────────────────────────────────────────────

def track_query(query: str) -> None:
    """Increment ask_count for a topic, inserting it if new."""
    # Use the first 5 words as the topic key to normalise similar queries
    topic = " ".join(query.lower().split()[:5])
    conn = get_connection()
    conn.execute("""
        INSERT INTO topics (name, ask_count, last_seen)
             VALUES (?, 1, CURRENT_TIMESTAMP)
        ON CONFLICT(name) DO UPDATE SET
             ask_count = ask_count + 1,
             last_seen  = CURRENT_TIMESTAMP
    """, (topic,))
    conn.commit()
    conn.close()


def update_quiz_score(topic: str, score: float) -> None:
    """
    Record a quiz attempt with a 0–100 score.
    Running average is maintained so repeated attempts improve/worsen score.
    """
    topic = topic.lower().strip()
    conn = get_connection()
    conn.execute("""
        INSERT INTO topics (name, quiz_attempts, quiz_score)
             VALUES (?, 1, ?)
        ON CONFLICT(name) DO UPDATE SET
             quiz_attempts = quiz_attempts + 1,
             quiz_score    = (quiz_score * quiz_attempts + ?) / (quiz_attempts + 1),
             last_seen     = CURRENT_TIMESTAMP
    """, (topic, score, score))
    conn.commit()
    conn.close()


def get_weak_topics(limit: int = 5) -> list[dict]:
    """
    Return topics ranked by weakness:
    - Low quiz_score   → student is failing quizzes on this topic
    - High ask_count   → student keeps revisiting (doesn't understand yet)
    Topics with no quiz attempts are ranked by ask_count alone.
    """
    conn = get_connection()
    rows = conn.execute("""
        SELECT name, ask_count, quiz_attempts, quiz_score, last_seen
          FROM topics
         ORDER BY
               CASE WHEN quiz_attempts > 0 THEN quiz_score ELSE 100 END ASC,
               ask_count DESC
         LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_topic_stats() -> list[dict]:
    """Return all topic stats for the progress dashboard."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT name, ask_count, quiz_attempts,
               ROUND(quiz_score, 1) AS quiz_score, last_seen
          FROM topics
         ORDER BY last_seen DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Flashcard management ──────────────────────────────────────────────────────

def save_flashcards(topic: str, pairs: list[dict]) -> None:
    """Persist a list of {question, answer} dicts to the flashcards table."""
    conn = get_connection()
    conn.executemany(
        "INSERT INTO flashcards (topic, question, answer) VALUES (?, ?, ?)",
        [(topic, p["question"], p["answer"]) for p in pairs]
    )
    conn.commit()
    conn.close()


def get_flashcards(topic: str = None) -> list[dict]:
    """Retrieve flashcards; optionally filter by topic."""
    conn = get_connection()
    if topic:
        rows = conn.execute(
            "SELECT * FROM flashcards WHERE topic LIKE ? ORDER BY created_at DESC",
            (f"%{topic}%",)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM flashcards ORDER BY created_at DESC"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Uploaded files log ────────────────────────────────────────────────────────

def log_uploaded_file(original_name: str, stored_name: str,
                      chunk_count: int, file_type: str) -> None:
    conn = get_connection()
    conn.execute("""
        INSERT INTO uploaded_files (original_name, stored_name, chunk_count, file_type)
        VALUES (?, ?, ?, ?)
    """, (original_name, stored_name, chunk_count, file_type))
    conn.commit()
    conn.close()


def get_uploaded_files() -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM uploaded_files ORDER BY uploaded_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
