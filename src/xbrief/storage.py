from __future__ import annotations

import json
import sqlite3
import uuid
from pathlib import Path

from xbrief.models import FetchSummary, Post, Reply

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id TEXT PRIMARY KEY,
    tweet_id TEXT NOT NULL,
    started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at TEXT,
    summary_json TEXT
);
CREATE TABLE IF NOT EXISTS posts (
    tweet_id TEXT PRIMARY KEY,
    payload_json TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS replies (
    root_tweet_id TEXT NOT NULL,
    reply_id TEXT NOT NULL,
    parent_id TEXT NOT NULL,
    depth INTEGER NOT NULL,
    payload_json TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (root_tweet_id, reply_id)
);
CREATE TABLE IF NOT EXISTS run_replies (
    run_id TEXT NOT NULL,
    root_tweet_id TEXT NOT NULL,
    reply_id TEXT NOT NULL,
    PRIMARY KEY (run_id, reply_id),
    FOREIGN KEY (run_id) REFERENCES runs(id)
);
CREATE TABLE IF NOT EXISTS pages (
    run_id TEXT NOT NULL,
    parent_id TEXT NOT NULL,
    cursor_in TEXT NOT NULL,
    cursor_out TEXT,
    page_index INTEGER NOT NULL,
    raw_count INTEGER NOT NULL,
    unique_count INTEGER NOT NULL,
    fetched_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (run_id, parent_id, cursor_in),
    FOREIGN KEY (run_id) REFERENCES runs(id)
);
CREATE INDEX IF NOT EXISTS idx_replies_root_depth
ON replies(root_tweet_id, depth, reply_id);
"""


class Storage:
    def __init__(self, path: Path) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def create_run(self, tweet_id: str) -> str:
        run_id = str(uuid.uuid4())
        with self._connect() as conn:
            conn.execute("INSERT INTO runs(id, tweet_id) VALUES (?, ?)", (run_id, tweet_id))
        return run_id

    def save_post(self, post: Post) -> None:
        payload = post.model_dump_json()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO posts(tweet_id, payload_json) VALUES (?, ?)
                ON CONFLICT(tweet_id) DO UPDATE SET
                    payload_json=excluded.payload_json,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (post.id, payload),
            )

    def commit_page(
        self,
        *,
        run_id: str,
        parent_id: str,
        cursor_in: str | None,
        cursor_out: str | None,
        page_index: int,
        raw_count: int,
        replies: list[Reply],
    ) -> int:
        inserted = 0
        cursor_key = cursor_in or ""
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            for reply in replies:
                seen = conn.execute(
                    "SELECT 1 FROM run_replies WHERE run_id=? AND reply_id=?",
                    (run_id, reply.id),
                ).fetchone()
                conn.execute(
                    """
                    INSERT INTO replies(root_tweet_id, reply_id, parent_id, depth, payload_json)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(root_tweet_id, reply_id) DO UPDATE SET
                        parent_id=CASE
                            WHEN excluded.depth < replies.depth THEN excluded.parent_id
                            ELSE replies.parent_id
                        END,
                        depth=MIN(replies.depth, excluded.depth),
                        payload_json=excluded.payload_json,
                        updated_at=CURRENT_TIMESTAMP
                    """,
                    (
                        reply.root_tweet_id,
                        reply.id,
                        reply.parent_id,
                        reply.depth,
                        reply.model_dump_json(),
                    ),
                )
                conn.execute(
                    """
                    INSERT OR IGNORE INTO run_replies(run_id, root_tweet_id, reply_id)
                    VALUES (?, ?, ?)
                    """,
                    (run_id, reply.root_tweet_id, reply.id),
                )
                if not seen:
                    inserted += 1
            conn.execute(
                """
                INSERT INTO pages(
                    run_id, parent_id, cursor_in, cursor_out, page_index, raw_count, unique_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (run_id, parent_id, cursor_key, cursor_out, page_index, raw_count, inserted),
            )
        return inserted

    def finish_run(self, summary: FetchSummary) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE runs SET finished_at=CURRENT_TIMESTAMP, summary_json=? WHERE id=?",
                (summary.model_dump_json(), summary.run_id),
            )

    def replies_for_run(self, run_id: str) -> list[Reply]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT r.payload_json
                FROM replies r
                JOIN run_replies rr
                  ON rr.root_tweet_id=r.root_tweet_id AND rr.reply_id=r.reply_id
                WHERE rr.run_id=?
                ORDER BY r.depth ASC, r.reply_id ASC
                """,
                (run_id,),
            ).fetchall()
        return [Reply.model_validate_json(row[0]) for row in rows]

    def replies_for_tweet(self, tweet_id: str) -> list[Reply]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT payload_json
                FROM replies
                WHERE root_tweet_id=?
                ORDER BY depth ASC, reply_id ASC
                """,
                (tweet_id,),
            ).fetchall()
        return [Reply.model_validate_json(row[0]) for row in rows]

    def post(self, tweet_id: str) -> Post | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload_json FROM posts WHERE tweet_id=?", (tweet_id,)
            ).fetchone()
        return Post.model_validate_json(row[0]) if row else None

    def summary(self, run_id: str) -> dict | None:
        with self._connect() as conn:
            row = conn.execute("SELECT summary_json FROM runs WHERE id=?", (run_id,)).fetchone()
        return json.loads(row[0]) if row and row[0] else None
