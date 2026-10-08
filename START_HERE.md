# START HERE

1. Unzip this folder anywhere on your Windows PC and open it as a workspace in Antigravity.
2. Select your LLM (a strong coding model works best; the job is long).
3. Open `KICKOFF_PROMPT.md`, copy everything in it, paste it into the agent, and grant the permissions it asks for.

That's it. The agent downloads everything it needs from the internet and builds the project in milestones
(M0 to M11). When it finishes, it will have created `scripts/setup_windows.ps1` and `scripts/run.ps1`:
run setup once, then run the app and open the address it prints in your browser.

Before you start, make sure:
- your NVIDIA graphics driver is installed (run `nvidia-smi` in PowerShell to check),
- you have a stable internet connection and roughly 30-50 GB of free disk space for models, map and imagery caches,
- the PC stays awake while the agent works.

Please read the responsible-use notice in `PROJECT_BRIEF.md` (section 6): do not use this tool to locate
private individuals who have not consented.
