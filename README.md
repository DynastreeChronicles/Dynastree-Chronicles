# Dynastree Chronicles

The official newsletter of the DYNASTREE dynasty league: a 12-team, superflex dynasty league on Sleeper. Web only, one page per issue, plus manager pages, a Hall of Fame, a draft and trade ledger, and a receipts archive.

**Live site:** https://dynastreechronicles.github.io/Dynastree-Chronicles/

---

## Contents

1. [How this README and the master state file fit together](#1-how-this-readme-and-the-master-state-file-fit-together)
2. [How the site works](#2-how-the-site-works) (see also "Automation at a glance" above it)
3. [Repo map](#3-repo-map)
4. [The GitHub Action](#4-the-github-action)
5. [Build scripts](#5-build-scripts)
6. [What you upload and what you never touch](#6-what-you-upload-and-what-you-never-touch)
7. [Making an issue](#7-making-an-issue)
8. [Issue data](#8-issue-data)
9. [Seasons and volumes](#9-seasons-and-volumes)
10. [The pages](#10-the-pages)
11. [MAXPF](#11-maxpf)
12. [Trophies](#12-trophies-reserved-art)
13. [On-deck issue cards](#13-on-deck-issue-cards)
14. [Site conventions: accessibility, fonts, meta tags, privacy](#14-site-conventions)
15. [Adding a new page](#15-adding-a-new-page)
16. [Running it locally](#16-running-it-locally)
17. [Backups](#17-backups)
18. [If the site looks wrong](#18-if-the-site-looks-wrong)

---

## 1. How this README and the master state file fit together

There are two documents, and they have different jobs.

| File | Audience | Purpose |
|---|---|---|
| `README.md` (this file) | A person opening the repo | What the site is, how it is built, what each folder and script does, what to upload, how to fix problems. |
| `DYNASTREE_MASTER_STATE.md` | A fresh Claude chat (and you) | The operating manual for making each issue: the league's rules and identity, the voice, the issue JSON schema, sort laws, open storylines, the per-issue checklist. |

Rules for keeping them in step:

* **The master state file is the authority for anything about league content and the issue workflow** (rules, voice, schema, steps for an issue). This README only summarises those and points to the matching master section.
* **This README is the authority for how the repo and the site are put together** (folders, scripts, the Action, conventions). The master state file keeps a shorter copy of the same facts in its sections 2, 3 and 6.
* **When code, the workflow, or a page changes, update both.** The master state file's section 14b lists exactly which sections to touch.
* If the two ever disagree, the code wins. Read the script, fix whichever document is wrong, and fix the other one in the same commit.

---

## Automation at a glance

* **Automatic on every Action run:** standings, records, MAXPF, manager pages and their FantasyCalc portfolio values, the Hall of Fame, the Ledger and its pick grades, Receipts, drafts, the champion, closing a season, and `brief.json`.
* **One bundle per issue (made in a Claude chat):** `issue-NN.json` (including `rulings` and `receipts`), the `data/issues.json` entry and the 12 bios.
* **Once a year:** the volume `story` in `data/history.json`, and `"season_final": true` on the season-review issue.
* **By hand, rarely:** `data/settings.json` when league rules change, a hand verdict or trade obituary in `data/ledger.json`, a Toilet Bowl entry, and a rename the pull cannot match.

---

## 2. How the site works

Sleeper is the single source of truth for numbers. Nothing numeric is typed by hand. Words live in JSON files. Every page is generated, so never edit a generated HTML file: the next build overwrites it.

```
Sleeper API --scripts/sleeper_pull.py--> data/<season>/*.json (+ draft.json, draft_meta.json, result.json), data/managers.json, assets/avatars/   all numbers
data/ + data/issues/<season>/*.json  --scripts/build_site.py--> index.html + issues/<season>/issue-NN/index.html
data/ + data/bios/                   --scripts/build_managers.py--> managers/index.html + managers/<handle>/index.html
FantasyCalc API + Sleeper rosters   --scripts/pull_values.py--> data/market/fantasycalc.json + data/<season>/portfolio.json   market values, manager portfolios (read by build_managers.py and make_brief.py)
all seasons + data/history.json      --scripts/build_history.py--> history/index.html
Sleeper stats + projections         --scripts/pull_player_stats.py--> data/stats/<season>.json
snapshots + trades + drafts + stats --scripts/ledger_values.py--> data/market/ledger_values.json   FantasyCalc value of every trade and pick, then and now
ledger_values.json + data/ledger.json --scripts/build_ledger.py (+ pick_grades.py)--> ledger/index.html   trade values and value-based pick verdicts
issue JSON (receipts, rulings)      --scripts/build_receipts.py, build_history.py (via auto_data.py)--> receipts/ and history/
all of the above                     --scripts/make_brief.py--> data/brief.json   (the one file shared with Claude)
chat log + master state + brief.json --Claude--> data/issues/<season>/issue-NN.json (incl. rulings + receipts) + data/issues.json + bios   all words
```

Two rules follow from this:

* **Numbers:** if a number looks wrong, the Sleeper data or the issue JSON is wrong or stale. Fix the source and rebuild. Never patch a number into prose.
* **Words:** prose lives only in the issue JSON, the bios, and the hand-entered files in section 6.

The data is baked into the HTML at build time, so pages do not depend on a fetch succeeding. Issue pages still use a small script (`js/issue.js`) to draw several sections from JSON that is embedded in the page (see section 14).

---

## 3. Repo map

```
.github/workflows/update-data.yml   the Action (section 4)
assets/                             images: crests, badges, trophies, grade art, avatars, issue cards (not in zips; large)
css/
  dynastree.css                     the stylesheet for every page
  managers.css, history.css,        extra styles, loaded only by the page that needs them
  ledger.css, receipts.css
js/
  issue.js                          draws the dynamic sections of an issue page
  site.js                           home page icons and the standings sort toggle
  nav.js                            The Vault dropdown
data/
  seasons.json                      season registry: volume, league id, active or closed
  settings.json                     league settings shown on the home page
  managers.json                     everyone who has ever been in the league
  issues.json                       issue index: title, dek, banner, ticker, weeks
  history.json                      permanent league history (champions, prediction results, awards)
  ledger.json                       pick verdicts, trade obituaries, grading rules
  receipts.json                     extra hot takes for the Receipts page
  brief.json                        the one file shared with Claude (written by the Action)
  bios/<handle>.json                desk bio for each manager
  issues/<season>/issue-NN.json     all prose for one issue
  issues/issue-template.json        empty issue schema
  <season>/                         one folder per season: league, standings, efficiency, transactions,
                                    schedule, draft, weeks/week-NN.json
  stats/<season>.json               NFL stats used for auto-grading draft picks
  market/fantasycalc.json           live FantasyCalc value index, top 1,000 players and picks
  market/snapshots/<date>.json      one FantasyCalc snapshot per pull (what values are looked up from, as of a date)
  market/ledger_values.json         FantasyCalc value of every trade and draft pick (written by ledger_values.py)
  <season>/portfolio.json           manager portfolios, crash flags and value history (inside each season folder)
  <season>/wealth.json              Wealth Index: roster, pick and total value per team for each finished week
scripts/                            the build (section 5)
  templates/issue.html              the shell every issue page is built from
index.html                          home page (shell + generated sections)
404.html                            branded not-found page (hand-written; GitHub Pages serves it for any bad address; uses <base href="/Dynastree-Chronicles/">)
issues/<season>/issue-NN/           one generated page per issue
managers/                           the hub and one generated page per manager
history/  ledger/  receipts/        generated pages
DYNASTREE_MASTER_STATE.md           the operating manual (section 1)
```

The zip you share with Claude can leave out `assets/`; Claude never needs the images to change text, data, scripts, or styles. It just cannot check how art looks.

---

## 4. The GitHub Action

`.github/workflows/update-data.yml` ("Update league data") does all the work. You never run a script yourself.

**It runs:**

* Tuesday 11:00 UTC (after Monday Night Football) and Wednesday 13:00 UTC (after stat corrections).
* By hand: **Actions** > "Update league data" > **Run workflow**.
* Automatically on any push to `main` that touches `data/issues/**`, `data/issues.json`, `data/seasons.json`, `data/managers.json`, `data/settings.json`, `data/history.json`, `data/ledger.json`, `data/receipts.json`, `data/bios/**`, `scripts/**`, `css/**`, or `js/**`.

**Steps, in order:**

1. Check out the repo, set up Python 3.12, `pip install pillow` (used only for avatar images).
2. `sleeper_pull.py` (Sleeper data)
3. `pull_values.py` (FantasyCalc values and portfolios; allowed to fail without failing the run)
4. `build_site.py` (home and issue pages)
5. `build_managers.py` (manager pages)
6. `build_history.py` (Hall of Fame)
7. `pull_player_stats.py` (allowed to fail without failing the run)
8. `ledger_values.py` (FantasyCalc values for trades and picks; allowed to fail without failing the run)
9. `build_ledger.py` (ledger)
10. `build_receipts.py` (receipts)
11. `make_brief.py` (the one-file brief)
12. Commit `data/`, `index.html`, `issues/`, `managers/`, `history/`, `ledger/`, `receipts/` and `assets/avatars/` as `dynastree-bot`, then push.

**Daily snapshot workflow (`.github/workflows/daily-values.yml`).** A second, lighter Action runs every day at 09:30 UTC (and by hand from the Actions tab). It runs `pull_values.py`, `ledger_values.py`, then rebuilds only `build_site.py`, `build_managers.py` and `build_ledger.py`, and commits as `dynastree-bot`. Result: a FantasyCalc snapshot every day, so portfolio charts, sparklines, the Wealth Index and "value at the time of the trade" all have daily resolution. It shares the `update-league-data` concurrency group with the main workflow, so the two queue instead of racing. Snapshots are about 30 KB a day (roughly 11 MB a year) and are never pruned, because older trade and pick values are looked up from them.

**One run at a time.** The workflow has a `concurrency` group, so overlapping triggers queue instead of racing. If you upload files while the Tuesday run is mid-build, your upload's run waits its turn and then rebuilds with your files. A queued or "pending" run is normal, not an error. The commit step also pulls and retries the push up to three times, so a late upload cannot make the bot's push fail on its own. A push made by the bot does not trigger another run, so there is no loop.

**If a run goes red,** open the run, find the red step, and read its log. A red `Build ...` step means that script failed; the usual causes are invalid JSON, a handle typo, or a missing file.

---

## 5. Build scripts

All scripts run from the repo root, in the order below, and read only from `data/`.

| Script | Reads | Writes | Notes |
|---|---|---|---|
| `sleeper_pull.py` | Sleeper's public API | `data/<season>/*` (incl. `draft_meta.json`, `draft.json` when missing, `result.json` once the champion is decided), `data/managers.json`, `assets/avatars/*.webp`, and `data/seasons.json` when it closes a season | Finds the league by name; no league id needed. Prints the MAXPF check. Closes the season when the champion is decided and the review issue (`season_final`) exists. A missing league is a warning, not a failure. |
| `seasons.py` | `data/seasons.json` | (library) | Season registry and paths; migrates the old flat layout once. |
| `build_site.py` | `data/`, `scripts/templates/issue.html` | `index.html` (between its `<!--MARKER-->` comments), every `issues/<season>/issue-NN/index.html` | Prints `note (issue NN): ...` lines that flag mismatches between prose and data. |
| `pull_values.py` | FantasyCalc API, Sleeper rosters and traded picks | `data/market/fantasycalc.json`, `data/<season>/portfolio.json` | Runs right after `sleeper_pull.py`; allowed to fail without failing the run. Skips a closed season. See "Market values and portfolios" below. |
| `build_managers.py` | `data/`, bios, issue JSON, `portfolio.json` | `managers/` | Imports `build_site.py`, so it runs after it. Draws the Portfolio value section on each page and "The market" section of the home page (`index.html`, between `<!--MARKET-->` markers). |
| `build_history.py` | every season, `result.json`, `data/history.json`, `data/settings.json`, issue `rulings` | `history/index.html` | Permanent; never resets. |
| `trophies.py` | (library) | none | The single place that says which trophy means what. |
| `pull_player_stats.py` | Sleeper stats and projections | `data/stats/<season>.json` | Points, games, position rank and Sleeper's projected points for every drafted player. Network trouble, or no projections, is a warning. |
| `ledger_values.py` | `data/market/snapshots/`, every season's transactions, draft, draft_meta, stats (final flag only), `data/ledger.json` | `data/market/ledger_values.json` | Values every trade (at the trade and latest) and every pick (at the pick and at each locked review point). See "Ledger values" below. |
| `market.py` | (library) | none | FantasyCalc helpers: name keys, pick parsing and valuation, dated snapshots, the as-of-a-date lookup. |
| `build_ledger.py` | draft, draft_meta, stats, `ledger_values.json`, `data/ledger.json`, issue JSON | `ledger/index.html` | Shows trade values and grades picks by FantasyCalc value through `pick_grades.py`. |
| `build_receipts.py` | issue JSON (`receipts`, `rulings`), `data/history.json`, `data/receipts.json` | `receipts/index.html` | |
| `make_brief.py` | everything above | `data/brief.json` | Adds no new facts; gathers and summarises, including `predictions_to_rule`, `season_end` and `market_portfolios`. |
| `auto_data.py` | issue JSON | (library) | Merges each issue's `rulings` and `receipts` into History and Receipts. |
| `season_events.py` | Sleeper JSON | (library) | Reads a finished draft and a decided championship; no network, testable offline. |
| `pick_grades.py` | `ledger_values.json` rows | (library) | The value-based pick grading rules (`grade_pick_value`); the older production-based grader stays in the file for reference only. |

### Market values and portfolios

`pull_values.py` gives every manager a portfolio value, using [FantasyCalc](https://www.fantasycalc.com) dynasty trade values (built from real trades) for this league's format: superflex, 12 teams, full PPR (the `FORMAT` constant at the top of the script).

* **What it writes.** `data/market/fantasycalc.json` is the live index of the top 1,000 players and picks, overwritten every run. `data/<season>/portfolio.json` holds each manager's total, position split, top holdings, IR exposure, status flag and rank, plus a `history` of one snapshot per run (the last 120 are kept; a second run on the same day replaces that day's snapshot). A closed season is frozen.
* **What it values.** Every rostered player matched by Sleeper id, and every future pick the manager owns after trades (Sleeper's `traded_picks`). Players outside the top 1,000 count as 0 and are tallied as `off_index`. FantasyCalc lists picks as players with position `PICK` and names like "2027 1st (Mid)", "2028 2nd" or "2027 Pick 1.05"; `parse_pick` in the script reads all three. For the next draft the tier comes from the original owner's current draft slot in `standings.json` (slots 1-4 Early, 5-8 Mid, 9-12 Late), using the exact `Pick R.SS` value when FantasyCalc has one. Later drafts use FantasyCalc's untiered pick, then Mid. A pick with no FantasyCalc value counts as 0 and is printed as a warning ("Picks with no FantasyCalc value"). Each manager's owned picks, with a "via" tag for acquired ones, are listed in `pick_list` and shown on the manager page.
* **The two numbers behind the flag.** `move30` is the 30-day change in value of the players held now, from FantasyCalc's own trend, so trades do not move it. `sidelined` is the value sitting on IR or on players Sleeper marks Out, IR, PUP, Doubtful or Sus. FantasyCalc dynasty values react slowly to injuries, which is why IR exposure is its own number. `since_change` is the change since the last snapshot at least 5 days old and does include trades; it is empty until the second weekly run.
* **Status flags.** `crash` when the 30-day market move is -5% or worse, or 25% or more of the portfolio is sidelined. `correction` at -2.5%, `bull` at +5%, otherwise `stable`. Change the thresholds in the constants at the top of `pull_values.py`, and the headline wording in the `STATUS` table in `build_managers.py`.
* **Where it shows.** A "Portfolio value" section on every manager page (chart, position split, biggest holdings) and a ranked "The Market" section on the home page (between Transactions and Rules, with its own item in the top nav and a collapsible legend that explains the columns and the status flags). Both portfolio legends are collapsible. The portfolio chart has a caption of chips (period, low, high, change). The desk file ends with an automatic **The balance sheet** card (`wealth_line()` in `build_managers.py`): wealth rank, share on IR, share in picks, the 30-day market move, and the rank and value change since the previous Wealth Index week; nothing to write by hand. Every stat tile also shows its league rank as a label in the corner, so the colour is never the only signal. The Biggest holdings table sorts by Pos, Value (default) or 30d; Draft picks owned always shows at least 9 picks, with Show all beyond that. The season stat tiles on a manager page are shaded by the manager's rank in the league for that category (green 1st, slate middle, red last; hover for the rank). The direction of each tile (for example lower Points against is better) is the `TILE_HIGHER` table in `build_managers.py`. Each season on a manager page is split into collapsible sections in this order: The season and Game log (open), then Transactions, The takes, The drama and What the desk said (closed). A link to `#log`, `#tx` or `#desk` opens its section. The Show all buttons are handled by `js/nav.js`, the only script manager pages load. The holdings and picks tables show the top 6 players and top 8 picks, with a "Show all" button for the full roster (defenses are never listed); the full list is `assets` in `portfolio.json`. Both disappear quietly if `portfolio.json` is missing. `brief.json` gets `market_portfolios` for the next issue.
* **Trend column.** The Market table has a sparkline per manager (the last 14 snapshots from `portfolio.json` history, which keeps about a year). A dash until two snapshots exist.
* **Season-end wealth.** The first run after a season is closed copies that season's last Wealth Index week into `data/history.json` (`seasons.<year>.wealth_final`: week, date, and each team's roster, picks and total). It is written once and never edited, one point per season for a multi-year dynasty arc.
* **Credit.** The page links to FantasyCalc as the source.

### Issue trade values (locked per issue)

**Freeze rule.** Every FantasyCalc number an issue shows is frozen the first time that issue is built: the Hypothetical Trade Machine and graded-trade values, and the Wealth index and Draft order tabs (this week's and last week's Wealth rows and the draft-slot values). All of it is stored in `data/issues/<year>/values-NN.json`, each part is written once, and a part already in the file is never recomputed, so market moves, new snapshots and rebuilds cannot change a published issue. A part that could not be computed at first build (no snapshot or no Wealth row yet) is filled in the first time its data exists. Delete a values file only to recompute that issue on purpose.

From the issue named in `data/settings.json` > `issue_values_from` (`[2026, 6]`, so Issue 6 onward) the freeze rule above applies. Earlier issues have no values file and are untouched; they keep reading the live Wealth rows for their own week only, which stop changing once the following week is final.

* **Hypothetical trades:** the current value of what each side sends, a "value edge" line, and how many assets could be valued. Players are matched by name; picks like "2027 1st-round pick" use FantasyCalc's value for that pick (a "(from Name)" suffix uses that team's draft slot). FAAB, "depth WR" and other unnamed assets are left out and the card says how many assets were valued.
* **Graded trades:** per side, the value at the time of the trade and the value when the issue ran, with the percent change and a value edge line for both moments. The trade is found in `transactions.json` by the two managers and the issue week. A `~` means the value at the trade is an estimate (see Ledger values).
* **Needs data:** nothing is written until at least one snapshot exists in `data/market/snapshots/`.

### Wealth Index (third standings tab)

The standings block, on the home page and in every issue, has a third tab, **Wealth index**: every team ranked by total FantasyCalc dynasty asset value, split into **Roster value**, **Draft capital** and **Total wealth**, with rank movement (MOV) and the change in total wealth since the previous tracked week. It has its own collapsible "How to read the Wealth Index" legend.

* **Data.** `pull_values.py` writes `data/<season>/wealth.json`: one entry per finished NFL week (`weeks.<N>` with `date` and each manager's `roster`, `picks`, `total`). The entry for the newest finished week is rewritten on every run until the next week finishes, then it is frozen. Movement compares a week with the nearest earlier week on file; the first tracked week shows a dash. Each week entry also stores `slots`, the FantasyCalc value of each round-1 draft slot (1.01 to 1.12), which feeds the **Draft capital** column of the Draft order tab (the per-slot Pick value column was removed; `slots` is still saved) (same pick values as The Market and the manager pages; an issue with no entry for its week has neither column). Draft capital is the combined value of every pick the team owns. The Standings order tab has PF then PA then FAAB. The old FUT CAP score is gone: nothing in the site, the brief or the workflow uses `fut_cap.json` any more, and it is no longer part of an issue bundle (delete `data/<season>/fut_cap.json` if it is still in the repo).
* **Where it shows.** The home page shows the newest week on file. An issue page shows its own week; if that week was never saved (every issue before the feature existed), the tab is simply not there. Built by `wealth_view()` in `build_site.py`; the tab toggle is in `js/site.js`.

### Ledger values (trades and pick verdicts)

FantasyCalc only serves current values, so `pull_values.py` also saves a dated snapshot on every run (`data/market/snapshots/YYYY-MM-DD.json`, about 30 KB each; a second run the same day replaces that day's file, and it keeps saving after a season closes). `ledger_values.py` looks values up "as of" a date from those snapshots.

* **As-of lookups.** A real snapshot within 3 days of the event counts as exact. Before the first snapshot there is nothing to read, so the lookup builds an estimate from the first snapshot's own 30-day trend (value minus trend is roughly the value 30 days earlier). Anything older than that uses the nearest value on file. The pages mark anything that is not exact with a `~`. This assumes FantasyCalc's `trend30Day` is the 30-day change in value.
* **Trades.** For each side, the combined value of what it received at the time of the trade and in the latest pull, a per-asset breakdown, and a one-line value edge (who came out ahead then, who is ahead now). FAAB has no value. Picks inside trades use the tier of the original owner's draft slot, as on the manager pages.
* **Pick verdicts.** `ratio = value at the review point / max(value at pick, floor)`. A hit is at or above `grading.value.over` (1.15), a bust at or below `grading.value.under` (0.70), otherwise mid. Picks after `late_round` cannot be busts. The floor (500) stops a near-zero pick from looking like a miracle. All three numbers are in `data/ledger.json` under `grading.value`. `grading.hit` now only lists which positions are graded (QB, RB, WR, TE).
* **Review points.** A rookie draft gets three verdicts, one per season (pick year, +1, +2). Each is judged once its NFL season is final (the `final` flag in `data/stats/<season>.json`) and is then locked in `ledger_values.json`, so later market swings never change it. The 2026 startup draft gets one verdict, locked when the 2026 season is final, filed in Volume 2 Issue 1. A hand verdict in `ledger.json` still overrides.
* **Honest limits.** Early on, every trade and the startup draft pre-date the first snapshot, so they show estimated values (~). A trend-based estimate only reaches about 30 days back; older events show the nearest value on file.

Every script has a docstring at the top that says what it does, what it reads, and where it writes.

---

## 6. What you upload and what you never touch

**Hand-written or Claude-written (you upload these):**

| File | What it is |
|---|---|
| `data/issues/<season>/issue-NN.json` | All prose for one issue. New each issue. |
| `data/issues.json` | The issue index. Replaced each issue. |
| `data/bios/<handle>.json` | A manager's tagline, desk file, and per-season story. Normally all 12 each issue. |
| `data/history.json` | Optional now: the volume `story`, `awards` and `toilet_bowl` entries, hand prediction overrides. The champion and prediction results come from `result.json` and the issue files. |
| `data/ledger.json` | Grading thresholds, plus exceptions only: a hand verdict over an automatic grade, and trade obituaries. |
| `data/receipts.json` | Optional: extra hot takes added by hand. Normal hot takes ride in each issue file. |
| `data/settings.json`, `data/seasons.json`, `data/managers.json` | Edit only when a rule, season, or handle changes. |
| `css/`, `js/`, `scripts/` | Style and code. Claude will name the exact path for every file it changes. |
| `DYNASTREE_MASTER_STATE.md`, `README.md` | The two documents in section 1. |

**Written by the Action (never upload or edit):** `index.html` between its markers, `issues/`, `managers/`, `history/`, `ledger/`, `receipts/`, `data/brief.json`, `data/stats/`, `data/market/`, `data/<season>/` (except `fut_cap.json`), and `assets/avatars/`.

When Claude changes site code, it hands back only the edited files and says where each one goes. Upload just those; do not re-upload the whole repo.

---

## 7. Making an issue

The full procedure is in `DYNASTREE_MASTER_STATE.md` sections 1, 3 and 4. In short:

1. Wait for the Tuesday or Wednesday Action run (or run it by hand) and check `data/brief.json` says `ready_for_new_issue: true`.
2. Start a Claude chat with the master state file, `brief.json`, and the new chat log.
3. Claude shows a data summary, you confirm, Claude returns the issue files and the updated master.
4. Upload the files to the paths Claude gives you, in one commit. The Action rebuilds the whole site, including every manager page.
5. Check the live site, then update the master state file's checklist (section 14).

---

## 8. Issue data

* `data/issues.json` lists the issues, newest first. `wire_week` is the post-game week; the pre-game week is `wire_week + 1`. Each entry needs `"year"`.
* `data/issues/<season>/issue-NN.json` is **prose only**: `desk`, `hero`, `zero`, headlines, takes, grades, projections, bold predictions, `wire.desk`, `bank.notes`, and `prev_motw`. The full schema is `DYNASTREE_MASTER_STATE.md` section 9; copy `data/issues/issue-template.json` to start one.
* Two bundled lists in the issue file replace separate uploads: **`rulings`** settles earlier issues' bold predictions (each `{issue, i, result, note}`; `brief.json` > `predictions_to_rule` lists what is open) and **`receipts`** carries hot takes from the chat log (each `{who, text, context, status, note}`). History and Receipts read them straight from every issue.
* Everything else on an issue page (standings, FAAB, draft slots, scores, records, bench points, MVPs, match-of-the-week stats, trade assets, waiver claims, bankroll) is computed at build time from `data/<season>/` as of the issue's week. The home page always shows the latest finished week.
* Waiver flags and one-liners live in `wire.waivers` as `{mgr, player, flag, note}`; the claims themselves come from Sleeper.
* Use exact handles everywhere (`C33DeezNutzz`, `fumbduckdumbfuck`, `CMac91`).
* **Renames:** add the old handle to `former_names` on the person's entry in `data/managers.json`. History stays attached and the old `managers/<old>/` address redirects. The pull detects most renames itself (same Sleeper user id) and prints `rename detected:`.

---

## 9. Seasons and volumes

Volume N is season N. Volume 1 is 2026. Issue numbers restart at 1 each volume.

* Each season has its own folder under `data/` (`data/2026/`, `data/2027/`, and so on). Prose is under `data/issues/<season>/`.
* `data/seasons.json` is the one switch. The newest season that is not `"closed"` is the active season; the pull, the brief and the issue workflow all use it. A closed season is frozen.
* **Closing a volume is automatic.** When Sleeper's winners bracket has a champion the pull writes `data/<season>/result.json`; History picks the champion, runner-up and score up from it. When the season-review issue is published with `"season_final": true` in its `data/issues.json` entry, the same run sets the season to `closed` with a `closed_at` timestamp, and the next pull opens the next volume. Only the volume `story` in `data/history.json` is hand-written (Claude does it once a year). The Toilet Bowl is not detected; add `toilet_bowl` to `data/history.json` by hand if you want it shown.
* Sleeper makes a new league id each season. The pull finds it by name. Until it exists, the pull keeps reading the old league and files anything after `closed_at` as week 0 (offseason) of the new season.
* The first issue of a new volume is the look-forward issue.

Details: `DYNASTREE_MASTER_STATE.md` sections 3b and 6c.

---

## 10. The pages

| Page | Address | Built by | What it shows |
|---|---|---|---|
| Home | `/` | `build_site.py` (+ `build_managers.py` for The Market) | Latest-issue banner, news ticker, leaderboard, standings (rank, draft or wealth order), transactions, The Market (portfolio values), archive, league rules and scoring. |
| Issue | `/issues/<season>/issue-NN/` | `build_site.py` + `js/issue.js` | One frozen issue: desk, hero and zero, standings, bankroll, transaction wire, post-game cards, drama, trade machine, pre-game cards, match of the week, bottom line, poll. |
| Managers | `/managers/` and `/managers/<handle>/` | `build_managers.py` | One page per manager: record, stat tiles, game log, transactions, desk quotes, bio, trophy case, portfolio value. Alumni keep their pages. The home page gets the ranked portfolio table, "The Market". |
| History | `/history/` | `build_history.py` | Hall of Fame, in order: award shelf (with a live regular-season progress bar on the active season), prediction ledger, manager careers, all-time records, season-by-season timeline. There is no Champions wall; the champion and the Toilet Bowl winner are on the award shelf. |
| Ledger | `/ledger/` | `build_ledger.py` | Every draft pick and trade, with grades and blockbuster scores. |
| Receipts | `/receipts/` | `build_receipts.py` | Every quote, hit, bold prediction and hot take, with filters and a random-receipt button. |

Navigation: the sticky top bar has **The Vault** (a dropdown with Managers, History, Ledger, Receipts), **Standings**, **Transactions**, **The Market**, **Issues**, **Rules**, **Scoring**. Issue pages use their own section nav instead (Desk, Standings, Wire and so on). To add a page to The Vault, add a link to the `#vault` block in `index.html` and in every `build_*.py` shell (see section 15).

---

## 11. MAXPF

MAXPF is **Max PF: the points of each week's best possible lineup, added up over the season.** It matches Sleeper's own Max PF and is not "starters plus bench". The lowest MAXPF gets rookie pick 1.01 (linear order, not snake). The pull script prints a check against Sleeper's own figure on every run; if it lists a mismatch, look at the 1.01 order before publishing.

---

## 12. Trophies (reserved art)

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

* **History page:** the Champions wall was removed. `build_history.py` still warns in the build log when a closed season has no champion in `data/history.json`.
* **History page, Award shelf:** Best Manager, Biggest Tank and Waiver Wire MVP each show their own trophy.
* **Manager pages, Trophy case:** appears only once a manager has actually won something. Champion and Toilet Bowl come from `data/history.json`. The three awards count once their season is closed, or earlier if `history.json` names the winner by hand. A live season's current leader does not get the trophy early.

To show one anywhere new, call `trophies.img("lombardi", root)` (keys: `lombardi`, `toilet_bowl`, `best_manager`, `biggest_tank`, `waiver_mvp`) instead of writing the `<img>` by hand.

Recording a Toilet Bowl in `data/history.json`, next to the champion for that season:

```json
"2026": {
  "champion": "Handle", "runner_up": "Handle", "final_score": [131.4, 118.2],
  "toilet_bowl": {"winner": "Handle", "runner_up": "Handle", "final_score": [88.1, 71.5], "note": "Optional line."}
}
```

Only `winner` is required. `winner` is whoever takes the Toilet Bowl trophy.

---

## 13. On-deck issue cards

Cards for issues 18 to 36 are already in `assets/cards/` (`logo-NN.webp` is the crest "The Archive" card, `plain-NN.webp` is the number-only card). Nothing shows until that issue exists in `data/issues.json`. Then the build picks them up on its own:

* the **logo** card appears beside the issue title on the issue page;
* the **plain** card appears as the tile in the home page archive list.

Finished art always wins. If `assets/issue-card-NN.webp` or `assets/archive-issue-NN.webp` exists for an issue, it is used instead. To swap which style goes where, edit `CARD_STYLE` near the top of the issue-art helpers in `scripts/build_site.py`.

---

## 14. Site conventions

These apply to every page. Keep them when you change a shell.

**Accessibility**

* Every page starts with a **"Skip to main content" link** (`<a class="skip" href="#main">`), the first thing keyboard users reach. It is hidden until focused. The target is `<main class="wrap" id="main" tabindex="-1">`. Styles are at the end of `css/dynastree.css`.
* Keyboard focus is shown with the global `:focus-visible` outline in `css/dynastree.css`.
* Images carry `alt` text; decorative avatars use `alt=""`. Images have `width` and `height` set, and below-the-fold images use `loading="lazy"`.
* The ticker and live-dot animations stop when the visitor has reduced-motion turned on.
* The Vault dropdown is a real button with `aria-expanded`, and Escape closes it.

**Shared look**

* **Issue archive rows** (art tile, "Issue N: title", weeks, Read) come from one function, `archive_row()` in `scripts/build_site.py`, used by both the home page and the Hall of Fame issue index so the two always match. The whole row is a link and gets a green border on hover.
* **Manager handles** are bold green in "From the desk" (bolded at build time by `bold_handles()` in `build_site.py`) and in "The bottom line" (bolded in the browser by `bh()` in `js/issue.js`). Both use the exact handles from `data/managers.json`, so write handles exactly in prose; nicknames are not picked up. The colour is the `.art strong` rule in `css/dynastree.css`.
* **Section badges** (Post-Game, Trade Alert, Pre-Game) sit just left of the heading text; the rules are at the end of `css/dynastree.css`.
* **Manager stat tiles** are built by `stat_tiles()` in `scripts/build_managers.py` and styled at the end of `css/managers.css`. The Receipts manager dropdown is styled at the end of `css/receipts.css`.

**Pages that need JavaScript**

* On **issue pages**, the bankroll watch, transaction wire, post-game cards, drama, trade machine, pre-game cards, match of the week, bottom line and poll are drawn by `js/issue.js` from JSON embedded in the page. The hero, desk, hero and zero, and standings are plain HTML. With JavaScript off, a `<noscript>` note at the top of the page says so. If the script fails, `issue.js` shows a "failed to load" note. Both notes use the `.nojs` / `.loaderr` style.
* **The weekly poll is read-only.** Voting happens in the league's Sleeper chat; the page shows the question and options ("Vote in the Sleeper chat"). From Issue 5, `prev_poll` shows last issue's results as bars (`result` = vote counts per option, taken from the chat log; or a short text line if only the winner is known). The poll started in Issue 4, so the build never shows a poll on Issues 1 to 3 or results before Issue 5 (`POLL_FROM` and `PREV_POLL_FROM` in `build_site.py`).
* The home page, manager, history, ledger and receipts pages carry their content in HTML; scripts only add toggles, filters and the dropdown.

**Fonts**

* Inter (body) and Oswald (headings) load from Google Fonts. The link appears in `index.html`, `scripts/templates/issue.html`, and the font blocks of `build_managers.py`, `build_history.py`, `build_ledger.py` and `build_receipts.py`. To change a font, change all six.
* Self-hosting the fonts is optional. It would remove the one external request and the dependency on Google, but nothing is wrong with the current setup.

**Meta tags and privacy**

* Every page has `<meta name="robots" content="noindex">`, so search engines are asked to skip the site. It is a members-only newsletter. The site and the repo are still public, so anyone with a link can open them.
* Link previews use Open Graph and Twitter tags in every page head with absolute URLs (`og_block()` in `scripts/build_site.py`; static copies in `index.html` and `scripts/templates/issue.html`). The preview image is `assets/apple-touch-icon.png` (the crest, 180 px square, shown as a small "summary" card). To change it, change `OG_IMAGE` in `build_site.py` and the two static tags.

---

## 15. Adding a new page

1. Write `scripts/build_<name>.py`. Copy the `shell()` function from an existing builder so you keep the skip link, `id="main"`, the nav, the footer and the scripts.
2. Add its stylesheet to `css/` if it needs one.
3. Add a step to the workflow, after the page it depends on, and add its output folder to the `git add -A` line in the commit step.
4. Add a link to the `#vault` block in `index.html` and in every `build_*.py` shell.
5. If it reads a new hand-edited data file, add that path to the workflow's push triggers.
6. Add it to the tables in section 10 here, and to the repo map and the matching section of `DYNASTREE_MASTER_STATE.md`.

---

## 16. Running it locally

You almost never need to. The Action does it. If you want to preview a change:

```
pip install pillow
python scripts/sleeper_pull.py
python scripts/pull_values.py
python scripts/build_site.py
python scripts/build_managers.py
python scripts/build_history.py
python scripts/pull_player_stats.py
python scripts/ledger_values.py
python scripts/build_ledger.py
python scripts/build_receipts.py
python scripts/make_brief.py
```

Python 3.12. Pillow is only needed for avatars. Skip `sleeper_pull.py`, `pull_values.py` and `pull_player_stats.py` to rebuild from the data already in the repo (they need internet). Serve the folder (`python -m http.server`) rather than opening files directly, so paths resolve.

---

## 17. Backups

Once a month, download a fresh zip (repo page > green **Code** button > **Download ZIP**) and keep it somewhere outside GitHub. If you leave out the large `assets/` folder from the zip you share with Claude, keep a separate copy of `assets/` too: the code and data cannot recreate the artwork.

---

## 18. If the site looks wrong

Open the **Actions** tab, click the latest "Update league data" run, and read the red step.

* **Nothing changed after an upload:** check the run exists. A waiting run is queued behind another one; give it a few minutes. If there is no run at all, the files you uploaded were not in the trigger list in section 4.
* **Invalid JSON:** a missing comma or quote. Paste the file into any JSON validator.
* **Handle typo:** the build prints `issue-NN.json names 'X', who is not in the league data`. Use the exact handle.
* **Numbers look wrong:** the data is stale. Run the Action by hand and check `data_pulled_at` in `data/brief.json`. Never patch a number into prose.
* **A manager page is missing or wrong:** read the "Build manager pages" step. It needs `scripts/build_managers.py`, `css/managers.css` and `data/managers.json`.
* **Ledger shows no values, or every value has a ~:** read the "Value trades and picks with FantasyCalc" step. It needs at least one file in `data/market/snapshots/`; a `~` is normal for events before the first snapshot.
* **Portfolio section or market table missing:** read the "Pull FantasyCalc values and build portfolios" step. It can warn and still pass; the pages show nothing until `data/<season>/portfolio.json` exists. A "Picks with no FantasyCalc value" warning means FantasyCalc has no value for that pick (or renamed it); check `parse_pick`.
* **Style changes:** `css/dynastree.css` (site and issues) or the page's own stylesheet (`css/managers.css`, `history.css`, `ledger.css`, `receipts.css`).
* **Push failed in the Commit step:** it retries three times. If it still fails, run the Action again by hand.
