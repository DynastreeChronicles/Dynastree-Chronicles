# Dynastree Chronicles

The official newsletter of the DYNASTREE dynasty league. Web only.

**Live site:** https://dynastreechronicles.github.io/Dynastree-Chronicles/

**Start here: `DYNASTREE_MASTER_STATE.md`** (in the repo root, next to this file). It holds the league rules, the voice, the open storylines and the exact steps for making an issue.

## How the site is built

Sleeper is the single source of truth for numbers. Nothing numeric is typed by hand. Words live in JSON files, and every page is generated, so never edit a generated HTML file; it is overwritten on the next build.

The GitHub Action (`.github/workflows/update-data.yml`) runs these scripts in order:

1. `scripts/sleeper_pull.py` pulls the league from Sleeper into `data/`.
2. `scripts/build_site.py` writes `index.html` and every `issues/<year>/issue-NN/index.html`. The issue page shell is `scripts/templates/issue.html`.
3. `scripts/build_managers.py` writes the manager pages: `managers/index.html` and `managers/<handle>/index.html`. It imports `build_site.py`, so it must run after it.
4. `scripts/make_brief.py` writes `data/brief.json`, the single file shared with Claude when drafting an issue.

The Action runs Tuesday 11:00 UTC and Wednesday 13:00 UTC, by hand from the Actions tab, and on any push to `main` that touches `data/issues/`, `data/issues.json`, `data/fut_cap.json`, `data/managers.json`, `data/bios/`, `scripts/`, `css/` or `js/`.

To run it locally (needs Python 3.12 and `pip install pillow`), run the four scripts above in order from the repo root.

## What you edit by hand

| File or folder | What it is |
|---|---|
| `data/issues/issue-NN.json` | All the prose for one issue. |
| `data/issues.json` | The issue index (title, dek, banner, ticker, `wire_week`). |
| `data/fut_cap.json` | Future-capital score per manager, recomputed each issue. |
| `data/bios/<handle>.json` | A manager's tagline and per-season biography. |
| `data/managers.json` | Handles, team names, avatars. Add `former_names` after a rename. |
| `css/`, `js/`, `scripts/` | Style and code. |

Everything else (`data/*.json` other than those above, `data/weeks/`, `index.html`, `issues/`, `managers/`, `data/brief.json`) is written by the Action. Do not upload or edit it.

## Issues

- `data/issues.json` lists the issues. `wire_week` is the week an issue covers (post-game); the pre-game week is `wire_week + 1`.
- `data/issues/issue-NN.json` is **prose only**: `desk`, `hero`, `zero`, headlines, takes, grades, projections, bold predictions, `wire.desk` and `prev_motw`.
- Everything else on an issue page (standings, FAAB, draft slots, final-score banner, scores, records, bench points, MVPs, match-of-the-week stats, trade assets, waiver claims, bankroll) is computed from `data/weeks/` and `data/transactions.json` at build time, as of the issue's week. The home page always shows the latest finished week.
- Waiver flags and one-liners live in `wire.waivers` as `{mgr, player, flag, note}`. The claims themselves come from Sleeper.

## Manager pages

- One page per manager, plus a hub at `managers/`. Linked from the home page nav, standings and leaderboard.
- Numbers (record, game log, transactions) come from `data/`.
- The season archive has one collapsible folder per year. Its prose comes from `data/bios/<handle>.json`; its takes, drama and desk quotes are mined automatically from every issue JSON that names the manager. A new folder appears when the league season changes or a bio file adds a year.
- Use exact handles in issue prose and keep `wire.desk` and `bank.notes` filled for all managers, because those lines feed the pages.
- **Renames:** add the old handle to `former_names` in `data/managers.json`. History stays attached to the manager, and the old `managers/<old>/` address redirects.

## MAXPF

MAXPF is **Max PF: the points of each week's best possible lineup, added up over the season.** It matches Sleeper's own Max PF and is not starters plus bench. The lowest MAXPF gets rookie pick 1.01. The pull script prints a check against Sleeper's own figure on every run; if it prints a mismatch, look at the 1.01 order before publishing.

## If the site looks wrong

Open the Actions tab, click the latest "Update league data" run and read the red step. Common causes: invalid JSON, a handle typo, or a missing file. Style changes go in `css/dynastree.css` (site and issues) or `css/managers.css` (manager pages).
