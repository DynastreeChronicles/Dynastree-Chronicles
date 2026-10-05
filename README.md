# Dynastree Chronicles

the official league newsletter (web only; issues 1 to 3 keep their PDFs as archive)

**Start here: `DYNASTREE_MASTER_STATE.md`** (kept next to this file in the repo root). It holds the league rules, the voice, the open storylines, the file map, and the exact steps for making an issue.

## How the site is built

Sleeper is the single source of truth for numbers. Nothing numeric is typed by hand.

1. `python scripts/sleeper_pull.py` pulls the league from Sleeper into `data/` (the GitHub Action runs it Tuesday and Wednesday, and on any push that touches issue files).
2. `python scripts/build_site.py` bakes `data/` into `index.html` and every `issues/<year>/issue-NN/index.html`. The issue page shell comes from `scripts/templates/issue.html`, so there is no hand-made HTML per issue.

3. `python scripts/make_brief.py` writes `data/brief.json`, the single file shared with Claude when drafting an issue.

### MAXPF

MAXPF is **Max PF: the points of each week's best possible lineup, added up over the season.** It matches Sleeper's own Max PF and is not starters plus bench. The lowest MAXPF gets rookie pick 1.01. The pull script prints a check against Sleeper's own figure on every run; if it prints a mismatch, look at the 1.01 order before publishing.

### Issues

- `data/issues.json` lists the issues. `wire_week` is the week an issue covers (post-game); the pre-game week is `wire_week + 1`.
- `data/issues/issue-NN.json` is **prose only**: `desk`, `hero`, `zero`, headlines, takes, grades, projections, bold predictions, `wire.desk`, and `prev_motw`.
- Everything else on an issue page (standings, FAAB, draft slots, final-score banner, scores, records, bench points, MVPs, match-of-the-week stats, trade assets, waiver claims, bankroll) is computed from `data/weeks/` and `data/transactions.json` at build time, as of the issue's week. The home page always shows the latest finished week.
- Waiver flags and one-liners live in `wire.waivers` as `{mgr, player, flag, note}`. The claims themselves come from Sleeper.
