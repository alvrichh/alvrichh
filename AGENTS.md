# AGENTS.md — alvrichh (GitHub profile README)

Guide for any AI agent working in this repo from scratch. This repo is **public** and is the profile page of GitHub user `alvrichh`. Only put in it what is already fine to show to anyone.

## What this is
- `README.md` — the profile page: about, featured projects, stack, and the "GitHub analytics" block.
- `profile/streak.svg` — streak card, regenerated daily.
- `assets/trophy.svg` — trophies card, regenerated daily.
- `profile/activity.svg` — 31-day contribution graph, regenerated daily by `scripts/activity_graph.py`.
- `.github/workflows/` — the three automations that keep those SVGs fresh.

## Automations (do not break them)
| Workflow | When (UTC) | What it does |
|---|---|---|
| `streak-stats.yml` | 03:00 daily | `DenverCoder1/github-readme-streak-stats` writes `profile/streak.svg`, then commits if it changed. |
| `activity-graph.yml` | 03:30 daily | `scripts/activity_graph.py` queries the GraphQL contribution calendar with `GITHUB_TOKEN` and writes `profile/activity.svg`. |
| `profile-trophies.yml` | 06:17 daily | Builds `assets/trophy.svg` with a **pinned** trophy generator. It patches star counts to use the public `stargazerCount`, because `GITHUB_TOKEN` cannot read other repos' stargazer connections. |

- Commits from the bot are normal (`chore(profile): refresh … `). Do not squash or rewrite them.
- If you edit a workflow, keep the schedules and the `concurrency` group in `profile-trophies.yml`.
- Workflows also run on push when their own file changes; a `workflow_dispatch` is available for manual runs.

## Working rules
- **Pull first** (`git pull --ff-only origin main`). The bot pushes often, so your local `main` is usually behind.
- **Edit the README by hand**, keep its existing layout (centred blocks, `<details>` only where it already is). Check that new images have `alt` text.
- Test the Python script locally before committing: `GH_TOKEN=<token> python3 scripts/activity_graph.py` writes `profile/activity.svg`. Without a token, pass a JSON file with `{"YYYY-MM-DD": count}` as the first argument.
- **Git:** commit as the configured user, **no `Co-Authored-By` or AI attribution lines**. Use conventional messages (`docs(profile): …`, `fix(profile): …`). Push to `main` only when the owner asks.
- Never add private data, personal contact details beyond what the README already shows, or secrets. Tokens go in repo secrets only.

## Known pitfalls
- Third-party image hosts (shields, quote generators, readme-typing) can go down. If a block in the README breaks, replace it with a local asset rather than debugging the host.
- The old activity graph service (`github-readme-activity-graph.vercel.app`) is gone; that is why `activity-graph.yml` exists. Do not reintroduce it.
- The trophy workflow fails safe: if the GitHub API check fails it keeps the previous card and exits. A red run is a signal to look at the log, not to re-run blindly.
