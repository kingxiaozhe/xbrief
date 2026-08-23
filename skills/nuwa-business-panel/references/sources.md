# Source provenance and limitations

Snapshot date: 2026-08-07.

## Upstream framework

- Nuwa: <https://github.com/alchaincyf/nuwa-skill>
- License: MIT
- Audited commit: `27642f5bfed2dc1bbf8ee59a2c1ee602a626bbd7`
- Public attention at audit time: about 29,988 stars and 4,174 forks. These counts are popularity metadata only.

Nuwa describes its output as a public-information cognitive profile and explicitly says the generated Skill is not the real person, cannot reproduce tacit intuition, and is a time-bounded snapshot.

## Method sources

### Richard Feynman

- Repository: <https://github.com/alchaincyf/feynman-skill>
- License: MIT
- Audited commit: `5ae5c5079909ef8654cc9815fe58fb3b89bfcb4c`
- Adopted methods: plain-language mechanism, naming-versus-understanding, direct demonstration, anti-self-deception, explicit uncertainty.
- Excluded: first-person roleplay, expression imitation, authority-by-persona.

### Paul Graham

- Repository: <https://github.com/alchaincyf/paul-graham-skill>
- License: MIT
- Audited commit: `8de3d2bf4e0c301ea3caf015b189307f8d8d8dc0`
- Adopted methods: concrete user need, make something people want, do things that do not scale, organic pull, smallest manual validation.
- Excluded: first-person roleplay, expression imitation, unqualified transfer of Silicon Valley startup experience.

### Charlie Munger

- Repository: <https://github.com/alchaincyf/munger-skill>
- License: MIT
- Audited commit: `2d5d7a388a0c4c7865accda39f1f2e741c886d9d`
- Adopted methods: inversion, incentives, counterevidence, bias stacking, circle of competence, `yes/no/too hard` gate.
- Excluded: first-person roleplay, expression imitation, domain judgments the source itself flags as weak.

## Reliability boundary

The upstream repositories publish substantial research notes and self-run fidelity evaluations. This supports traceability to public material, not prediction quality or commercial success. The method panel must still be tested against real outcomes, and all current-market claims require independent evidence.

## Related projects reviewed but not installed

- <https://github.com/emmazangAI/mindwiki-skills>, audited at `f366126b`. Its explicit expert-conflict design informed the panel's decision-conflict check. It was not installed because the repository has no detected license, its top-level claim that it is not roleplay conflicts with first-person roleplay instructions, and its JSON files define expected test directions rather than publishing observed test runs.
- <https://github.com/konglong87/hall-of-fame>, MIT, audited at `233cb30a`. Its dynamic routing is useful for a future optional-expert layer, but the current implementation routes into first-person persona Skills, so it is not a runtime dependency.
- <https://github.com/Wechat-ggGitHub/investment-masters-skill>, audited at `0f99e98f`. It is finance-specific, has no detected license, and its root Skill frontmatter fails validation; it is not suitable as the default commercial-opportunity panel.
- <https://github.com/zrxparley/tian-dao-tui-yan-skill>, audited at `4f492f2f`. It has no detected license, publishes unsupported accuracy tiers up to `85%+`, assigns subjective probabilities without a calibration requirement, and includes a recorder script with a hard-coded path and a runtime name error; it is excluded.
