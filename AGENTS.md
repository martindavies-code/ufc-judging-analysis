# Agent Workflow Rules

## Git & Deployment Protocol
- **Always Commit and Push Changes:** At the end of every task or whenever code, data, or dashboard changes are made, run all verification checks (`pytest`, `ruff`), stage the files, commit with a clear Conventional Commit message, and push directly to `origin main`.
- **GitHub Pages Synchronization:** The live dashboard is served via GitHub Pages tracking `main` (`https://martindavies-code.github.io/ufc-judging-analysis/`). Never leave modified files or recompiled versions of `index.html` uncommitted or unpushed, as the user relies on the live site reflecting the latest codebase immediately.
