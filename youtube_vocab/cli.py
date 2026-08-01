"""Typer command-line interface."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from youtube_vocab.config import Settings
from youtube_vocab.errors import YTVocabError
from youtube_vocab.pipeline import analyze_video
from youtube_vocab.storage.database import Database
from youtube_vocab.storage.known_words import KnownWordsRepository
from youtube_vocab.transcripts.youtube_api import YouTubeTranscriptProvider, parse_video_id

app = typer.Typer(no_args_is_help=True, help="从 YouTube 英文字幕提取学习词汇和固定表达。")
words_app = typer.Typer(no_args_is_help=True, help="管理个人已知词库。")
app.add_typer(words_app, name="words")
console = Console()

DatabaseOption = Annotated[
    Path | None,
    typer.Option("--database", help="覆盖 SQLite 数据库路径。"),
]


def _fail(exc: Exception) -> None:
    console.print(f"[bold red]错误：[/bold red]{exc}")
    raise typer.Exit(code=1)


@app.command()
def analyze(
    video_url: Annotated[str, typer.Argument(help="YouTube URL 或 11 位视频 ID")],
    output_dir: Annotated[Path, typer.Option("--output-dir")] = Path("output"),
    model: Annotated[str | None, typer.Option("--model")] = None,
    language: Annotated[str, typer.Option("--language")] = "en",
    min_usefulness: Annotated[int, typer.Option("--min-usefulness", min=1, max=5)] = 3,
    min_confidence: Annotated[float, typer.Option("--min-confidence", min=0, max=1)] = 0.75,
    include_proper_nouns: Annotated[bool, typer.Option("--include-proper-nouns")] = False,
    no_llm: Annotated[bool, typer.Option("--no-llm")] = False,
    force: Annotated[bool, typer.Option("--force")] = False,
    database: DatabaseOption = None,
) -> None:
    try:
        settings = Settings.from_env(model=model, database_path=database)
        result, destination, cached = analyze_video(
            video_url,
            settings=settings,
            output_dir=output_dir,
            language=language,
            min_usefulness=min_usefulness,
            min_confidence=min_confidence,
            include_proper_nouns=include_proper_nouns,
            no_llm=no_llm,
            force=force,
            progress=lambda message: console.print(f"[cyan]•[/cyan] {message}"),
        )
    except (YTVocabError, OSError, ValueError) as exc:
        _fail(exc)
        return
    table = Table(title="分析完成" + ("（复用缓存）" if cached else ""))
    table.add_column("项目")
    table.add_column("结果", justify="right")
    rows = [
        ("字幕轨", result.language_code),
        ("字幕类型", "自动生成" if result.is_generated else "人工"),
        ("原始片段", str(len(result.raw_captions))),
        ("规范化句子", str(len(result.sentences))),
        ("去重词", str(len(result.all_words))),
        ("推荐词", str(len(result.study_words))),
        ("固定表达", str(len(result.expressions))),
        ("输出目录", str(destination.resolve())),
    ]
    for label, value in rows:
        table.add_row(label, value)
    console.print(table)
    for warning in result.warnings:
        console.print(f"[yellow]警告：{warning}[/yellow]")


@app.command("transcript-info")
def transcript_info(
    video_url: Annotated[str, typer.Argument()],
    language: Annotated[str, typer.Option("--language")] = "en",
) -> None:
    try:
        video_id = parse_video_id(video_url)
        document = YouTubeTranscriptProvider().fetch(video_id, language)
    except YTVocabError as exc:
        _fail(exc)
        return
    table = Table(title=f"字幕信息 · {video_id}")
    table.add_column("语言")
    table.add_column("类型")
    table.add_column("已选择")
    for track in document.available_tracks:
        table.add_row(
            f"{track.language} ({track.language_code})",
            "自动" if track.is_generated else "人工",
            "✓" if track == document.selected_track else "",
        )
    console.print(table)
    end = max((caption.start + caption.duration for caption in document.captions), default=0)
    console.print(f"片段数：{len(document.captions)}；时间范围：0.00–{end:.2f} 秒")


def _known(database: Path | None) -> KnownWordsRepository:
    return KnownWordsRepository(Database(Settings.from_env(database_path=database).database_path))


@words_app.command("add")
def words_add(
    lemma: Annotated[str, typer.Argument()],
    pos: Annotated[str, typer.Option("--pos")] = "X",
    status: Annotated[str, typer.Option("--status")] = "known",
    database: DatabaseOption = None,
) -> None:
    try:
        _known(database).add(lemma, pos, status)
        console.print(f"已保存：[bold]{lemma.lower()} / {pos.upper()}[/bold] ({status})")
    except (OSError, ValueError) as exc:
        _fail(exc)


@words_app.command("remove")
def words_remove(
    lemma: Annotated[str, typer.Argument()],
    pos: Annotated[str, typer.Option("--pos")] = "X",
    database: DatabaseOption = None,
) -> None:
    try:
        removed = _known(database).remove(lemma, pos)
        console.print("已删除。" if removed else "未找到匹配的 lemma + POS。")
    except OSError as exc:
        _fail(exc)


@words_app.command("list")
def words_list(database: DatabaseOption = None) -> None:
    try:
        rows = _known(database).list()
    except OSError as exc:
        _fail(exc)
        return
    table = Table("Lemma", "POS", "Status")
    for row in rows:
        table.add_row(*row)
    console.print(table)


@words_app.command("import")
def words_import(
    path: Annotated[Path, typer.Argument(exists=True, readable=True)],
    default_pos: Annotated[str, typer.Option("--default-pos")] = "X",
    database: DatabaseOption = None,
) -> None:
    try:
        count = _known(database).import_file(path, default_pos)
        console.print(f"已导入 {count} 条。")
    except (OSError, ValueError) as exc:
        _fail(exc)


@words_app.command("export")
def words_export(path: Annotated[Path, typer.Argument()], database: DatabaseOption = None) -> None:
    try:
        _known(database).export_file(path)
        console.print(f"已导出到 {path.resolve()}")
    except OSError as exc:
        _fail(exc)


if __name__ == "__main__":
    app()
