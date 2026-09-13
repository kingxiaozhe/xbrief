# XBrief read-only and archive routing update

Historical scope: personal installed Skill update, not a CLI release. Target is
`skills/xbrief`; `/Users/zero/.codex/skills/xbrief` resolves to that directory.
Preserve pre-existing dirty work. No commit, push, Vault writes or credentials.

References reused: current XBrief workflow and CLI output schema, existing
method-only panel, user-supplied AI_DVD6 post and its correction-retention comment,
Yao resource-boundary method. No new dependencies or duplicate Skill.

Changes: READ by default, explicit ARCHIVE, aligned interface prompts, bounded
comment selection, no forced commercial plan, conditional null execution JSON,
method review in both modes, sparse/inaccessible source behavior, focused tests.
Archive details moved to a referenced file to keep the entrypoint lean.

Verification: 47 local pytest cases pass; 13 keyword/semantic trigger fixtures
pass with no false positives/negatives. These are static contracts and heuristic
routing checks, NOT live model execution or browser/Vault end-to-end evidence.
No fresh-session agent output evaluation has been run. Yao validate_skill.py
could not run because the available Python environments lack PyYAML; no dependency
was installed. Resource budget and formatting checks are run separately.

Rollback boundary: reverse only this task's Skill/interface/eval/test/documentation
edits; preserve all pre-existing modifications. Installed copy is a symlink, so
there is no separate installation to overwrite. Future live acceptance should
cover tool recommendation, disputed opinion, sparse comments and weak business
evidence, with both explicit saving and explicit no-save requests.

## Main integration follow-up

The approved integration combines X Article capture with XBrief Skill 0.1.2.
The generated CLI analysis prompt now follows the same depth gate and sparse-comment
rules as the Skill, with a regression check for the previously conflicting prompt.
README and changelog describe the combined behavior. No package tag, live X capture
or real Vault write is part of this integration check. Global AGENTS, personal
Skills and local workflow logs are outside the public repository change set.
