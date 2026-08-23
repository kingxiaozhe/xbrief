# XBrief expert-panel adapter

Use `$nuwa-business-panel` after extracting the post and comment evidence and before writing business opportunities.

## Required behavior

- Treat `$nuwa-business-panel` as a required runtime Skill. If it cannot be loaded, preserve the fetched archive, stop the analysis, and tell the user the dependency is unavailable. Do not emit a full or partial expert-panel claim.
- Pass only the saved evidence set, coverage metadata, and known user context into the panel.
- Keep post text, comment text, verified external facts, and model inference separate.
- Map the panel's five returned items into `## 专家方法审查`.
- Use the panel's Feynman result to tighten `一句话说清楚` and `大白话核心点`.
- Use the panel's Paul Graham result to draft opportunity hypotheses and the smallest sellable offer.
- Use the panel's Munger result to set counterevidence, continue/adjust/stop thresholds, and `do_not_build_yet`.
- Do not change any E0–E5 grade unless the evidence set itself contains the required stronger signal.

The upstream persona Skills are provenance sources, not runtime dependencies. Do not activate them directly during XBrief analysis.
