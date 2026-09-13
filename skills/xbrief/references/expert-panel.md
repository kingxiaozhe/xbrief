# XBrief expert-panel adapter

Use `$nuwa-business-panel` for business opportunities, material effort/cost decisions, execution plans or explicit method review. Basic summaries/usefulness do not require it; saving alone does not activate it.

## Required behavior

- When the depth requires `$nuwa-business-panel`, load it before dependent conclusions. If unavailable, preserve any existing archive (create nothing in READ), stop only panel-dependent analysis and return independently supported facts with 未完成方法审查. Do not emit a full or partial expert-panel claim.
- Pass only the saved evidence set (ARCHIVE) or directly observed in-context evidence (READ), coverage metadata, and known user context into the panel.
- Keep post text, comment text, verified external facts, and model inference separate.
- Map the panel's five returned items into `## 专家方法审查` for ARCHIVE; in READ compress them into the judgment and next action, explicitly labeling method-based inference and actual panel status.
- Use the panel's Feynman result to tighten `一句话说清楚` and `大白话核心点`.
- Use the panel's Paul Graham result to draft opportunity hypotheses and the smallest sellable offer.
- Use the panel's Munger result to set counterevidence, continue/adjust/stop thresholds, and `do_not_build_yet`.
- Do not change any E0–E5 grade unless the evidence set itself contains the required stronger signal.

The upstream persona Skills are provenance sources, not runtime dependencies. Do not activate them directly during XBrief analysis.
