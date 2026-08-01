# YouTube Vocab

一个面向中文母语英语学习者的命令行工具：输入任意 YouTube URL，优先读取人工英文字幕，在没有人工字幕时读取 YouTube 自动英文字幕；随后确定性地清理滚动重复、恢复带时间戳的句子、用 spaCy 做 lemma/POS/词频聚合，并使用 DeepSeek V4 Flash 筛选值得学习的词汇和固定表达。

## 安装

需要 Python 3.12+ 和 [uv](https://docs.astral.sh/uv/)。

### macOS / Linux

```bash
uv sync
uv run python -m spacy download en_core_web_sm
cp .env.example .env
```

### Windows PowerShell

```powershell
uv sync
uv run python -m spacy download en_core_web_sm
Copy-Item .env.example .env
```

在 `.env` 中配置（不要提交密钥）：

```dotenv
DEEPSEEK_API_KEY=你的密钥
DEEPSEEK_MODEL=deepseek-v4-flash
DEEPSEEK_BASE_URL=https://api.deepseek.com
# YTVOCAB_DB_PATH=~/.local/share/ytvocab/ytvocab.db
```

Windows 用户如果希望把数据库放在 `AppData`，可以填写完整路径：

```dotenv
YTVOCAB_DB_PATH=C:\Users\你的用户名\AppData\Local\ytvocab\ytvocab.db
```

不要把包含 API key 的 `.env` 提交到 Git。

可选的字幕备用后端：`uv sync --extra ytdlp`。它也只下载字幕。

## 使用

```bash
uv run ytvocab analyze "https://www.youtube.com/watch?v=VIDEO_ID"
uv run ytvocab analyze VIDEO_ID --no-llm --output-dir ./output
uv run ytvocab analyze VIDEO_ID --model MODEL_NAME --min-usefulness 3 --min-confidence 0.75
uv run ytvocab analyze VIDEO_ID --include-proper-nouns --force
uv run ytvocab transcript-info VIDEO_URL

uv run ytvocab words add entail --pos VERB
uv run ytvocab words remove entail --pos VERB
uv run ytvocab words list
uv run ytvocab words import known_words.txt
uv run ytvocab words export known_words.txt
```

已知词以 `lemma + POS` 为主键，状态可为 `known`、`learning`、`ignored`。导入文件支持 `lemma<TAB>POS<TAB>status`；只有一个字段时 POS 默认为通配的 `X`。所有数据库命令和 `analyze` 都支持 `--database PATH`。

`--no-llm` 不需要 API key，仍会完成字幕获取、清洗、lemma/POS、去重、词频和基础导出。相同视频默认复用数据库中最近一次完整结果；`--force` 新建分析历史，不覆盖旧 run。

## 输出

每个视频写入 `output/VIDEO_ID/`：

- `metadata.json`、`raw_captions.json`、`normalized_sentences.json`、`analysis.json`
- `all_words.csv`、`study_words.csv`、`expressions.csv`
- `anki_words.csv`、`anki_expressions.csv`
- `report.html`：可搜索、可筛选、带字幕时间轴的离线可视化报告

CSV 使用 UTF-8 BOM，包含跳转到对应秒数的 YouTube 链接。规范化句子保存 `source_caption_ids`，可回溯原始字幕。LLM 的纠错仅保存为 `original/suggested/confidence/reason` 建议，绝不覆盖原文。

分析结束后可直接双击 `report.html`。也可以使用系统命令打开。

macOS：

```bash
open output/VIDEO_ID/report.html
```

Linux：

```bash
xdg-open output/VIDEO_ID/report.html
```

Windows PowerShell：

```powershell
Start-Process "output\VIDEO_ID\report.html"
```

## Windows 支持

核心 CLI、SQLite 数据库、字幕处理、DeepSeek 分析、CSV/Anki 导出和离线 HTML 报告均支持 Windows。项目不依赖 Bash；Windows 用户应在 PowerShell 中执行示例命令。

完整的 Windows 使用流程：

```powershell
uv sync
uv run python -m spacy download en_core_web_sm
Copy-Item .env.example .env

# 编辑 .env 并填写 DEEPSEEK_API_KEY 后：
uv run ytvocab analyze "https://www.youtube.com/watch?v=VIDEO_ID" --force
Start-Process "output\VIDEO_ID\report.html"
```

已知词库命令在 Windows 上无需修改：

```powershell
uv run ytvocab words import known_words.txt
uv run ytvocab words list
uv run ytvocab words export known_words.txt
```

如果启用可选的 yt-dlp 字幕后端，请运行：

```powershell
uv sync --extra ytdlp
```

## 字幕、隐私与成本

字幕优先级为人工 `en`、`en-US`、`en-GB`、`en-CA`、`en-AU`，随后以相同语言顺序选择自动轨。主后端是 `youtube-transcript-api`；请求失败时可尝试 yt-dlp 字幕后端。程序不会下载视频或音频。

启用 LLM 时，发送的是分块后的清洗句子、时间戳和本地候选词，不会把整部超长视频一次发送给 API。字幕文本会发送到 DeepSeek API 并产生相应费用；`--no-llm` 全程不调用任何 LLM。日志不会打印 API key。

LLM 客户端连接的唯一默认地址是 `https://api.deepseek.com`，模型默认为 `deepseek-v4-flash`。项目使用 DeepSeek 官方文档推荐的 OpenAI-compatible Python SDK 作为 HTTP 客户端，但不会连接 OpenAI 或 ChatGPT。DeepSeek 的 JSON Output 会先由 Pydantic 完整校验，再进入本地 grounding 校验。

默认不运行 ASR，是为了避免下载媒体带来的带宽、运行时间、隐私和算力成本，也避免在已有字幕时引入额外识别误差。没有英文字幕时程序会明确报错。

## 已知限制

- YouTube 可能限流、封锁数据中心 IP，或对受限视频拒绝字幕访问。
- 自动字幕本身可能有识别错误；高置信度纠错只辅助分析并保留原文。
- yt-dlp 备用后端会分别尝试人工轨和自动轨；它能报告所选类型，但可用轨列表不如主后端完整。
- 句子时间由相关字幕片段时间范围估算，不是逐词对齐。
- LLM 结果受模型质量影响，但本地 grounding 会拒绝不存在的 evidence、越界时间戳和非候选词。

## 开发检查

测试完全离线，使用 fake/mocks，不访问真实 YouTube 或 DeepSeek：

```bash
uv run pytest
uv run ruff check .
uv run mypy
```
