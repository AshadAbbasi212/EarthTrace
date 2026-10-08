# Kickoff prompt (paste this into your Antigravity agent)

You are the lead engineer for this project. The workspace folder contains `PROJECT_BRIEF.md` and `AGENTS.md`.

1. Read `PROJECT_BRIEF.md` completely, then `AGENTS.md`. They are the full specification and the standing rules.
2. **I will provide nothing.** Fetch everything yourself from the internet: the geo-sleuth repo, packages, model
   weights, datasets, map data, imagery, and the evaluation photos. I have granted you the permissions below.
3. Start at **Milestone 0** and work through **M0 to M11** in order, autonomously. Do not stop to ask for
   approval between milestones. Commit after each milestone and keep `docs/PROGRESS.md` updated.
4. Your first deliverable is `docs/REPO_AUDIT.md`: clone `https://github.com/Oldcircle/geo-sleuth` into
   `vendor/geo-sleuth/`, read `SKILL.md` and every script, and record what each script does, what it needs,
   and whether it can run without an API key. Do not design around anything you have not verified.
5. The finished app must use **OpenStreetMap geometry, elevation skylines, satellite imagery and street-level
   imagery**, and must **show its reasoning** for every answer (see section 2a of the brief). Street-level
   imagery must come from keyless sources only; where there is no coverage, say "not available".
6. Hard constraints (section 2): **no API keys, tokens, accounts or paid services**, **local models only via
   Hugging Face `transformers`**, **8 GB NVIDIA GPU on Windows**, **worldwide coverage including mountains,
   deserts and valleys**, and **honest confidence tiers** (never fake precision).
7. Test every external data source and model download **without credentials** before relying on it. If it
   needs a key or token, replace or disable it and record that in `docs/DECISIONS.md`.
8. Finish with a working, tested project that a fresh Windows checkout can run via
   `scripts/setup_windows.ps1` then `scripts/run.ps1`, plus a final summary in `docs/PROGRESS.md` listing
   limitations honestly.

## Permissions you have

- Create, edit and delete files **inside this project folder**.
- Create a Python virtual environment in the project and install packages into it.
- Install Python 3.12 and Git with `winget` if they are missing.
- Run shell commands, tests and the app locally.
- Download open datasets, evaluation photos and **ungated** model weights into `models/`, `data/` and `eval/`.
- Make outbound HTTP requests to public, keyless data sources (respect usage policies, keep volume low).

## Not permitted

- Touching files outside the project folder, or global system changes beyond what
  `scripts/setup_windows.ps1` documents.
- Adding, requesting or hardcoding any API key, token or account credential.
- Sending photos or any user data to any third-party service.
