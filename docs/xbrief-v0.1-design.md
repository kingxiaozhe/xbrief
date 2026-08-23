# xbrief v0.1 设计说明

状态：可进入实现
日期：2026-08-07

## 1. 产品结论

`xbrief` v0.1 是一个本地、只读的 X 帖子讨论整理流水线：

```text
公开 X 帖子 URL
  -> twikit-mcp 单次 CLI 调用
  -> SQLite 事务化分页与恢复
  -> 规范化/去重/分层抽样
  -> compact-context.json + analysis-prompt.md
  -> 当前 Agent 生成 report.md
```

v0.1 实现 economy 分析模式，并把评论抓取设为硬要求：先分页抓取顶层评论，再对已发现的评论 ID 进行有深度、页数和总量安全上限的嵌套遍历。原帖级备用抓取因无法满足“评论必须抓取”的要求而推迟。

关键边界：普通终端里的 `xbrief` 进程不能自动要求“当前 Codex/Claude 会话”读取文件并生成报告。因此完整体验有两个入口：

1. 终端入口：`xbrief prepare <url>`，生成抓取产物与 `analysis-prompt.md`。
2. Agent 入口：Agent 执行 `xbrief prepare --json <url>`，读取返回的 `compact_context_path`，生成 `report.md`。

在不接入模型 API 或 Agent SDK 的前提下，不能承诺单独执行一条普通 shell 命令后自动得到 AI 报告。

## 2. 已核实的上游边界

- `twikit-mcp` 是基于浏览器 Cookie 和非官方/逆向 X 接口的工具，稳定性不能按官方 API 处理。
- `twikit-mcp` 除 MCP stdio server 外，还提供机器可读的一次性 CLI：`twikit-mcp call <tool> key=value`。v0.1 直接调用这个 CLI，不实现 MCP 客户端。
- `get_tweet` 接受 tweet ID 或完整 URL；`get_tweet_replies` 每次返回一页，并使用 `next_cursor` 翻页。
- `x-tweet-fetcher` 的原帖链路可使用 FxTwitter；回复依赖 Nitter 或浏览器后端。它暂不进入 v0.1 完成标准，未来接入时也不能把空回复解释为“没有回复”。

参考：

