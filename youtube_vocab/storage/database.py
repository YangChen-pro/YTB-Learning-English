"""SQLite schema and append-only analysis-run persistence."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from youtube_vocab.models import AnalysisResult

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS known_words (
    lemma TEXT NOT NULL,
    pos TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('known', 'learning', 'ignored')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (lemma, pos)
);
CREATE TABLE IF NOT EXISTS videos (
    video_id TEXT PRIMARY KEY,
    language_code TEXT NOT NULL,
    is_generated INTEGER NOT NULL,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS analysis_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT NOT NULL REFERENCES videos(video_id),
    model TEXT,
    prompt_version TEXT,
    analyzed_at TEXT NOT NULL,
    result_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sentences (
    run_id INTEGER NOT NULL REFERENCES analysis_runs(id),
    sentence_id INTEGER NOT NULL,
    text TEXT NOT NULL,
    start REAL NOT NULL,
    end REAL NOT NULL,
    source_caption_ids TEXT NOT NULL,
    PRIMARY KEY (run_id, sentence_id)
);
CREATE TABLE IF NOT EXISTS vocabulary_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES analysis_runs(id),
    lemma TEXT NOT NULL,
    pos TEXT NOT NULL,
    surface_forms TEXT NOT NULL,
    count INTEGER NOT NULL,
    first_timestamp REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS occurrences (
    vocabulary_item_id INTEGER NOT NULL REFERENCES vocabulary_items(id),
    surface TEXT NOT NULL,
    sentence_id INTEGER NOT NULL,
    timestamp REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS expressions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES analysis_runs(id),
    canonical_form TEXT NOT NULL,
    category TEXT NOT NULL,
    timestamp REAL NOT NULL,
    payload_json TEXT NOT NULL
);
"""


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path

    def connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.executescript(SCHEMA)
        return connection

    def latest_result(self, video_id: str) -> AnalysisResult | None:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT result_json FROM analysis_runs WHERE video_id = ? ORDER BY id DESC LIMIT 1",
                (video_id,),
            ).fetchone()
        return AnalysisResult.model_validate_json(row["result_json"]) if row else None

    def save_result(self, result: AnalysisResult) -> int:
        with self.connect() as connection:
            connection.execute(
                """INSERT INTO videos(video_id, language_code, is_generated, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(video_id) DO UPDATE SET
                    language_code=excluded.language_code,
                    is_generated=excluded.is_generated,
                    updated_at=CURRENT_TIMESTAMP""",
                (result.video_id, result.language_code, int(result.is_generated)),
            )
            cursor = connection.execute(
                """INSERT INTO analysis_runs
                (video_id, model, prompt_version, analyzed_at, result_json)
                VALUES (?, ?, ?, ?, ?)""",
                (
                    result.video_id,
                    result.model,
                    result.prompt_version,
                    result.analyzed_at.isoformat(),
                    result.model_dump_json(),
                ),
            )
            if cursor.lastrowid is None:
                raise RuntimeError("SQLite 未返回 analysis run ID")
            run_id = cursor.lastrowid
            connection.executemany(
                """INSERT INTO sentences
                (run_id, sentence_id, text, start, end, source_caption_ids)
                VALUES (?, ?, ?, ?, ?, ?)""",
                [
                    (
                        run_id,
                        sentence.id,
                        sentence.text,
                        sentence.start,
                        sentence.end,
                        ",".join(map(str, sentence.source_caption_ids)),
                    )
                    for sentence in result.sentences
                ],
            )
            for item in result.all_words:
                item_cursor = connection.execute(
                    """INSERT INTO vocabulary_items
                    (run_id, lemma, pos, surface_forms, count, first_timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        run_id,
                        item.lemma,
                        item.pos,
                        "|".join(item.surface_forms),
                        item.count,
                        item.first_timestamp,
                    ),
                )
                if item_cursor.lastrowid is None:
                    raise RuntimeError("SQLite 未返回 vocabulary item ID")
                item_id = item_cursor.lastrowid
                connection.executemany(
                    """INSERT INTO occurrences
                    (vocabulary_item_id, surface, sentence_id, timestamp) VALUES (?, ?, ?, ?)""",
                    [
                        (item_id, occurrence.surface, occurrence.sentence_id, occurrence.timestamp)
                        for occurrence in item.occurrences
                    ],
                )
            connection.executemany(
                """INSERT INTO expressions
                (run_id, canonical_form, category, timestamp, payload_json)
                VALUES (?, ?, ?, ?, ?)""",
                [
                    (
                        run_id,
                        item.canonical_form,
                        item.category,
                        item.timestamp,
                        item.model_dump_json(),
                    )
                    for item in result.expressions
                ],
            )
        return run_id
