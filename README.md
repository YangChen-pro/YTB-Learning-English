# YouTube Vocab

一个面向中文母语英语学习者的命令行工具：输入具有可用英文字幕的 YouTube URL，优先读取人工英文字幕，在没有人工字幕时读取 YouTube 自动英文字幕；随后确定性地清理滚动重复、恢复带时间戳的句子、用 spaCy 做 lemma/POS/词频聚合，并通过 OpenAI-compatible Chat Completions 接口筛选值得学习的词汇和固定表达。默认配置指向 DeepSeek，也可以连接兼容的本地网关或其他服务。

## 安装

需要 Python 3.12+ 和 [uv](https://docs.astral.sh/uv/)。

### macOS / Linux

```bash
# 推荐安装 yt-dlp 字幕备用后端；不需要时可改为 uv sync
uv sync --extra ytdlp
uv run python -m spacy download en_core_web_sm
cp .env.example .env
```

### Windows PowerShell

```powershell
# 推荐安装 yt-dlp 字幕备用后端；不需要时可改为 uv sync
uv sync --extra ytdlp
uv run python -m spacy download en_core_web_sm
Copy-Item .env.example .env
```

`en_core_web_sm` 不在项目锁定依赖中，任何后续 `uv sync` 都可能移除它。若重新同步依赖，请在最后再次执行 spaCy 模型安装命令。

在 `.env` 中配置（不要提交密钥）：

```dotenv
DEEPSEEK_API_KEY=你的密钥
DEEPSEEK_MODEL=deepseek-v4-flash
DEEPSEEK_BASE_URL=https://api.deepseek.com
# 把数据库保存在项目目录；不设置时默认为 ~/.local/share/ytvocab/ytvocab.db
YTVOCAB_DB_PATH=./data/ytvocab.db
```

配置键保留了 `DEEPSEEK_` 前缀，但底层调用的是 OpenAI-compatible Chat Completions：`POST {DEEPSEEK_BASE_URL}/chat/completions`。`DEEPSEEK_BASE_URL` 会原样传给 SDK，不会自动补 `/v1`。例如连接本地网关：

```dotenv
DEEPSEEK_API_KEY=非空占位符
DEEPSEEK_MODEL=网关支持的模型名
DEEPSEEK_BASE_URL=http://localhost:PORT/v1
YTVOCAB_DB_PATH=./data/ytvocab.db
```

客户端当前要求 `DEEPSEEK_API_KEY` 非空；即使本地网关不校验身份，也要填写一个非空占位符。接口还需要支持 `response_format={"type":"json_object"}`，并能接受 DeepSeek 风格的 `thinking` 扩展字段，因此不能假定所有 OpenAI-compatible 服务都可直接使用。

相对数据库路径以执行命令时的当前目录为基准。要把数据库和分析结果都保存在项目内，请从项目根目录运行命令；数据库将写入 `./data/`，分析结果默认写入 `./output/`。

Windows 用户如果希望把数据库放在 `AppData`，可以填写完整路径：

```dotenv
YTVOCAB_DB_PATH=C:\Users\你的用户名\AppData\Local\ytvocab\ytvocab.db
```

不要把包含 API key 的 `.env` 提交到 Git。

yt-dlp 备用后端也只下载字幕，不下载视频或音频。安装 yt-dlp 并不保证能通过 YouTube 的登录或机器人验证，具体限制见下文。

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

核心 CLI、SQLite 数据库、字幕处理、OpenAI-compatible LLM 分析、CSV/Anki 导出和离线 HTML 报告均支持 Windows。项目不依赖 Bash；Windows 用户应在 PowerShell 中执行示例命令。

完整的 Windows 使用流程：

```powershell
uv sync --extra ytdlp
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

如果后续重新运行 `uv sync` 或切换 extra，请再次安装 `en_core_web_sm`。

## 字幕、隐私与成本

字幕优先级为人工 `en`、`en-US`、`en-GB`、`en-CA`、`en-AU`，随后以相同语言顺序选择自动轨。主后端是 `youtube-transcript-api`；请求失败时可尝试 yt-dlp 字幕后端。程序不会下载视频或音频。

启用 LLM 时，发送的是分块后的清洗句子、时间戳和本地候选词，不会把整部超长视频一次发送给 API。字幕文本会发送到 `DEEPSEEK_BASE_URL` 指向的服务，并可能产生相应费用；`--no-llm` 全程不调用任何 LLM。日志不会打印 API key。

LLM 客户端默认地址是 `https://api.deepseek.com`，默认模型是 `deepseek-v4-flash`；两者都可通过 `.env` 或 `--model` 覆盖。项目使用 OpenAI Python SDK 作为 OpenAI-compatible HTTP 客户端，实际连接目标完全由 `DEEPSEEK_BASE_URL` 决定。JSON Output 会先由 Pydantic 完整校验，再进入本地 grounding 校验。

默认不运行 ASR，是为了避免下载媒体带来的带宽、运行时间、隐私和算力成本，也避免在已有字幕时引入额外识别误差。没有英文字幕时程序会明确报错。

## 已知限制

- YouTube 可能限流、封锁当前 IP，或要求登录并进行机器人验证。出现 `Sign in to confirm you’re not a bot` 时，不能据此判断视频没有字幕。
- 内置 yt-dlp 后端当前不会传递浏览器 Cookie，也没有配置 Node/EJS 挑战求解器；在受限网络环境中，普通 CLI 可能无法自动获取实际存在的字幕。
- 内置 yt-dlp 后端当前只解析 JSON3。YouTube 只返回 VTT 时，即使字幕可下载，程序也无法直接导入。
- 自动字幕本身可能有识别错误；高置信度纠错只辅助分析并保留原文。
- yt-dlp 备用后端会分别尝试人工轨和自动轨；它能报告所选类型，但可用轨列表不如主后端完整。
- 句子时间由相关字幕片段时间范围估算，不是逐词对齐。
- LLM 结果受模型质量影响，但本地 grounding 会拒绝不存在的 evidence、越界时间戳和非候选词。

## 字幕获取故障排查

字幕获取失败主要分为三类：

1. **视频确实没有英文字幕**：人工字幕和自动字幕轨都不存在。当前版本不会下载音频或运行 ASR，因此无法分析。
2. **视频有字幕，但匿名请求被拦截**：常见错误包含 `Sign in to confirm you’re not a bot`、IP blocked 或请求限流。这是访问问题，不等同于没有字幕。
3. **yt-dlp 能看到字幕，但内置后端无法导入**：浏览器 Cookie、Node/EJS 挑战求解或 VTT 格式可能是必要条件，但这些能力尚未接入当前 CLI。

排查时先运行：

```bash
uv run ytvocab transcript-info "VIDEO_URL"
```

该命令仍然依赖 `youtube-transcript-api`；如果它被 YouTube 拦截，只能说明主后端访问失败。当前项目尚未实现真实浏览器字幕后端，不应把浏览器登录态、自动绕过验证或音频 ASR 视为已有功能。

## 开发检查

测试完全离线，使用 fake/mocks，不访问真实 YouTube 或 DeepSeek：

```bash
uv run pytest
uv run ruff check .
uv run mypy
```
