# DYNASTREE CHRONICLES: REFERENCE (site, scripts, pages)

> Read this only when a script, page, style or convention is being changed. For making an issue, use `DYNASTREE_ISSUE_GUIDE.md` and `DYNASTREE_STATE.md`. Where a section here says "this file" or "the master", it means the three-file set; section numbers are shared.

**Built so far:** the web-only site with the one-file `brief.json`, manager pages, the Hall of Fame & League History page, the Receipts archive, and the Draft & Trade Ledger; automation for prediction rulings, receipts, drafts, the champion and the season close; the **FantasyCalc market feature** (live value index, daily snapshots, manager portfolios with crash flags, The Market table with trend lines, the Wealth Index standings tab, wealth lines in the manager bios, value-based pick verdicts and trade values in the ledger, and locked FantasyCalc numbers in every issue from Issue 6 on); and the Oct 2026 site hardening (skip-to-content link, no-JavaScript note, one-run-at-a-time Action with push retry, full README rewrite; see 14b).

|Section|Lives in|
|-|-|
|1, 4, 5, 6, 6b-weekly, 9, 10, 11, 14|`DYNASTREE_ISSUE_GUIDE.md` (stable; read every issue)|
|7, 8, 12, 13|`DYNASTREE_STATE.md` (changes every issue; returned every issue)|
|2, 3, 3b, 6b, 6c, 6d, 6e, 6f, 14b, 15, 16|`DYNASTREE_REFERENCE.md` (site, scripts, pages; read only when changing them)|

---

## 2. HOW THE SITE WORKS (one source of truth)

```
Sleeper API --scripts/sleeper_pull.py (GitHub Action)--> data/*.json          all numbers (incl. schedule.json)
data/ + data/issues/*.json --scripts/build_managers.py--> managers/index.html + managers/<handle>/index.html   manager pages
FantasyCalc API + Sleeper rosters --scripts/pull_values.py (GitHub Action)--> data/market/fantasycalc.json + data/<season>/portfolio.json   market values and every manager's portfolio (read by build_managers.py and make_brief.py)
snapshots + trades + drafts + stats --scripts/ledger_values.py (GitHub Action)--> data/market/ledger_values.json   FantasyCalc value of every trade and pick, then and now (read by build_ledger.py)
draft + transactions + stats + data/ledger.json --scripts/build_ledger.py--> ledger/index.html   Draft & Trade Ledger
issue JSON + data/receipts.json --scripts/build_receipts.py--> receipts/index.html   Receipts Archive
all seasons' data/ + data/history.json + data/settings.json --scripts/build_history.py--> history/index.html   Hall of Fame & League History (permanent)
data/ --scripts/make_brief.py (GitHub Action)--> data/brief.json             the one file you share with Claude
chat log + this file --Claude--> data/issues/issue-NN.json + data/issues.json   all words
data/ + scripts/templates/issue.html --scripts/build_site.py--> index.html + issues/2026/issue-NN/index.html
```

* **Numbers:** Sleeper data wins over anything in this file or the chat.
* **Words:** issue JSON only. No hand-edited HTML, ever. Pages are regenerated from the template on every build, so manual edits to an issue page are overwritten.
* **Look:** `css/dynastree.css` and `js/issue.js` (rendering), `scripts/templates/issue.html` (page shell). Change style there, never in an issue.
* If a page looks wrong, the data or JSON is wrong or stale. Fix the source, rebuild.

### The Action (`.github/workflows/update-data.yml`)

Runs, in order: `sleeper_pull.py`, `pull_values.py` (FantasyCalc; may fail without failing the run), `build_site.py`, `build_managers.py`, `build_history.py`, `pull_player_stats.py` (may fail without failing the run), `ledger_values.py` (FantasyCalc values for trades and picks; may fail without failing the run), `build_ledger.py`, `build_receipts.py`, `make_brief.py`. Then it commits `data/`, `index.html`, `issues/`, `managers/`, `history/`, `ledger/`, `receipts/`, `assets/avatars/`. It triggers:

* Tuesday 11:00 UTC and Wednesday 13:00 UTC (after Monday Night Football, then after stat corrections);
* by hand: GitHub > **Actions** > "Update league data" > **Run workflow**;
* automatically when a push touches `data/issues/**`, `data/issues.json`, `data/seasons.json`, `data/*/fut_cap.json`, `data/managers.json`, `data/settings.json`, `data/history.json`, `data/ledger.json`, `data/receipts.json`, `data/bios/**`, `scripts/**`, `css/**`, or `js/**`.

**One run at a time.** The workflow has a `concurrency` group (`update-league-data`, no cancelling), so a second trigger waits in the queue instead of racing the first, and the commit step pulls with rebase and retries the push up to three times. A "pending" run is normal.

