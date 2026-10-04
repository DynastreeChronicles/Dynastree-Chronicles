# Dynastree Chronicles

the official league newsletter

## How the site is built

Sleeper is the single source of truth. Nothing numeric is typed by hand.

1. `python scripts/sleeper_pull.py` pulls the league from Sleeper into `data/` (the GitHub Action runs it Tuesday and Wednesday).
2. `python scripts/build_site.py` bakes `data/` into `index.html` and each `issues/<year>/issue-NN/index.html`.

### MAXPF

MAXPF is **Max PF: the points of each week's best possible lineup, added up over the season.** It matches Sleeper's own Max PF and is not starters plus bench. The lowest MAXPF gets rookie pick 1.01. The pull script prints a check against Sleeper's own figure on every run; if it prints a mismatch, look at the 1.01 order before publishing.

### Issues

- `data/issues.json` lists the issues. `wire_week` is the week an issue covers.
- `data/issues/issue-NN.json` is **prose only** (headlines, takes, grades, projections, bold predictions, the desk asides under each manager's waiver list in `wire.desk`, and `prev_motw`, the previous issue's Match of the Week that gets the top result card).
- Everything else on an issue page (standings, FAAB, draft slots, final-score banner, scores, records, bench points, MVPs, match-of-the-week stats, trade assets, waiver claims, bankroll) is computed from `data/weeks/` and `data/transactions.json` at build time, as of the issue's week. The home page always shows the latest finished week.
- Waiver flags and one-liners live in `wire.waivers` as `{mgr, player, flag, note}`. The claims themselves come from Sleeper.
