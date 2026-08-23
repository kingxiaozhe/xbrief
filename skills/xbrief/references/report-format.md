# Report format

Write only between these markers in `index.md`:

```markdown
<!-- XBRIEF_ANALYSIS_START -->
## 一句话说清楚

...

## 大白话核心点

...

## 最核心评论（原文 + 解读）

### 1. @username：这条评论为什么核心

> 评论原文，逐字保留

- 来源：[在 X 中查看](https://x.com/...)
- 与原帖的关系：支持 / 质疑 / 补充
- 综合解读：...

## 综合判断

...

## 专家方法审查

- 费曼审查（方法推断）：大白话主张、证据缺口、最快直接测试。
- PG 审查（方法推断）：真实用户痛点、首个人工报价、需求证据缺口。
- 芒格审查（方法推断）：失败路径、激励/偏差、风险门槛。
- 关键分歧：支持行动的最强证据、反对行动的最强证据、争议假设和解决证据。
- 综合裁决：立即做 / 先验证 / 暂不建议，并给出决定性的证据等级。

## 赚钱机会与产品启发

### 机会 1：标题

- 痛点：...
- 目标用户：...
- 使用场景：...
- 现有替代：...
- 付费或损失信号：...
- 支持证据：...
- 反对证据：...
- 信息类型：事实 / 观点 / 推断
- 证据等级：E0–E5
- 置信度：低 / 中 / 高
- 未知项：...
- 最小验证实验：...

## 最值得先验证的方向

...

## 如果建议你落地：执行方案

- 推荐结论：立即做 / 先验证 / 暂不建议
- 为什么适合你：仅使用已知上下文
- 首个可售卖形态：...
- 目标客户：...
- 获客入口：...
- 价格假设：...（明确待验证）

### 第 1–7 天

1. ...

### 第 8–30 天

1. ...

### 继续、调整和停止标准

- 继续：...
- 调整：...
- 停止：...
- 当前不要做：...

## 抓取覆盖和局限

...
<!-- XBRIEF_ANALYSIS_END -->
```

Keep the report concise enough to read in Obsidian. Link to `[[comments]]` when the reader needs the complete archive. Attribute representative comments by username and avoid long verbatim reproductions.

The expert panel is a method audit, not roleplay. Do not write as Feynman, Paul Graham, or Charlie Munger, and do not imply that the real person reviewed the post. Evidence grades and source records always outrank panel judgments.

Use `评论区共识` only when stance coverage or counts support it. Otherwise write `入选评论中的重复主题` and state the sampling limit.

For the 3–6 selected core comments, verbatim text is required because the reader asked to see the evidence. Quote only the relevant saved comment, preserve its wording, and link its X source. Do not reproduce the full discussion or quote comments merely because they have high engagement.

Evidence grades:

- E0: author claim, likes, or generic agreement only
- E1: one concrete user pain or ordinary question without explicit current cost or intent to buy
- E2: repeated by independent users or posts
- E3: explicit current spend, quantified loss, recurring costly workaround, migration, or vendor-directed price request/purchase intent; a generic question or request for free advice is not E3
- E4: recurrence across platforms or time
- E5: interview, preorder, paid pilot, or verified revenue