So: **upload the issue files, wait about a minute, and the site is rebuilt, including every manager page** (records, game logs, transactions and desk quotes refresh from the new data and the new issue JSON). If the site does not change, open the Actions tab and read the failed run's log.

---

### What is automatic and what is not

* **Fully automatic, every Action run:** standings, records, MAXPF, every manager page, the FantasyCalc value index and every manager's portfolio (with its crash flag), the Hall of Fame (records, careers, issue index, awards once a season is closed), the Ledger (every pick and trade, pick grades at 12/24/36 months), the Receipts archive, the champion and runner-up when Sleeper's bracket decides them, closing a season once the review issue is out, drafts (new draft dates and, for a new draft, its picks), and `brief.json`.
* **Comes with each issue (the one Claude bundle):** `issue-NN.json` (with `rulings` and `receipts`), the `issues.json` entry, the 12 weekly bios.
* **Once a year:** the volume `story` in `history.json`, and flagging the season-review issue `"season_final": true`.
* **By hand, rarely:** `settings.json` (league rules changed), a hand `verdicts` override or trade obituary in `ledger.json`, a Toilet Bowl entry, a rename the pull could not match.

## 3. REPO MAP (where everything lives)

|Path|What it is|Who writes it|
|-|-|-|
|`data/bios/<handle>.json`|stable desk bio per manager (see 6b): story paragraph 1, The type, Signature move; changes only on a rewrite|**Claude**|
|`data/bios/weekly/<handle>.json`|weekly bio laid over the stable one by `bs.load_bio()` (`merge_bio()` in `build_site.py`); returned every issue|**Claude**|
|`DYNASTREE_STATE.md`|weekly memory: open threads, voice bits, poll memory (keep in the repo root so it is in every zip)|Claude returns it every issue, you upload|
|`DYNASTREE_ISSUE_GUIDE.md`|stable rules for making an issue (repo root)|Claude returns it only when a rule changes, you upload|
|`DYNASTREE_REFERENCE.md`|this file: how the site, scripts and pages work (repo root)|Claude returns it only when the build changes, you upload|
|`README.md`|full human-readable guide to the repo, the Action and the conventions. Must agree with this file (see 14b)|Claude returns it when the build changes, you upload|
|`index.html`|home page: banner, ticker, leaderboard, standings, transactions, archive|build_site.py (never by hand)|
|`market/index.html`|The Market (top) and the trade calculator (`#calculator`; `js/calc.js`, `css/calc.css`)|build_managers.py (never by hand)|
|`rules/index.html`, `scoring/index.html`|Rules and Scoring, one page each|build_site.py (never by hand)|
|`scripts/shell.py`|the shared top bar, the Vault and Research link lists, the page shell for the new pages|static|
|`404.html`|branded not-found page (GitHub Pages serves it for any bad address); hand-written, uses `<base href="/Dynastree-Chronicles/">`; update its three buttons if the nav changes|static, by hand|
|`issues/2026/issue-NN/index.html`|one page per issue|build_site.py (never by hand)|
|`data/<season>/league.json`|league id, roster slots, budget, `generated_at`, weeks with scores|Action|
|`data/managers.json`|everyone who has ever been in the league: handle, team name, avatar, Sleeper `user_id`, `active` true/false, `former_names` (old handles, section 6)|Action writes and keeps it; people who leave stay in it as `active: false`; hand-added fields are preserved|
|`data/<season>/standings.json`|live standings, MAXPF, draft pick, FAAB|Action|
|`data/<season>/efficiency.json`|points vs optimal per manager|Action|
|`data/<season>/transactions.json`|every trade, waiver claim, bid|Action|
|`data/<season>/schedule.json`|every matchup for weeks 1 to 18 (this is where next week's pre-game games come from)|Action|
|`data/brief.json`|**the one file to share with Claude** (see section 1)|Action|
|`data/<season>/weeks/week-NN.json`|per-team scores, optimal lineup, bench, MVP; `"final"` flag|Action|
|`data/issues.json`|issue index (title, dek, banner, ticker, weeks, `wire_week`)|**Claude**|
|`data/issues/<season>/issue-NN.json`|all prose for issue NN|**Claude**|
|`data/issues/issue-template.json`|empty schema to copy|static|
|`scripts/seasons.py`|season registry, paths, one-time migration|static|
|`scripts/sleeper_pull.py`|Sleeper pull + standings/MAXPF logic|static|
|`scripts/build_site.py`|builds home + issue pages|static|
|`scripts/build_managers.py`|builds the manager hub and one page per manager; imports `build_site.py`, so it must run after it|static|
|`scripts/pull_values.py`|pulls FantasyCalc dynasty values, runs every roster and pick through them, writes the portfolio files below; runs right after `sleeper_pull.py` and is allowed to fail without failing the run|static|
|`data/market/fantasycalc.json`|live value index: top 1,000 dynasty players and picks (value, rank, 30-day trend, Sleeper id), overwritten every run|Action|
|`data/market/snapshots/<date>.json`|one FantasyCalc snapshot per pull (values are looked up from these as of a date)|Action|
|`data/market/ledger_values.json`|FantasyCalc value of every trade (then, now) and every draft pick (at pick, locked review points)|Action|
|`scripts/ledger_values.py`, `scripts/market.py`|ledger values step; FantasyCalc helper library|static|
|`data/<season>/portfolio.json`|per-manager portfolio: total value, position split, top holdings, 30-day market move, IR exposure, status flag, plus a growing snapshot `history`. Frozen with the season|Action|
|`data/<season>/wealth.json`|Wealth Index: roster value, draft capital and total per team for each finished week (the third standings tab)|Action|
|`scripts/make_brief.py`|builds `data/brief.json`|static|
|`scripts/templates/issue.html`|issue page shell with `{{TOKENS}}`|static|
|`css/dynastree.css`|the stylesheet in use|static|
|`css/managers.css`|styles for the manager pages (loaded only by them)|static|
|`managers/index.html`, `managers/<handle>/index.html`|manager hub and one page per manager (avatar, record, stat tiles, game log, transactions, desk quotes). `managers/<old handle>/` is a redirect stub after a rename|build_managers.py (never by hand)|
|`data/history.json`|**permanent league history**: per-season champion, runner-up, final score, volume story, award overrides, and the result of every bold prediction. Never reset, never inside a season folder|**Claude / you**|
|`data/settings.json`|league settings shown on the home page (at-a-glance tiles, scoring system, playoff start week and team count). Edit when the commissioner changes a rule|**Claude / you**|
|`scripts/build_history.py`|builds `history/index.html` from every season's data + `history.json`; runs after `build_managers.py`|static|
|`history/index.html`|Hall of Fame & League History page (champions wall, all-time records, manager careers, award shelf, prediction ledger, season-by-season timeline)|build_history.py (never by hand)|
|`css/history.css`|styles for the history page (loaded only by it)|static|
|`data/ledger.json`, `data/receipts.json`|hand-entered ledger verdicts / trade notes and extra receipts (see 6d, 6e)|**Claude / you**|
|`scripts/pull_player_stats.py`, `scripts/build_ledger.py`, `scripts/build_receipts.py`, `scripts/trophies.py`|NFL stats pull, ledger page, receipts page, trophy registry|static|
|`ledger/index.html`, `receipts/index.html`|Draft & Trade Ledger and Receipts Archive|build_ledger.py / build_receipts.py (never by hand)|
|`css/ledger.css`, `css/receipts.css`, `js/nav.js`|styles for those two pages; The Vault dropdown|static|
|`js/issue.js`, `js/site.js`|render issue cards; icons and sort toggle|static|
|`assets/`|crests, badges, grade images, trophies, icons|static|
|`assets/avatars/*.webp`|manager avatars|Action|
|`pdf/` folder|old PDFs, no longer linked anywhere; safe to delete|frozen|
|`.github/workflows/update-data.yml`|the Action|static|

### Where to put files Claude hands back

See `DYNASTREE_ISSUE_GUIDE.md`, section 1.

---

## 3b. SEASONS AND VOLUMES (one folder per season)

**Volume N = season N.** Volume 1 = 2026. Issue numbers restart at 1 in every volume.

```
data/seasons.json            registry: volume, league_id, status ("active" / "closed"), closed_at, carry_from   (shared; the one switch)
data/managers.json, data/bios/, data/brief.json, data/issues.json, data/issues/issue-template.json              (shared)
data/issues/2026/issue-NN.json     issue prose, one folder per season
data/2026/                         league, standings, efficiency, transactions, schedule, draft, fut_cap, weeks/week-NN.json
data/2027/                         same files, created by the pull when 2027 opens
```

* **Active season** = the newest season in `seasons.json` that is not `closed`. The pull, `brief.json` and the Claude workflow always work on it. A closed season is frozen: the pull skips it and its pages never change.
* **Capping a volume is automatic.** As soon as Sleeper's winners bracket has a champion, the pull records it in `data/<season>/result.json` (champion, runner-up, final score; a two-week final is summed). When the season-review issue is published with `"season_final": true` on its `data/issues.json` entry, that same run closes the season (`status: closed`, `closed_at` = that moment) and the next pull opens the next volume (`carry_from` = the closed one). `brief.json` > `season_end` tells Claude when the review issue is due. Closing by hand (`status` and `closed_at` in `seasons.json`) still works.
* **Fresh pool:** Sleeper makes a new league id each season. The pull looks it up by name. Until the new league exists it keeps reading the old league and files every transaction created after `closed_at` as **week 0** of the new season (offseason). Nothing before the cap is carried over; nothing after it is lost. Duplicates are dropped by transaction id.
* **Nothing to pull is not an error:** if Sleeper has no league for the active season yet (and no previous league to read), or does not answer, the pull prints a yellow warning on the Actions run and the run still succeeds. The build steps run on the data already in the repo. A red run now means a real bug.
* **Volume opener:** the first issue of a new volume is the look-forward issue. While there are no final weeks, `brief.json` says so and lists `transactions_offseason`.
* **Issue files:** `issues.json` entries need `"year": <season>`. New issue prose goes to `data/issues/<season>/issue-NN.json`. `fut_cap.json` now lives at `data/<season>/fut_cap.json`.
* The old flat layout is migrated automatically on the first Action run after this update (`scripts/seasons.py`).

## 6b. MANAGER PAGES

*Six bullets that matter every week (bios, the writing rule, the Hypothetical Trade Machine, the market flag and how to write with it) now live in `DYNASTREE_ISSUE_GUIDE.md`, section 6b-weekly.*

* One page per manager at `managers/<handle lowercased>/`, plus the hub at `managers/`. **Everyone in `data/managers.json` gets a page, and so does anyone who appears in any season's standings.** Linked from the home nav, the standings tables and the leaderboard.
* **Active or alumni:** `active` in `managers.json` is set by the pull from the live Sleeper rosters. Someone who leaves the league keeps their page and links; the page says "Alumni. Last played in <season>", the hub lists them under **Alumni**, and they drop out of the prev/next ring and out of `brief.json`'s `managers` (they appear in its `alumni` list instead).
* **Numbers come from each season's own folder.** The top of the page shows the manager's latest season; every season block below it (newest first) has its own record, rank, PF/PA, MAXPF, efficiency, draft slot, FAAB, game log and transactions from `data/<season>/`. A closed season reads "Final standing" and is written in the past tense. There are no typed final records or ranks anywhere any more.
* **Portfolio value (FantasyCalc).** `pull_values.py` pulls FantasyCalc dynasty trade values for this league's format (superflex, 12 teams, full PPR) and runs every roster and every future pick (after trades) through them. Each manager page gets a **Portfolio value** section (status flag, total, league rank, 30-day market move, share of value on IR, draft capital, value history chart, position split, biggest holdings), and the **home page** gets a **The Market** section (between Transactions and Rules, with its own item in the top nav on every page) ranking all 12, with a collapsible legend. `build_managers.py` writes it into `index.html` between `<!--MARKET-->` markers. Source: `data/<season>/portfolio.json`; the pages skip the section if it is missing.
* **Trade calculator.** On `market/#calculator`: pick a team for each side, add players and picks, see each side's FantasyCalc total, a verdict (Even under 5%, Fair enough under 15%, Lopsided under 30%, Robbery beyond), the portfolio impact for each team (value, rank before and after), suggested assets to even it up, and a shareable link. Pure browser code (`js/calc.js`) over data embedded by `build_managers.py` (`calc_data()`); a plain sum of values with no roster-spot adjustment. The Research dropdown's Trade Calculator item links to `market/#calculator`.
* **Trade finder.** On `market/#finder` (Research dropdown, menu-only). Pick your team, offer positions, picks (the Picks chip) or exact players, optionally say what positions you want back and your role (Let the finder decide, Win now, Balanced, Build for the future), press Find trades: up to five roughly even deals with a reason each and an Open-in-calculator button. The classification below is INTERNAL: it is never shown on the site (no labels, no table), and **never write that a manager is a contender, rebuilder or retooling in an issue or any published text**; managers may see themselves differently. Two ideas: NEED (how much your offered players raise a team's starting lineup, injured players do not start) and WINDOW (each team is a Contender, Retooling or Rebuilder from 50% lineup strength, 30% record, 20% starter age). Internally, a rebuilding-type team values picks and youth above market and older players below; a contender the reverse (`factor()` in `js/finder.js`), so a deal must be fair in market value AND make sense for the other team's window; offering only picks finds rebuilders who would sell veterans. Value-based, no point projections. `js/finder.js` over the same embedded data as the calculator, plus ages and standings.
* **Daily snapshots.** A second workflow (`daily-values.yml`, 09:30 UTC every day) saves a FantasyCalc snapshot and rebuilds only the value pages, so charts, sparklines, the Wealth Index and trade "value at the time" have daily points. It queues with the main workflow. `prune_snapshots.py` (a daily-workflow step) keeps every snapshot for 60 days, then one per calendar week, and always keeps the first snapshot, the newest, and the one nearest each trade date and draft pick date, so ledger values never shift.
* **The balance sheet.** Each manager's desk file ends with an automatic card (rank by wealth, share on IR, share in picks, 30-day market move, change since last Wealth Index week). It is built from `portfolio.json` and `wealth.json`; do not write it into the bios. Stat tiles on manager pages show their league rank as a corner label as well as the colour. The Market table has a Trend sparkline per manager.
* **Season-end wealth.** When a season is closed, the next run copies its last Wealth Index week into `data/history.json` > `seasons.<year>.wealth_final` (once, never edited): the permanent basis for a multi-year dynasty arc.
* **Wealth Index.** The standings block (home page and every issue) has a third tab, **Wealth index**: teams ranked by total FantasyCalc dynasty value, split into roster value and draft capital, with rank movement and the change in total wealth since the previous tracked week. Source: `data/<season>/wealth.json` (written by `pull_values.py`, one entry per finished week, frozen once the next week is final). The home page shows the newest week; an issue shows its own week and has no tab if that week was never saved. Built by `wealth_view()` in `build_site.py`.
* **Issue trade values (locked).** From the issue in `data/settings.json` > `issue_values_from` (`[2026, 6]`), under the freeze rule below, the Hypothetical Trade Machine shows the current value of each side's assets plus a value edge, and each graded trade in the wire shows value at the trade and value when the issue ran. `build_site.py` computes them on the issue's first build and locks them in `data/issues/<year>/values-NN.json`; they never change afterwards, and earlier issues are untouched. Hypothetical assets are parsed from the text (player names, "2027 1st-round pick"); FAAB and unnamed assets are not valued. Claude writing an issue: use real player names and "YYYY Nth-round pick" wording in `trades.items` `as`/`bs` so values can be attached.
* **Standings column names (current):** Standings order W-L, MOV, PF, PA, FAAB; Draft order Pick, Team, DRAFT CAP, MAXPF, MOV, FAAB; Wealth index ROSTER CAP, DRAFT CAP, Total wealth, MOV, CHANGE. The Market's column is 30-day move. The standings legend defines every column, including PA.
* **Draft order Pick value.** The Draft order tab (home and issues) has **DRAFT CAP** (the combined FantasyCalc value of every pick the team owns) in place of the old FUT CAP; same pick values as The Market and the manager pages. There is no per-slot Pick value column. The Standings order tab columns are #, Team, W-L, MOV, PF, PA, FAAB. Issues with no wealth entry for their week have neither column.
* **Freeze rule (important).** Every FantasyCalc number an issue shows is frozen the first time that issue is built: trade values, the Wealth index and Draft order tabs. It is stored in `data/issues/<year>/values-NN.json`, each part is written once and never recomputed, so market moves and rebuilds cannot change a published issue. Applies from the issue in `settings.json` > `issue_values_from` (`[2026, 6]`); earlier issues are untouched.
* **Ledger table and hub (current):** draft tables show Value at pick, End of season and Change columns (no notes block; hand notes sit under the player name); trade value edge is two cards (At the trade, Latest) with a Flipped tag; the managers hub has only The podium and The rest; the Moves tile is gray, last and never ranked.
* **Manager page tiles and tables:** the stat tiles are shaded by league rank for that category (green 1st, red last; `TILE_HIGHER` in `build_managers.py` sets which direction is better). Biggest holdings sorts by Pos, Value (default) or 30d. Draft picks owned shows at least 9. The Game of the Week Final verdict shows each team's avatar beside its name and score.
* **Manager page season sections:** The season and Game log open; Transactions, The takes, The drama, What the desk said closed (each collapsible). **Manager names that link** are green with a glow on hover, site-wide.
* **Honest limits.** FantasyCalc dynasty values react slowly to injuries, so an IR stash flags through `sidelined_pct`, not through a falling market value. Players outside the top 1,000 count as 0 (`off_index`). Picks are FantasyCalc `PICK` rows (names like "2027 1st (Mid)"); for the next draft the tier comes from the original owner's draft slot in `standings.json`, later drafts use the untiered or Mid value. A pick with no value counts as 0 and is printed as a warning in the Action log. Each manager's picks (with a "via" tag when acquired) appear on the manager page. Values are credited to FantasyCalc on the page.
* Nothing to upload: the Action rebuilds the `managers/` folder on every run. A failed `build_managers.py` step shows as its own red step in the Actions log.
* **Known limit:** if a manager is replaced on a roster in the middle of a season, Sleeper's weekly data is keyed by roster, so the open season's weeks are attributed to the current owner each pull. Departures between seasons are safe, because a closed season is frozen.

## 6c. HALL OF FAME & LEAGUE HISTORY (`history/`)

* One permanent page that never resets and grows every offseason. Linked from the nav as **History**. Rebuilt on every Action run, so records, careers, awards and the timeline update weekly with no upload.
* **Automatic (from every season's `data/<season>/`):** all-time records (best week, worst week, biggest blowout, best MAXPF season, longest win streak across seasons, most FAAB on one player), manager career table (record, PF, titles, playoff trips, a live "Pace" flag for the open season), award shelf, volume stat tiles, key trades, issue index, and the prediction ledger (every `bold` entry in every issue appears automatically as Pending).
* **Award rules:** Best Manager = highest season lineup efficiency (points / MAXPF) **among teams with a win rate of 44% or higher once at least 5 games have been played** (before 5 games, no floor). The spirit is start/sit skill: a team that is losing, or has stopped managing, leaves nothing on the bench, so a high efficiency there is not good management. A season-long Best Manager (the award, its standing mention in an issue, bio or the history page) is never given to a team under the floor. **Hero of the Week and Zero of the Week are weekly and can be any team**; a sub-44% team can be a Hero of the Week, or a candidate for it, for a single lineup. A team that is tanking is recognized through **Biggest Tank** (lowest MAXPF, the 1.01), not Best Manager. Biggest Tank = lowest MAXPF (the 1.01). Waiver Wire MVP = most weekly `mvp` flags in `wire.waivers`. Bold Prediction Hit = the ledger entry marked `"star": true`, else the latest hit. Any award can be overridden in `history.json` under `seasons.<year>.awards.<key>` with `winner` and `note` (keys: `best_manager`, `biggest_tank`, `waiver_mvp`, `bold_hit`).
* **Award shelf is 8 trophies, two rows of four, one collapsible block per volume (newest open):** 1 League Champion (`lombardi`), 2 Silver Cup (`silver_cup`, the championship runner-up), 3 Apex Predator (`apex_predator`, highest regular-season PF), 4 Best Manager, 5 Toilet Bowl Champion (`toilet_bowl`, hand entry in `history.json`), 6 Biggest Tank, 7 Waiver Wire MVP, 8 Bold Prediction Hit. Champion and Silver Cup fill in from `result.json`; Apex Predator is the season PF leader. Year-end issues use the same trophy art from `assets/trophies/` through `scripts/trophies.py` (`silver-cup`, `apex-predator`, each with an `-sm` version). `awards` overrides also accept `apex_predator`.
* **Prediction rulings ride in the issue file.** Every issue, Claude settles earlier issues' still-pending bold predictions in that issue's `rulings` list (section 9). `brief.json` > `predictions_to_rule` lists exactly what is open, with issue number and index, so nothing is judged from memory. A later ruling replaces an earlier one. `data/history.json` > `predictions` still works as a hand override and wins, except a hand `"pending"` never blocks a ruling. Champion, runner-up and final score fill in from `data/<season>/result.json`; `history.json` is only needed for the volume `story`, an optional `note`, `playoffs`, `awards` overrides and a `toilet_bowl` entry. **The Toilet Bowl is not detected** (leagues define it differently); enter it by hand if you want it.
* **Offseason ritual (in the season-review issue):** Claude writes the review issue with `"season_final": true` on its `issues.json` entry, and once a year writes the volume `story` into `history.json`. The champion, runner-up, final score and closing the season are automatic. A closed season whose champion could not be read from Sleeper prints a `history:` note in the Action log and shows "Champion not recorded yet"; then add it to `history.json` by hand.
* Playoffs start Week 15 with 6 teams (`playoff_start`, `playoff_teams` in `data/settings.json`); regular-season record and PF count weeks before 15.

## 6d. DRAFT & TRADE LEDGER (`ledger/`)

* Page at `ledger/index.html`, linked from the nav as **Ledger**. Built by `scripts/build_ledger.py` (runs after `build_history.py`), styled by `css/ledger.css`. Never edit the HTML by hand.
* **Automatic:** every pick from `data/<season>/draft.json`, every trade from `data/<season>/transactions.json`, and the desk's grades and takes from each issue's `wire.trades`. Trades get a Blockbuster score (1st 75, 2nd 30, 3rd 10, other pick 5, player 20, $10 FAAB 1; weights and the `blockbuster_min` cutoff live in `data/ledger.json` > `settings`).
* **Hand-entered, `data/ledger.json` (exceptions only):** `verdicts` (a hand grade overrides the automatic one; `"2026:1.01": {"grade": "hit|mid|bust", "note": "..."}`) and `trades` (obituaries: key = Sleeper trade id; `status: deceased` with `headline`, `cause`, `obituary`, `survived_by`; Claude may add one with an issue when a trade is clearly dead). Never grade from memory.
* **(Superseded for the verdict: see the next bullet.) Auto-grading at 12, 24 and 36 months:** `scripts/pull_player_stats.py` (Action step, `continue-on-error`) writes `data/stats/<season>.json` with each drafted player's points (league scoring), games, position rank and `proj` (the points Sleeper projected for the weeks he played). `scripts/pick_grades.py` (called by `build_ledger.py`) then grades each pick at 12, 24 and 36 months after the pick date (draft completion date from `data/<season>/draft_meta.json`, else `drafts.<year>.date` in `ledger.json`, else Sept 1 of the draft year). A checkpoint is due once the month mark has passed AND the NFL season it judges (pick year + k - 1) is final. Grade = position-rank thresholds in `ledger.json` > `grading` (hit inside `hit`, mid inside `mid`, else bust; picks after `late_round` can't be busts), moved one step up if actual points were at least `projection.over` (1.15) times Sleeper's projection, or one step down at `projection.under` (0.70) or less (needs `min_games`, 4). The latest due checkpoint is the verdict; after 36 months it is final. Until a checkpoint is due the pick shows "check due <month>". If Sleeper's projections endpoint does not answer, the Actions log prints "projections are not available" and picks are graded on production alone. Drafts are pulled too: `draft_meta.json` every run, and `draft.json` is written only when missing (a hand-made one, like the startup draft, is never overwritten).
* **Value-based verdicts and trade values (FantasyCalc).** `pull_values.py` saves a dated FantasyCalc snapshot on every run (`data/market/snapshots/`); `scripts/ledger_values.py` (Action step, `continue-on-error`) writes `data/market/ledger_values.json`; `build_ledger.py` reads it. **Trades:** each side shows the value of what it received at the time of the trade and in the latest pull, per-asset values and a value edge line. **Picks:** verdict = value at the review point divided by value at the pick (floor `grading.value.floor`, 500): hit at 1.15 or more, bust at 0.70 or less, otherwise mid (`grading.value` in `ledger.json`; picks after `late_round` cannot be busts). A rookie draft gets three verdicts, one per NFL season (pick year, +1, +2), each judged once that season is final and then locked. The 2026 startup draft gets one season-long verdict, locked when 2026 is final and filed in Volume 2, Issue 1. A hand verdict still overrides. FantasyCalc keeps no history, so trades and picks that pre-date the first snapshot use an estimate from FantasyCalc's 30-day trend (shown with a ~). `pull_player_stats.py` still supplies the season-final flag and the position rank shown beside each verdict.
* Repo map additions: `data/ledger.json` (Claude / you), `scripts/build_ledger.py`, `scripts/pull_player_stats.py`, `data/stats/*.json` (Action writes), `css/ledger.css`, `ledger/index.html` (builder output).

## 6e. THE RECEIPTS ARCHIVE (`receipts/`)

* Page at `receipts/index.html`, linked from the nav as **Receipts**. Built by `scripts/build_receipts.py` (after `build_ledger.py`), styled by `css/receipts.css`. Never edit the HTML by hand.
* **Automatic, from every issue JSON:** `hits` (Chat Greatest Hit), `quote` (Quote of the Week) and `bold` (Bold Prediction, ruled Aged well / Aged badly / Pending from `data/history.json`). Duplicates are dropped. Grouped by season (volume), newest first, with filters for type, manager, free-text search and a Random receipt button.
* **Hot takes ride in the issue file.** Each issue's `receipts` list (section 9) holds the best lines from the chat log that did not make the issue: exact words, exact handle, `status` aged_well / aged_badly / pending. To update an older one, list it again in a later issue (same `who` and `text`) with the new `status` and `note`; the first issue keeps the source link. `data/receipts.json` > `takes` still works for extras added by hand.
* **Per-issue ritual:** while reading the chat log, Claude fills the issue's `receipts` and re-lists any older receipt whose status has changed. No separate upload.

## 6f. NAVIGATION

* The top bar reads **The Vault** (dropdown), **Research** (dropdown: The Market, Trade Calculator, Rules, Scoring), Standings, Transactions, Issues. It is built once in `scripts/shell.py` (`nav()`, with the `VAULT` and `RESEARCH` lists) and used by every page; `index.html` gets it through the `NAV` marker. Add a new link in `shell.py` only; it also feeds the two tile groups on the home page (`VAULT` marker). The Market table links `market/#market`, the trade calculator `market/#calculator`.
* **Home page (current):** sections run latest issue banner (with the crest and the two tile groups, Inside the Vault and Research), leaderboard, standings, transactions, archive. Rules, Scoring and The Market are their own pages (`/rules/`, `/scoring/`, `/market/`).
* **History page order (current):** Award shelf (with the regular-season progress bar on the active season) and prediction ledger, Manager careers, All-time records, Season by season. The Champions wall was removed. **Ledger page:** the Blockbuster score box was removed; "How trade values are measured" stays. **Issue polls:** option letters only, no list numbers. **Legends** that carry long labels use `legend wide` (same look as the standings legend).
* Managers, History, Ledger and Receipts live in **The Vault** dropdown; The Market, Trade Calculator, Rules and Scoring live in **Research**. Behavior in `js/nav.js` (any number of dropdowns), look in `css/dynastree.css`.
* **Every page shell** (`index.html`, `scripts/templates/issue.html`, and the `shell()` in each `build_*.py`) starts with the skip link `<a class="skip" href="#main">Skip to main content</a>` right after `<body>`, and its `<main>` is `<main class="wrap" id="main" tabindex="-1">`. Issue pages also carry a `<noscript>` note (class `nojs`) because the wire, game cards, drama, trade machine, pre-game cards, bottom line and poll are drawn by `js/issue.js`. Keep all of this in any new shell. Skip-link and note styles are at the end of `css/dynastree.css`.
* Archive rows on the home page and the Hall of Fame issue index both come from `archive_row()` in `build_site.py` ("Issue N: title", art tile, whole row links, green hover), so they stay identical. Manager handles are bold green in "From the desk" (`bold_handles()` in `build_site.py`) and "The bottom line" (`bh()` in `js/issue.js`); both match exact handles only, so always use exact handles in prose. Manager stat tiles come from `stat_tiles()` in `build_managers.py` (includes Best week and FAAB spent).
* Link previews: every page head carries Open Graph and Twitter tags with absolute URLs, via `og_block()` in `build_site.py` (static copies in `index.html` and the issue template). The image is `assets/apple-touch-icon.png` (180 px square, `summary` card). `noindex` stays on every page (the league is fine being findable, no one has a preference; to allow search, remove it from the six shells).
* Fonts (Inter and Oswald) load from Google Fonts in those same six shells; changing a font means changing all six. All pages carry `noindex`.
* Issue pages keep their own section nav (Desk, Standings, Wire...). Ledger opens on the Blockbuster Registry tab by default.

## 14b. KEEPING THE README AND THIS FILE IN SYNC

The README (human guide to how the repo and site are built) and `DYNASTREE_ISSUE_GUIDE.md` plus this file (operating manual for making issues) overlap on purpose. Division of labour: **the issue guide owns league content and the issue workflow; this file owns how the pages are built** (rules, voice, schema, sort laws, threads); **the README owns repo structure, the Action, scripts and site conventions.** When something changes, update both in the same upload:

|What changed|README section|This file|
|-|-|-|
|A script is added, renamed or reordered; the Action's steps, triggers or committed folders|2, 3, 4, 5, 6|2 (diagram and The Action), 3 (repo map)|
|A hand-edited data file is added or its purpose changes|3, 6|3 (repo map and return table)|
|A page is added or its nav entry changes|10, 15|3, 6b to 6f|
|FantasyCalc values, portfolios, crash thresholds|4, 5, 10, 16, 18|2, 3, 6b, 15|
|Page shell, accessibility, fonts, meta tags, noindex|14|6f|
|Season or volume rules|9|3b|
|Trophies or on-deck cards|12, 13|6c|
|What is automatic vs bundled with each issue (rulings, receipts, pick grades, season close)|"Automation at a glance", 6, 8, 9|"What is automatic", 3b, 4, 6c to 6e, 9, 14|
|Issue steps, JSON schema, voice, league rules|7, 8 (summary only)|4, 9, 10, 11|

If the two disagree, the code wins: read the script, then fix both documents.

---

## 15. IF THINGS GO WRONG

* **Whole chat history lost:** nothing is lost. Start a new chat with the three items in section 1.
* **Claude cannot open the live-site link:** download `brief.json` yourself and attach it. If the site is down, Actions > latest run > the `data` folder in the repo has the same file.
* **Repo lost or deleted:** this file records the data model and the rules but not the code. Restore from a saved zip (this is why the monthly backup in section 14 matters). GitHub may also let you restore a recently deleted repo from your account settings, but do not count on it. Without the code, a new build of `sleeper_pull.py`, `build_site.py`, the issue template, CSS, and JS would have to be recreated from the schema in section 9.
* **A run says "pending" or "queued":** another run is in progress; the Action runs one at a time. Wait; it will pick up your upload. If a Commit step reports `Could not push after 3 attempts`, run the Action again by hand.
* **Site did not update after upload:** Actions tab > open the latest "Update league data" run > read the red step. Common causes: invalid JSON (missing comma or quote), a handle typo, or `issues.json` missing `wire_week`.
* **Numbers look wrong:** wrong or stale data; run the Action by hand, re-download the zip, rebuild. Never patch a number in the JSON prose to match.
* **Manager page looks wrong or is missing:** open the Actions run and read the "Build manager pages" step. It needs `scripts/build_managers.py`, `css/managers.css` and `data/managers.json` in the repo. Style changes go in `css/managers.css`.
* **Portfolio section or market table missing:** open the Actions run and read the "Pull FantasyCalc values and build portfolios" step (it may be yellow-warned and still pass). The pages show nothing until `data/<season>/portfolio.json` exists. Warning "Picks with no FantasyCalc value" means FantasyCalc has no value for that pick or renamed it; check `parse_pick` in `pull_values.py`.
* **Style change wanted:** edit `css/dynastree.css` or `scripts/templates/issue.html`; it applies to every issue on the next build.

## 16. BRAND FOOTER

DYNASTREE CHRONICLES: Documenting your worst takes and archiving your receipts, because time heals all wounds but screenshots last forever. Questions, corrections, or demands for a higher ranking: settle it on the field (or the trade screen).

