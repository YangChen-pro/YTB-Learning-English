"""Known-word repository keyed by lemma and POS."""

from __future__ import annotations

from pathlib import Path

from youtube_vocab.storage.database import Database

VALID_STATUSES = {"known", "learning", "ignored"}


class KnownWordsRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def add(self, lemma: str, pos: str, status: str = "known") -> None:
        if status not in VALID_STATUSES:
            raise ValueError(f"无效状态 {status!r}；请选择 known、learning 或 ignored")
        with self.database.connect() as connection:
            connection.execute(
                """INSERT INTO known_words(lemma, pos, status)
                VALUES (?, ?, ?)
                ON CONFLICT(lemma, pos) DO UPDATE SET
                    status=excluded.status, updated_at=CURRENT_TIMESTAMP""",
                (lemma.strip().lower(), pos.strip().upper(), status),
            )

    def remove(self, lemma: str, pos: str) -> bool:
        with self.database.connect() as connection:
            cursor = connection.execute(
                "DELETE FROM known_words WHERE lemma = ? AND pos = ?",
                (lemma.strip().lower(), pos.strip().upper()),
            )
        return cursor.rowcount > 0

    def list(self) -> list[tuple[str, str, str]]:
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT lemma, pos, status FROM known_words ORDER BY lemma, pos"
            ).fetchall()
        return [(str(row["lemma"]), str(row["pos"]), str(row["status"])) for row in rows]

    def filtering_keys(self) -> set[tuple[str, str]]:
        return {
            (lemma, pos) for lemma, pos, status in self.list() if status in {"known", "ignored"}
        }

    def import_file(self, path: Path, default_pos: str = "X") -> int:
        count = 0
        for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            fields = [field.strip() for field in line.replace(",", "\t").split("\t")]
            lemma = fields[0]
            pos = fields[1] if len(fields) > 1 and fields[1] else default_pos
            status = fields[2] if len(fields) > 2 and fields[2] else "known"
            self.add(lemma, pos, status)
            count += 1
        return count

    def export_file(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        lines = ["lemma\tpos\tstatus", *("\t".join(row) for row in self.list())]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
