# ruff: noqa: E501
"""Self-contained, offline HTML learning report."""

from __future__ import annotations

import json
from pathlib import Path

from youtube_vocab.models import AnalysisResult


def export_html_report(result: AnalysisResult, path: Path) -> None:
    payload = {
        "video_id": result.video_id,
        "language_code": result.language_code,
        "is_generated": result.is_generated,
        "model": result.model,
        "analyzed_at": result.analyzed_at.isoformat(),
        "study_words": [item.model_dump(mode="json") for item in result.study_words],
        "expressions": [item.model_dump(mode="json") for item in result.expressions],
        "all_words": [item.model_dump(mode="json") for item in result.all_words],
        "sentences": [item.model_dump(mode="json") for item in result.sentences],
        "warnings": result.warnings,
    }
    # Prevent caption text from terminating the JSON script element.
    data = json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c")
    path.write_text(_TEMPLATE.replace("__REPORT_DATA__", data), encoding="utf-8")


_TEMPLATE = r"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>YouTube English Study Report</title>
  <style>
    :root {
      --ink: #172421; --muted: #64706d; --paper: #f6f3eb; --card: #fffdf8;
      --line: #dedbd1; --accent: #126e63; --accent-dark: #0a4942; --warm: #e66a3c;
      --shadow: 0 12px 34px rgba(28, 48, 43, .08); --radius: 18px;
    }
    * { box-sizing: border-box; }
    body { margin: 0; color: var(--ink); background: var(--paper); font: 15px/1.65 Inter, ui-sans-serif, system-ui, -apple-system, "PingFang SC", sans-serif; }
    button, input, select { font: inherit; }
    .hero { color: white; background: linear-gradient(125deg, #082f2b 0%, #126e63 65%, #269584 100%); padding: 54px 24px 74px; }
    .hero-inner, main { width: min(1120px, calc(100% - 32px)); margin: auto; }
    .eyebrow { margin: 0 0 8px; color: #9fe2d7; font-size: 12px; font-weight: 800; letter-spacing: .14em; text-transform: uppercase; }
    h1 { max-width: 780px; margin: 0; font: 700 clamp(31px, 6vw, 60px)/1.08 Georgia, "Noto Serif SC", serif; letter-spacing: -.03em; }
    .subtitle { max-width: 720px; margin: 18px 0 0; color: #d7efeb; font-size: 16px; }
    .hero-meta { display: flex; flex-wrap: wrap; gap: 9px; margin-top: 24px; }
    .meta-pill { padding: 6px 11px; border: 1px solid rgba(255,255,255,.22); border-radius: 999px; background: rgba(255,255,255,.08); color: #eefbf8; font-size: 12px; }
    main { position: relative; margin-top: -40px; padding-bottom: 72px; }
    .stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
    .stat { padding: 21px; border: 1px solid var(--line); border-radius: var(--radius); background: var(--card); box-shadow: var(--shadow); }
    .stat strong { display: block; color: var(--accent-dark); font: 700 31px/1 Georgia, serif; }
    .stat span { color: var(--muted); font-size: 12px; }
    .workspace { margin-top: 18px; border: 1px solid var(--line); border-radius: 22px; background: var(--card); box-shadow: var(--shadow); overflow: hidden; }
    .toolbar { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; padding: 15px; border-bottom: 1px solid var(--line); }
    .tabs { display: flex; flex: 1 1 auto; gap: 4px; overflow-x: auto; }
    .tab { white-space: nowrap; padding: 9px 13px; border: 0; border-radius: 10px; color: var(--muted); background: transparent; cursor: pointer; font-weight: 700; }
    .tab.active { color: white; background: var(--accent); }
    .search { width: min(270px, 100%); padding: 9px 13px; border: 1px solid var(--line); border-radius: 10px; background: white; color: var(--ink); outline: none; }
    .search:focus { border-color: var(--accent); box-shadow: 0 0 0 3px rgba(18,110,99,.12); }
    .panel { display: none; padding: 22px; }
    .panel.active { display: block; }
    .section-head { display: flex; justify-content: space-between; align-items: end; gap: 12px; margin-bottom: 17px; }
    .section-head h2 { margin: 0; font: 700 25px/1.2 Georgia, "Noto Serif SC", serif; }
    .section-head span { color: var(--muted); font-size: 12px; }
    .grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 13px; }
    .study-card { padding: 18px; border: 1px solid var(--line); border-radius: 15px; background: #fff; }
    .card-top { display: flex; justify-content: space-between; align-items: start; gap: 10px; }
    .term { margin: 0; font-size: 21px; font-weight: 800; letter-spacing: -.02em; }
    .surface { margin-left: 7px; color: var(--muted); font-size: 13px; font-weight: 500; }
    .badge { padding: 3px 8px; border-radius: 999px; background: #e4f2ef; color: var(--accent-dark); font-size: 11px; font-weight: 800; text-transform: uppercase; }
    .meaning { margin: 11px 0 3px; color: var(--warm); font-size: 17px; font-weight: 800; }
    .explanation { margin: 0; color: #45524f; }
    blockquote { margin: 13px 0 10px; padding: 10px 12px; border-left: 3px solid #b9d9d3; background: #f7faf9; color: #30413d; }
    .card-foot { display: flex; justify-content: space-between; align-items: center; gap: 10px; color: var(--muted); font-size: 12px; }
    .rating { color: #b24c28; font-weight: 800; }
    .time-link { color: var(--accent); font-weight: 800; text-decoration: none; }
    .time-link:hover { text-decoration: underline; }
    .timeline { display: grid; gap: 0; }
    .sentence { display: grid; grid-template-columns: 80px 1fr; gap: 16px; padding: 14px 0; border-bottom: 1px solid var(--line); }
    .sentence:last-child { border: 0; }
    .sentence p { margin: 0; font-size: 16px; }
    .table-wrap { overflow-x: auto; }
    table { width: 100%; border-collapse: collapse; }
    th, td { padding: 11px 10px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }
    th { color: var(--muted); font-size: 11px; letter-spacing: .06em; text-transform: uppercase; }
    .empty { padding: 50px 20px; color: var(--muted); text-align: center; }
    .warnings { margin-top: 15px; padding: 14px 18px; border: 1px solid #efd8ae; border-radius: 13px; background: #fff7e8; color: #77501d; }
    .warnings summary { cursor: pointer; font-weight: 800; }
    footer { color: var(--muted); text-align: center; font-size: 12px; }
    @media (max-width: 760px) { .hero { padding-top: 36px; } .stats { grid-template-columns: repeat(2, 1fr); } .grid { grid-template-columns: 1fr; } .toolbar { align-items: stretch; } .tabs { order: 2; flex-basis: 100%; } .search { width: 100%; } .panel { padding: 16px; } }
    @media print { .hero { padding: 25px; } main { margin-top: 10px; } .toolbar { display: none; } .panel { display: block !important; page-break-before: always; } .workspace, .stat { box-shadow: none; } }
  </style>
</head>
<body>
  <header class="hero"><div class="hero-inner">
    <p class="eyebrow">YouTube Vocab · Study Report</p>
    <h1>把视频里真正值得记住的英语留下来。</h1>
    <p class="subtitle">词汇、固定表达与原字幕上下文集中在一页；点击时间即可回到视频对应位置。</p>
    <div class="hero-meta" id="hero-meta"></div>
  </div></header>
  <main>
    <section class="stats" id="stats" aria-label="分析摘要"></section>
    <section class="workspace">
      <div class="toolbar">
        <nav class="tabs" aria-label="报告内容">
          <button class="tab active" data-panel="words">学习词汇</button>
          <button class="tab" data-panel="expressions">固定表达</button>
          <button class="tab" data-panel="transcript">字幕时间轴</button>
          <button class="tab" data-panel="all">全部词汇</button>
        </nav>
        <input class="search" id="search" type="search" placeholder="搜索词汇、释义或字幕…" aria-label="搜索报告">
      </div>
      <section class="panel active" id="words"></section>
      <section class="panel" id="expressions"></section>
      <section class="panel" id="transcript"></section>
      <section class="panel" id="all"></section>
    </section>
    <details class="warnings" id="warnings" hidden><summary>查看分析警告</summary><ul></ul></details>
    <footer><p>由 YouTube Vocab 在本地生成 · 原始字幕始终保留</p></footer>
  </main>
  <script id="report-data" type="application/json">__REPORT_DATA__</script>
  <script>
    const data = JSON.parse(document.getElementById('report-data').textContent);
    const $ = (id) => document.getElementById(id);
    const node = (tag, cls, text) => { const n = document.createElement(tag); if (cls) n.className = cls; if (text !== undefined) n.textContent = text; return n; };
    const videoUrl = (seconds) => `https://www.youtube.com/watch?v=${data.video_id}&t=${Math.max(0, Math.floor(seconds))}s`;
    const time = (seconds) => { const s = Math.max(0, Math.floor(seconds)); return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`; };
    const link = (seconds) => { const a = node('a', 'time-link', `▶ ${time(seconds)}`); a.href = videoUrl(seconds); a.target = '_blank'; a.rel = 'noopener'; return a; };
    const searchable = (value, query) => JSON.stringify(value).toLocaleLowerCase().includes(query);
    let query = '';

    const meta = [data.video_id, data.is_generated ? 'YouTube 自动字幕' : '人工字幕', data.language_code, data.model || '本地分析'];
    meta.forEach(value => $('hero-meta').append(node('span', 'meta-pill', value)));
    [['推荐词', data.study_words.length], ['固定表达', data.expressions.length], ['去重词', data.all_words.length], ['字幕句子', data.sentences.length]].forEach(([label, value]) => {
      const card = node('article', 'stat'); card.append(node('strong', '', String(value)), node('span', '', label)); $('stats').append(card);
    });

    function heading(title, count) { const wrap = node('div', 'section-head'); wrap.append(node('h2', '', title), node('span', '', `${count} 项`)); return wrap; }
    function empty(message) { return node('div', 'empty', message); }
    function renderWords() {
      const root = $('words'); root.replaceChildren();
      const items = data.study_words.filter(item => searchable(item, query)); root.append(heading('值得学习的词', items.length));
      if (!items.length) { root.append(empty(data.study_words.length ? '没有匹配的词汇。' : '本次没有推荐词；若使用了 --no-llm，这是正常结果。')); return; }
      const grid = node('div', 'grid');
      items.forEach(item => {
        const card = node('article', 'study-card'); const top = node('div', 'card-top');
        const term = node('h3', 'term', item.lemma); term.append(node('span', 'surface', item.surface)); top.append(term, node('span', 'badge', item.pos));
        card.append(top, node('p', 'meaning', item.meaning_zh), node('p', 'explanation', item.explanation_zh), node('blockquote', '', item.evidence));
        const foot = node('div', 'card-foot'); foot.append(node('span', 'rating', `难度 ${item.difficulty}/5 · 价值 ${item.usefulness}/5`), link(item.timestamp)); card.append(foot); grid.append(card);
      }); root.append(grid);
    }
    function renderExpressions() {
      const root = $('expressions'); root.replaceChildren();
      const items = data.expressions.filter(item => searchable(item, query)); root.append(heading('值得积累的固定表达', items.length));
      if (!items.length) { root.append(empty(data.expressions.length ? '没有匹配的表达。' : '本次没有提取到固定表达。')); return; }
      const grid = node('div', 'grid');
      items.forEach(item => {
        const card = node('article', 'study-card'); const top = node('div', 'card-top'); top.append(node('h3', 'term', item.canonical_form), node('span', 'badge', item.category.replaceAll('_', ' ')));
        card.append(top, node('p', 'meaning', item.meaning_zh), node('p', 'explanation', item.explanation_zh), node('blockquote', '', item.evidence));
        const foot = node('div', 'card-foot'); foot.append(node('span', 'rating', `学习价值 ${item.usefulness}/5`), link(item.timestamp)); card.append(foot); grid.append(card);
      }); root.append(grid);
    }
    function renderTranscript() {
      const root = $('transcript'); root.replaceChildren(); const items = data.sentences.filter(item => searchable(item.text, query)); root.append(heading('字幕时间轴', items.length));
      if (!items.length) { root.append(empty('没有匹配的字幕。')); return; }
      const timeline = node('div', 'timeline'); items.forEach(item => { const row = node('article', 'sentence'); row.append(link(item.start), node('p', '', item.text)); timeline.append(row); }); root.append(timeline);
    }
    function renderAllWords() {
      const root = $('all'); root.replaceChildren(); const items = data.all_words.filter(item => searchable(item, query)); root.append(heading('全部去重词汇', items.length));
      if (!items.length) { root.append(empty('没有匹配的词汇。')); return; }
      const wrap = node('div', 'table-wrap'); const table = node('table'); const head = node('thead'); const hr = node('tr'); ['Lemma', 'POS', 'Surface forms', '次数', '首次出现'].forEach(v => hr.append(node('th', '', v))); head.append(hr); table.append(head); const body = node('tbody');
      items.forEach(item => { const row = node('tr'); row.append(node('td', '', item.lemma), node('td', '', item.pos), node('td', '', item.surface_forms.join(', ')), node('td', '', String(item.count))); const cell = node('td'); cell.append(link(item.first_timestamp)); row.append(cell); body.append(row); }); table.append(body); wrap.append(table); root.append(wrap);
    }
    function render() { renderWords(); renderExpressions(); renderTranscript(); renderAllWords(); }
    document.querySelectorAll('.tab').forEach(tab => tab.addEventListener('click', () => { document.querySelectorAll('.tab, .panel').forEach(item => item.classList.remove('active')); tab.classList.add('active'); $(tab.dataset.panel).classList.add('active'); }));
    $('search').addEventListener('input', event => { query = event.target.value.trim().toLocaleLowerCase(); render(); });
    if (data.warnings.length) { const box = $('warnings'); box.hidden = false; data.warnings.forEach(value => box.querySelector('ul').append(node('li', '', value))); }
    render();
  </script>
</body>
</html>
"""
