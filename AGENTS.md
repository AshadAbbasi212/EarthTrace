# AGENTS.md: standing rules for any coding agent in this repo

The full specification is `PROJECT_BRIEF.md`. Read it first. These rules always apply.

## Hard rules
- **The owner provides nothing.** Fetch everything yourself (repo, packages, models, data, eval photos).
- **No API keys, tokens, accounts or paid services**, for AI or for data. If something needs one, do not use
  it and note it in `docs/DECISIONS.md`. Do not add key slots to `.env` or config.
- **Local models only** (Hugging Face `transformers`, ungated repos, weights downloaded once, then offline).
- Target hardware: **Windows + one NVIDIA GPU with 8 GB VRAM**. Load models one at a time; unload after use.
- **Worldwide scope**, including mountains, deserts and valleys. Never restrict to cities.
- **Use all four evidence types** and show each in the report: OpenStreetMap geometry, elevation skylines,
  satellite imagery, street-level imagery (keyless providers only; report "not available" when no coverage).
- **Show the reasoning:** every claim cites the pipeline step and the artifact file that support it.
- **Honesty over precision:** report a confidence tier and calibrated radius; return "region-level" or
  "unknown" when evidence is weak. Never fabricate a point.
- Do not edit `vendor/geo-sleuth/` in place. Wrap it with adapters in `src/geolocator/adapters/`, or add a
  patch file in `patches/`. Keep its LICENSE and attribution.
- Keep the responsible-use notice in the UI and README. Do not remove it.

## Working style
- Work through milestones M0 to M11 in order, autonomously. Commit after each milestone.
- Update `docs/PROGRESS.md` as you go. Record deviations from the brief in `docs/DECISIONS.md`.
- Test before you claim: no data source, library or model counts as working until you ran it.
- Stay inside the project folder. Install packages only into the project venv.
- Respect each data source's usage policy and licence; cache aggressively; keep request volume low.
- Prefer simple, maintainable solutions over clever ones.
- Ask the owner only about real blockers (see section 14 of the brief), after finishing everything else.
