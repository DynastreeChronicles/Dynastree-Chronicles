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

## Trophies (reserved art)

Five trophies are reserved for one job each. They live in `assets/trophies/` and are mapped in `scripts/trophies.py`, the single place that says which trophy means what. Each has a full version and a `-sm` version for tight spots.

| Trophy | File | Used for |
|---|---|---|
| Lombardi Trophy | `lombardi` | League champion, once a year |
| Toilet Bowl Trophy | `toilet-bowl` | The Toilet Bowl (last-place bracket) |
| Best Manager (football with the rising arrow) | `best-manager` | Hall of Fame award shelf |
| Biggest Tank (deflated football, 1.01) | `biggest-tank` | Hall of Fame award shelf |
| Waiver Wire MVP (diamond) | `waiver-mvp` | Hall of Fame award shelf |

They are separate from the in-season rank trophies (`trophy-gold`, `-silver`, `-bronze`, `-trash`), which belong to the live standings and leaderboard. Do not use the five above for rank.

Where they appear:

- **History page, Champions wall:** Lombardi on each season's champion card. If a season has a `toilet_bowl` entry, a Toilet Bowl card follows it.
- **History page, Award shelf:** Best Manager, Biggest Tank and Waiver Wire MVP each show their own trophy.
- **Manager pages, Trophy case:** a manager's page shows a Trophy case section only once they have actually won something, so nothing appears until the first win. Champion and Toilet Bowl come from `data/history.json`. The three awards count once their season is closed, or earlier if `history.json` names the winner by hand. A live season's current leader does not get the trophy early.

To show one anywhere new, call `trophies.img("lombardi", root)` (keys: `lombardi`, `toilet_bowl`, `best_manager`, `biggest_tank`, `waiver_mvp`) instead of writing the `<img>` by hand.

Recording a Toilet Bowl in `data/history.json`, next to the champion for that season:

```json
"2026": {
  "champion": "Handle", "runner_up": "Handle", "final_score": [131.4, 118.2],
  "toilet_bowl": {"winner": "Handle", "runner_up": "Handle", "final_score": [88.1, 71.5], "note": "Optional line."}
}
```

Only `winner` is required. `winner` is whoever takes the Toilet Bowl trophy.

## On-deck issue cards

Cards for issues 18 to 36 are already in `assets/cards/` (`logo-NN.webp` is the crest "The Archive" card, `plain-NN.webp` is the number-only card). Nothing shows until that issue exists in `data/issues.json`. Then the build picks them up on its own:

- the **logo** card appears beside the issue title on the issue page;
- the **plain** card appears as the tile in the home page archive list.

Finished art always wins. If `assets/issue-card-NN.webp` or `assets/archive-issue-NN.webp` exists for an issue, it is used instead. To swap which style goes where, edit `CARD_STYLE` near the top of the issue-art helpers in `scripts/build_site.py`.

## If the site looks wrong

Open the Actions tab, click the latest "Update league data" run and read the red step. Common causes: invalid JSON, a handle typo, or a missing file. Style changes go in `css/dynastree.css` (site and issues) or `css/managers.css` (manager pages).
