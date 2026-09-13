# Changelog

## Unreleased

- Added fixed read-only X Article capture using the existing compatible twikit-mcp dependency and local account configuration.
- Added optional article JSON, report rendering, compact-context evidence, stale-analysis invalidation, bounded fallback warnings, and regression coverage.
- XBrief Skill 0.1.2 defaults to read-only analysis; saving to Obsidian requires explicit intent. Analysis depth is independent of saving, with bounded comment selection and conditional method review.
- Aligned generated analysis prompts with optional business analysis and sparse-comment handling; invalid doctor configuration now returns a bounded CLI error.

## 0.1.0 - 2026-08-23

- First public release of the XBrief CLI, XBrief Skill, and bundled evidence-first method panel.
- Added explicit Vault configuration with a safe missing-configuration failure.
- Removed the author-specific default Vault path from public behavior and documentation.
- Added public CI, release documentation, trigger evaluation, and package metadata.