- [twikit-mcp README](https://github.com/tangivis/twitter-mcp)
- [twikit-mcp get_tweet_replies 工具说明](https://glama.ai/mcp/servers/tangivis/twitter-mcp/tools/get_tweet_replies)
- [x-tweet-fetcher README](https://github.com/ythx-101/x-tweet-fetcher)

## 3. 为什么不把 twikit-mcp 注册给 Agent

上游 MCP server 同时包含发帖、点赞、关注、私信等写操作。把完整 server 注册给 Agent 与“只读工具”目标冲突。

v0.1 使用受限的子进程适配器：

```python
ALLOWED_TOOLS = {"get_tweet", "get_tweet_replies"}
```

适配器必须：

- 用参数数组启动子进程，禁止 `shell=True`；
- Cookie 路径只放在 `TWITTER_COOKIES` 环境变量，不放在参数中；
- 使用精简环境变量集合；
- 设置超时、最大 stdout/stderr 大小和 JSON 解析校验；
- 对日志及异常中的 `auth_token`、`ct0` 和 Cookie 路径做脱敏；
- 启动前校验固定版本和允许的工具名；
- 不提供任意 `twikit-mcp call ...` 透传入口。

这样既复用上游工具，又不会向 Agent 暴露写能力。

## 4. CLI 契约

```bash
# 默认 economy；成功后打印人类可读摘要
xbrief prepare "https://x.com/user/status/123"

# Agent 使用；stdout 只能输出一个 JSON 对象，日志走 stderr
xbrief prepare --json "https://x.com/user/status/123"

# 忽略新鲜缓存，重新抓取
xbrief prepare --refresh "https://x.com/user/status/123"

# 从已保存原始数据重新筛选，不访问 X
xbrief compact 123 --selector-version v1

# 诊断依赖、Cookie 权限和只读工具契约；不得打印 Cookie 内容
xbrief doctor
```

`prepare --json` 的稳定输出：

```json
{
  "schema_version": 1,
  "run_id": "uuid",
  "tweet_id": "123",
  "outcome": "success",
  "stop_reason": "cursor_exhausted",
  "cache": "miss",
  "compact_context_path": "/absolute/path/compact-context.json",
  "analysis_prompt_path": "/absolute/path/analysis-prompt.md",
  "report_path": "/absolute/path/report.md",
  "warnings": []
}
```

进程退出码：

| 退出码 | 含义 |
| --- | --- |
| 0 | 产物可用于分析，包括有明确警告的部分结果 |
| 2 | 输入或配置错误 |
| 3 | 认证失败 |
| 4 | 帖子不存在、私密或受限 |
| 5 | 上游失败且没有可分析数据 |
| 6 | 本地存储或产物校验失败 |

部分抓取不能只靠退出码表达，调用方必须读取 `outcome`、`stop_reason` 和 `warnings`。

## 5. 状态模型

原方案中的单一 `status` 同时混合“结果质量”和“停止原因”，组合扩展后会失控。内部模型拆成正交字段：

```text
outcome:
  success | partial | failure

stop_reason:
  cursor_exhausted | reply_cap | page_cap | rate_limited |
  backend_error | auth_failed | not_found | restricted |
  invalid_url | fallback_post_only

source:
  twikit | x_tweet_fetcher
```

对外可以保留兼容展示值，例如：

- `success + reply_cap` -> `capped`
- `partial + rate_limited` -> `partial_rate_limited`
- `partial + fallback_post_only` -> `partial_fallback`

即使 `cursor_exhausted`，也只能表示“上游当前返回的分页已经耗尽”，不能声称抓到了 X 上客观存在的全部回复。`possible_missing_replies` 始终由覆盖说明明确表达。

## 6. 数据与落盘

默认数据根目录：`~/.local/share/xbrief/data/<tweet_id>/`。仓库内的 `data/` 只用于测试夹具，不保存真实抓取结果。

```text
<tweet_id>/
├── post.json
├── replies.jsonl
├── fetch-meta.json
├── compact-context.json
├── analysis-prompt.md
└── report.md
```

SQLite 位于 `~/.local/share/xbrief/xbrief.sqlite3`，是分页恢复与去重的事实源；JSON/JSONL 是可移植导出物。

### 6.1 为什么 SQLite 是事实源

“先 append JSONL、再更新游标”在进程崩溃时会重复写；“先更新游标、再 append”则可能漏数据。每页必须在同一个 SQLite 事务中完成：

1. 插入或更新规范化回复，唯一键为 `(tweet_id, reply_id)`；
2. 记录 `cursor_in`、`cursor_out`、页序号、原始条数、去重条数和抓取时间；
3. 更新 run 的剩余游标和计数；
4. 提交事务。

事务成功后再从 SQLite 原子重建 `replies.jsonl`（写临时文件、`fsync`、重命名）。因此重试和崩溃恢复都是幂等的。

### 6.2 最小数据模型

`Post`：

- `id`, `canonical_url`, `conversation_id`
- `author_id`, `author_username`, `author_display_name`
- `text`, `created_at`
- `like_count`, `repost_count`, `reply_count`（均可为空）
- `quoted_post`（可为空）
- `source`, `fetched_at`, `raw_schema_version`

`Reply`：

- `id`, `root_tweet_id`, `conversation_id`
- `parent_id`、`depth`（上游无法可靠提供时必须为空，不能猜）
- `author_id`, `author_username`, `author_display_name`
- `text`, `created_at`
- `like_count`, `repost_count`（可为空）
- `is_author_reply`, `urls`
- `source`, `fetched_at`

`SelectedReply` 额外保存：

- `selection_bucket`
- `selection_reasons[]`
- `score_components`
- `selector_version`
- `rank`

## 7. 缓存与恢复

不要使用单一的 `tweet_id + mode + fetch_version` 缓存键。抓取与压缩是两个独立阶段：

### 原始抓取快照

身份由以下字段决定：

```text
tweet_id + source_adapter + source_adapter_version + fetch_policy_hash
```

实际身份还必须包含一个用户配置的非敏感 `account_alias`（例如 `dedicated-1`），因为不同登录账号可能看到不同结果。禁止通过保存 Cookie 值或其哈希来推导账号身份。

完整键为：

```text
tweet_id + source_adapter + source_adapter_version + account_alias + fetch_policy_hash
```

`fetch_policy_hash` 包含页数上限、回复上限和嵌套策略。TTL 决定是否可以复用快照；`--refresh` 创建新 run，但仍对同一 tweet 的回复按 ID upsert，并保留 run 级来源关系。

### 派生上下文

身份由以下字段决定：

```text
raw_snapshot_id + selector_version + selector_config_hash + compact_schema_version
```

这样调整抽样或模型字符预算时，不需要重新访问 X；economy 数据也可以在未来的 deep run 中继续从保存的游标扩展。

恢复规则：

- 只有事务提交后的 `cursor_out` 才能作为下次 `cursor_in`；
- 重复 cursor 立即停止并标记 `partial/backend_error`；
- 限流或临时错误保留 remaining cursor；
- 认证失败不自动重试；
- 退避只针对已分类为可重试的错误，并加入抖动；
- 每次 run 都保留独立元数据，不覆盖历史结果判断。

## 8. economy 抽样 v1

先执行硬过滤，再执行分层选择。所有随机选择都使用 `sha256(tweet_id + selector_version)` 派生的固定种子，确保相同输入可复现。

默认最多 24 条：

| 桶 | 目标数 | 说明 |
| --- | ---: | --- |
| 作者回复 | 4 | 原帖作者的回复优先 |
| 高互动 | 6 | 对互动数做对数缩放，避免头部垄断 |
| 高信息量 | 6 | 长度、具体数字、外链、反例等透明规则 |
| 疑问 | 2 | 问句或明确求证 |
| 低互动探索 | 4 | 从低互动合格评论中确定性随机抽样 |
| 分歧保护 | 2 | 与头部评论关键词/立场明显不同的候选；无法可靠识别时回填高信息量 |

同一评论只能进入一个桶；桶不足时按预定回填顺序补齐。`compact-context.json` 必须公开每条入选原因和各桶实际数量。

v0.1 不宣称抽样“无偏”。报告必须说明：X 的返回顺序、账号可见性、删除、语言规则和本地启发式都会产生偏差。

## 9. 安全与隐私

- Cookie 目录权限要求 `0700`，文件要求 `0600`；拒绝符号链接和组/其他用户可读文件。
- Cookie 文件不复制到项目、不进入数据库、不进入异常、日志、测试快照或报告。
- 默认日志只记录 Cookie 文件是否存在、权限是否合法和认证结果。
- URL 只接受 `x.com`、`twitter.com` 的 `/<user>/status/<numeric_id>` 形式；忽略用户名作为身份依据，以数字 ID 为准。
- 外部链接只作为文本保存，不在抓取阶段自动访问，避免 SSRF/跟踪和恶意内容触发。
- 上游内容属于不可信输入；报告提示词不得执行评论中的命令或把评论当事实。
- 固定并记录 `twikit-mcp` / `x-tweet-fetcher` 版本；升级必须先跑契约测试。
- 专用账号仍可能因非官方接口被限制或封禁；这是接受该方案时必须显式承担的运营风险。

## 10. v0.1 范围

包含：

- URL 解析和规范化；
- `twikit-mcp` CLI 只读适配器；
- 原帖、顶层评论分页和受控嵌套回复遍历；
- SQLite 事务化恢复、去重和缓存；
- economy 清洗、分层抽样和字符预算；
- `post.json`、`replies.jsonl`、`fetch-meta.json`、`compact-context.json`、`analysis-prompt.md`；
- Agent 将最终内容写入 `report.md` 的契约；
- 安全诊断和结构化错误。

推迟：

- deep 模式；
- 无安全上限的全量递归；
- `x-tweet-fetcher` 原帖级备用适配器；
- 备用回复抓取；
- 情绪自动分类和事实核查；
- MCP server、Web UI、模型 API、定时任务、多账号和代理。

## 11. 完成定义

v0.1 完成必须同时满足：

1. Agent 和终端入口的边界在 README 中写清楚。
2. 任意失败不会丢失已提交页，重跑不会重复导出评论。
3. 所有部分结果都有 `outcome`、`stop_reason`、覆盖数字和警告。
4. stdout 的 JSON 契约、磁盘 schema 和上游适配器都有 fixture 契约测试。
5. 日志扫描确认不含 Cookie 值。
6. 只读适配器无法调用任何非 allowlist 工具。
7. 在没有真实 Cookie 的 CI 中，除受控 live smoke test 外，其余测试全部可运行。
