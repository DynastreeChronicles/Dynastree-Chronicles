# DYNASTREE CHRONICLES: ISSUE GUIDE (stable; read every issue)

> How to make an issue. This file rarely changes. The weekly memory is `DYNASTREE_STATE.md`; how the site and scripts work is `DYNASTREE_REFERENCE.md`. If every chat is gone, this guide + `DYNASTREE_STATE.md` + `brief.json` + the new chat log is enough to continue. PDFs are fully retired; all issues are web pages.

|Section|Lives in|
|-|-|
|1, 4, 5, 6, 6b-weekly, 9, 10, 11, 14|`DYNASTREE_ISSUE_GUIDE.md` (stable; read every issue)|
|7, 8, 12, 13|`DYNASTREE_STATE.md` (changes every issue; returned every issue)|
|2, 3, 3b, 6b, 6c, 6d, 6e, 6f, 14b, 15, 16|`DYNASTREE_REFERENCE.md` (site, scripts, pages; read only when changing them)|

**Fill in once (then never lose it):**

* GitHub repo: `https://github.com/DynastreeChronicles/Dynastree-Chronicles` (public)
* Live site (GitHub Pages): `https://dynastreechronicles.github.io/Dynastree-Chronicles/` (confirmed)
* Brief file, always the latest: `<live site>/data/brief.json`
* Zip backup: repo page > green **Code** button > **Download ZIP**.

---

## 1. COLD START (what to share, what Claude does first)

Share **four things** in a new chat. Nothing else is needed.

1. **`DYNASTREE_STATE.md`**: the small weekly file (open threads, voice bits, poll memory). Claude returns it after every issue.
2. **`DYNASTREE_ISSUE_GUIDE.md`**: the stable rules for making an issue (this file). It rarely changes.
3. **`brief.json`**: one file the Action writes every Tuesday and Wednesday. Get it by opening `<live site>/data/brief.json` and saving it, or on GitHub: `data` folder > `brief.json` > **Download raw file**. If the live-site address works for Claude's fetch tool, pasting that link instead of the file is enough.
4. **The new chat log** (the narrative source).

`DYNASTREE_REFERENCE.md` (how the site, scripts and pages work) is **not** needed for a normal issue. Attach it only when a script, page, style or convention is being changed.

`brief.json` already contains: whether a new issue is ready, the issue number and weeks to cover, the week's games (scores, MVPs, bench points), perfect lineups, top and bottom score, standings with MAXPF and draft order, FAAB balances, next week's matchups with records, every trade and claim from the week on, handles with team names, the league settings, the previous issue trimmed to its voice samples and open threads (`previous_issue_json`), the empty issue template (the schema), and `market_portfolios` (FantasyCalc portfolio value, 30-day market move, IR exposure and crash flag for every manager).

Claude must, in this order:

1. Open `brief.json`. If `ready_for_new_issue` is `false`, stop and say why (read `warnings`). Do not draft from stale data.
2. Check `data_pulled_at` is after the last Monday game. If not, ask for a fresh Action run (section 4, step 1).
3. Show a short **data summary** (records, top and bottom score, MAXPF top and bottom, trades and FAAB moves, next week's matchups) and wait for a nod before writing copy.
4. Write the deliverables in the return table below, then say which `note (issue NN): ...` lines a build would print (section 4).

**Claude's limits:** Claude's sandbox has no internet, so it can never call Sleeper. The GitHub Action does that. `github.com` pages and `raw.githubusercontent.com` links are blocked or unreachable for Claude, so share the file or the live-site link, not the repo link. If Claude needs code (only for style or script changes), attach the zip. The zip may leave out the large `assets/` folder; that is fine, because Claude never needs images to change text, data, scripts or styles, but it cannot check how artwork looks. Claude hands back **only the files it edited**, each with its repo path, never the whole repo.

### Prompt to paste

```
Prepare the next issue. Follow DYNASTREE_ISSUE_GUIDE.md and DYNASTREE_STATE.md. Numbers come only from
the attached brief.json (never type a record, score, FAAB, or pick). Check ready_for_new_issue, show me
a short data summary first, then write issue-NN.json in the schema of issue_template (previous_issue_json is a trimmed
voice sample), the new data/issues.json entry, the 12 weekly bios and the updated DYNASTREE_STATE.md. Chat log is the narrative source.
Please do not give a preview or extras to keep token allowance low.
```

Attach: the chat log, `DYNASTREE_STATE.md`, `DYNASTREE_ISSUE_GUIDE.md` and `brief.json`.

### Where to put files Claude hands back

For a normal issue Claude returns **`issue-NN.json`, the `issues.json` entry, the twelve manager bios and the updated `DYNASTREE_STATE.md`** (more only if a style or code change was requested). Upload each to the same path in GitHub (**Add file > Upload files**, or the pencil icon on an existing file; for a new folder, type the path in the filename box). Commit to `main`.

|File Claude returns|Upload to|New or replace|
|-|-|-|
|`issue-NN.json`|`data/issues/<season>/issue-NN.json`|new|
|`issues.json` (or its new entry, pasted at the top)|`data/issues.json`|replace|
|`<handle>.json` (all 12 weekly bios)|`data/bios/weekly/<handle>.json`|replace|
|`DYNASTREE_STATE.md`|repo root|replace|

Never upload `index.html`, `issues/.../index.html`, anything in `managers/`, `data/brief.json`, or anything else the Action writes; it is rebuilt on every push. If Claude changed `scripts/`, `css/`, `js/`, or `scripts/templates/`, it will say so and give the exact path for each file.

---

## 4. MAKING AN ISSUE (step by step)

1. **Wait for final data.** Monday night games done, then the Tuesday 11:00 UTC or Wednesday 13:00 UTC Action run. To force it earlier: GitHub > **Actions** > "Update league data" > **Run workflow**. Then open `brief.json` and check `ready_for_new_issue` is `true` and `data_pulled_at` is after the games. You never run any script yourself.
2. **Start a chat** with the four items in section 1 and the prompt there.
3. **Claude shows the data summary.** You confirm or add narrative notes.
4. **Claude writes** `issue-NN.json` (including its `rulings` and `receipts`, section 9), the `issues.json` entry, the 12 weekly bios, and the updated `DYNASTREE_STATE.md`. That is the whole bundle: prediction results, receipts, pick grades, the champion and the season close are all automatic.
5. **You upload** the files to the paths in section 1 (one commit). The Action rebuilds the site and a new `brief.json` automatically.
6. **Check the live site:** home page banner and ticker, the new issue page, standings order, one or two manager pages (new week in the game log, new quotes under "What the desk said"), and that no section says "failed to load". Open the Actions tab if anything is off.
7. **Update `DYNASTREE_STATE.md`** (section 14 checklist) so the next chat starts correct.

### Build notes Claude must read (printed by `build_site.py`, which Claude can run on a copy only if the zip is attached; otherwise Claude checks these by hand against `brief.json`)

* `trade X/Y: no matching trade in transactions.json` -> wrong handles or the trade is not in the feed yet; fix the JSON or wait for the pull.
* `trade ...: Sleeper logs it in Week N, the issue covers Week M` -> informational. Fine when a deal cleared the week before.
* `trade in Week N not covered by the issue` -> a real trade happened that the issue ignores; add a card or say why not.
* `waiver note for X / Player has no matching claim` -> name mismatch with the feed (use the full name as Sleeper spells it; defenses match by team name).
* `no desk aside for X in wire.desk` -> that manager's waiver list will show no aside; add one.
* `post-game card A vs B: Sleeper says A played C` -> wrong matchup in `post`; fix it.
* `pre-game card A vs B: not a Week N matchup in data/schedule.json` or `Week N game with no pre-game card` -> the cards must match the real Week N+1 schedule exactly (the Match of the Week is separate from `pre` and must not be listed twice).
* `data/schedule.json has no Week N matchups` -> cards could not be checked; use the chat log and say so.
* `issue-NN.json names 'X', who is not in the league data` -> handle typo.
* `WARNING: issue JSON has no 'desk'` -> add `desk`.

### MAXPF cross-check

The pull prints `MAXPF check: ...` in the Action log (GitHub > Actions > the run > "Pull Sleeper data"). If it lists differences above 0.05 for any team, check the 1.01 order before publishing. `sleeper_maxpf` is `null` in `standings.json`; the comparison only exists in that log.

---

## 5. SORT LAWS AND DERIVED FIELDS

* **Standings order:** wins desc, then PF desc. **PF/PA:** roster `settings` (`fpts`, `fpts_decimal`).
* **MAXPF = Max PF = the points your best possible lineup would have scored each week, added up** (Sleeper's `ppts` + `ppts_decimal`/100). It is NOT "starters + bench". Bench points only count if they would have made the best lineup, so how you set your lineup never changes it. Explain it where it first appears in an issue.
* **Draft slot:** lowest MAXPF picks 1.01. Linear, not snake. The 2027 rookie draft uses this order; payouts still go to the playoff winner.
* **FAAB remaining:** budget (500) minus bids, with trade FAAB moved between sides; rebuilt from the feed.
* **MOV:** compared with the previous final week.
* **Draft capital (FantasyCalc):** the old hand-kept FUT CAP score is retired. A team's draft capital is the combined FantasyCalc value of every pick it owns, computed automatically (`wealth.json`); the Draft order tab shows it next to **Pick value**, the market value of the team's own round-1 slot. Nothing about picks needs to be typed or returned with an issue.
* **Computed by the builder (do not type):** records, scores, bench points, left-on-bench, MVPs, Match of the Week stats (record, PF rank, best week, average PF), trade assets, waiver claims, bankroll balances and weekly change, final-score banner (biggest margin), and the previous Match of the Week result card.

## 6. LEAGUE IDENTITY

* **League:** DYNASTREE. Newsletter: **Dynastree Chronicles**. Dynasty, 12 teams, 23-round startup. Sleeper league ID `1389008727859806208`, season 2026. Lineup: QB, 2 RB, 2 WR, TE, 2 FLEX, SUPER_FLEX, DEF, 10 bench. FAAB budget $500.
* **Commissioner:** Darkspaces (team First Down Syndrome).
* **Voice:** independent desk, not the commissioner. Clever, roast-heavy (about 70/30), dynasty-first. Inside jokes beat generic advice. Managers call the desk "AI" in chat; answer with an aside when it fits.
* **Naming:** handles are bolded in prose (the builder does this automatically in `desk`; elsewhere just use the exact handle). Never bold NFL player names. Never swap a handle for "the manager" or "last place". Handle spelling is exact: `C33DeezNutzz`, `fumbduckdumbfuck`, `CMac91`. **Cassellrole is now `Johnny4Skins`** (renamed in Sleeper, Oct 2026). Renames are handled by `"former_names": ["Cassellrole"]` on the Johnny4Skins entry in `data/managers.json`: `build_site.py` swaps every old handle (dict keys and exact-match values) for the current one in the weeks, transactions, standings and issue JSON, so history stays attached to the person and the build does not break. New issues must still use the current handle. When anyone else renames: add their old handle to `former_names` in `data/managers.json`, and the old `managers/<old>/` address redirects to the new page. Free-text prose that mentions the old handle is left as written.
* **Roster id to handle (fallback):** 1 Darkspaces, 2 Snipe58, 3 StealingGas, 4 Zygon, 5 Hades9mm, 6 Johnny4Skins, 7 Sarge71, 8 C33DeezNutzz, 9 Painty69, 10 CMac91, 11 YesChef23, 12 fumbduckdumbfuck.

## 6b-weekly. WEEKLY BITS OF THE MANAGER PAGES (bios, trade machine, market flag)

* **Words (bios):** each manager has a **stable bio** `data/bios/<handle>.json` (tagline, the four-blurb `file`, per-season `headline`, `story`, `takes`, `drama`; the wealth line on each manager page is automatic, do not write it) and a **weekly bio** `data/bios/weekly/<handle>.json` that the build lays over it. The stable bio keeps the parts that do not change (story paragraph 1, The type, Signature move). Claude only ever writes the weekly file.
* **Weekly bio update (part of every issue):** Claude reads `bios` in `brief.json` (each manager's current merged bio for the active season) and returns all 12 `data/bios/weekly/<handle>.json`. A weekly file is complete for what it carries and replaces the previous one. Fields, all optional except `asof`:
  `{"asof": "Issue 9, through Week 8", "tagline": "...", "file": {"Nemesis": "...", "The desk is watching": "..."}, "season": "2026", "headline": "...", "story_keep": 1, "story": ["paragraph 2", "paragraph 3"], "takes": ["...", "..."]}`.
  `file` is a label-to-text map and lists only the blurbs that changed (normally Nemesis and The desk is watching). `story` replaces every paragraph after the first `story_keep` (default 1) of the stable bio, so write the whole tail. Facts must come from `brief.json` or the issue JSON, never from memory. The record, rank, points and transactions lines rebuild automatically; the prose changes only when the weekly files are uploaded. Desk quotes, takes and drama are mined from `data/issues/<season>/issue-*.json`. To rewrite paragraph 1 or The type, return a full stable bio instead and delete that manager's weekly file.
* **Writing rule for new issues:** use the exact handle in every `desk` line and keep `wire.desk` and `bank.notes` filled for all managers, because those lines become the manager pages' quotes.

* **Hypothetical Trade Machine from the Trade Finder.** `brief.json` > `trade_finder` > `suggestions` holds up to 8 realistic league-wide deals from the same logic as the site's Trade Finder (one side has a real lineup need or, for a rebuilder, a timeline fit; values within 10%; each team read as contender, retooling or rebuilder). **Build the issue's hypothetical trades from these**: use their `a`, `b`, `as`, `bs` exactly as written (the assets are in issue wording, the values and the calculator link depend on it) and write the desk commentary yourself. Do not invent assets. Each hypothetical card shows a **Load in trade calculator** tag that opens the calculator with that trade filled in.

* **Reading the flag.** Statuses: `crash`, `correction`, `stable`, `bull`. `move30` is the 30-day market move of the players held *now* (trade-neutral). `since_change` is the change since the last snapshot at least 5 days old (it includes trades; empty until the second weekly run). `sidelined` is value on IR or players Sleeper marks Out, IR, PUP, Doubtful or Sus. A manager is on crash watch when `move30_pct` is -5% or worse, or `sidelined_pct` is 25% or more. Thresholds are constants at the top of `pull_values.py`; the headline wording is the `STATUS` table in `build_managers.py`.

* **Writing with it.** Claude reads `brief.json` > `market_portfolios` for the market angle (it lists `crash_watch` first). Numbers come from there only. Say "market value", never "worth" in dollars, and never claim an injury moved a value unless `move30` shows it. A manager on crash watch is fair game for the desk.

---

## 9. ISSUE JSON SCHEMA (`data/issues/issue-NN.json`)

Copy the latest issue file; `data/issues/issue-template.json` is the empty skeleton. Every key below is read by `js/issue.js` or `build_site.py`.

|Key|Shape|Notes|
|-|-|-|
|`desk`|list of strings|From the Desk paragraphs. Handles auto-bolded. Required.|
|`pull`|string, optional|Hero pull quote. Default: first sentence of `desk[0]`.|
|`hero`, `zero`|`{manager, text, desk}`|`text` = the take, `desk` = one-line aside. Score and "perfect lineup" label come from data. If omitted: hero = perfect lineup first, else top score; zero = lowest score. Always supply them.|
|`prev_motw`|`{issue, a, b, note}`|The previous issue's Match of the Week; the builder adds scores and winner.|
|`prev_poll`|`{issue, q, opts, result, note}`, from Issue 5 on|Last issue's poll results, shown as bars. `result` = vote counts per option, same order as `opts` (from the chat log, never guessed), or a short text line if only the winner is known. `note` = the desk's one-line reaction. Never rendered before Issue 5.|
|`bank.notes`|`{handle: line}` for all 12|One line per manager under their FAAB balance.|
|`wire.block`|optional list of `{mgr, players:["Name (POS, TEAM)"], desk}`|Trade-block listings for the week (used by Issues 2 and 3).|
|`wire.trades`|list of `{a, b, ai, bi, ah, bh, ga, gb, desk}`|`ai/bi` immediate impact, `ah/bh` dynasty horizon, `ga/gb` letter grades (A+ to F). Assets (`ar/br`) are filled from the feed. Optional `match` (a player name) tells apart two trades between the same pair of managers.|
|`wire.waivers`|list of `{mgr, player, flag, note}`|`flag` is `mvp` (exactly 1), `fav` (about 3), or `note`. Matched to the feed by manager + player.|
|`wire.desk`|`{handle: line}`|One aside per manager who made a claim.|
|`post`|list of `{a, b, tag, aged, means, key, ga, gb, desk}`|One per Week-N game, `aged/means/key` are 3-line lists. Scores, records, bench, MVPs are filled from data.|
|`quote`|`{text, by, desk}`|Quote of the week.|
|`drama`|list of `{h, heat, p, desk}`|About 4; `heat` 0 to 100+.|
|`hits`|list of `[quote, who]`|Chat greatest hits.|
|`trades`|`{note, items:[{t, a, as, b, bs, ay, by, desk}]}`|Hypothetical trade machine. `as/bs` are asset lists, `ay/by` the reasons. `note` is exactly "The Hypothetical Trade Machine stays open through Week 12." (no Trade Finder or 10% wording).|
|`pre`|list of `{a, b, pa, pb, wa, wb, ma, mb, la, lb, edge, desk}`|One per Week N+1 game. `pa/pb` projections, `wa/wb` win % (sum 100), `ma/mb` must-get-right, `la/lb` landmines. Records are filled from data.|
|`motw`|same as `pre` plus `stakes`, `sw`, `verdict`|`sw` = `[[handle, [strengths x3], [weak links x3]], [other handle, ...]]`. `stats` is computed.|
|`bottom`|`{paras:[...]}`|Bottom line. The MAXPF explainer is appended automatically only for issues in `EXPLAIN` in `build_site.py` (Issue 4); other issues use `closer`.|
|`closer`|`{label?, h, text}`, optional|Desk sign-off card shown in place of the MAXPF explainer in every issue except those listed in `EXPLAIN` in `build_site.py` (currently Issue 4 only).|
|`bold`|list of `[headline, text]`|Bold predictions, each with a deadline so the ledger can score it next issue. **From Issue 6 on, exactly 2 bold predictions per issue** (earlier issues have 3 or 4; the build prints a warning if a later issue has any other number).|
|`rulings`|list of `{issue, i, result, note, star?}`|Settles bold predictions from EARLIER issues. `issue` = that issue's number, `i` = its index in that issue's `bold` list (starts at 0), `result` = `hit`, `miss` or `pending`. Take them from `brief.json` > `predictions_to_rule`, check the evidence in the data, and cite it in `note`. `[]` if none resolved.|
|`receipts`|list of `{who, text, context?, date?, tags?, status, note?}`|Hot takes from the chat log that did not make the issue. `text` verbatim, `who` an exact handle. `status`: `aged_well`, `aged_badly`, `pending`. Re-list an older one with a new `status` to update it. `[]` if none.|
|`poll`|`{id, q, opts, desk}`|`id` like `issue-05`. Shown read-only with "Vote in the league's Sleeper chat"; the poll itself is created in the Sleeper chat. No `endpoint` any more. Optional: with neither `poll` nor `prev_poll`, the Poll nav link and section are left out. Polls began in Issue 4, so none appear on Issues 1 to 3.|

### `data/issues.json` entry (newest first)

```
{"no": 5, "year": 2026, "title": "...", "weeks": "Week 4 post-game and Week 5 pre-game",
 "web": true, "month": "October 2026", "dek": "...", "banner": "...", "ticker": ["...", "...", "...", "..."],
 "wire_week": 4, "standings_week": 4}
```

* `wire_week` = the post-game week; the pre-game week is `wire_week + 1`. `web: true` for every new issue. There is no `pdf` field.
* `season_final` (optional): `true` on the season-review issue only. With a decided champion, it makes the next pull close the season and open the next volume.
* `title`, `dek`, `banner`, `ticker` feed the home page; `banner` is short, `ticker` is 4 headlines. Lead with the biggest story.
* Every issue is `"web": true` with no `pdf`.
* `tx_from` (optional, `{"waiver": ms, "free_agent": ms}`): for a retro issue whose week already had claims in an earlier issue. Only claims created after these timestamps are listed and counted in that issue's bankroll change. Issue 2 uses Issue 1's `tx_cutoff` values.

## 10. LEAGUE RULES (live)

* 2027 rookie draft: ordered by MAXPF as defined in section 5, linear. Payouts still go to the playoff winner.
* Trade vetoes enabled. Tanking now means selling scoring assets.

## 11. CONTENT REQUIREMENTS

* Lead with the biggest story in the title and dek. Explain MAXPF where it first appears.
* Say each fact once. From the Desk sets up, sections add detail, Bottom Line closes. Do not recap.
* Every team scannable somewhere. Post-game and pre-game cards are specific to the game (no shared placeholders).
* Waivers: 1 gold MVP, about 3 green Desk Favorites. Drama: about 4 segments, desk take under each.
* Predictions get a deadline so the ledger can score them next issue.

## 14. AFTER PUBLISH (checklist, then return the updated DYNASTREE_STATE.md)

* [ ] Change "Last updated" and "Next issue" at the top of `DYNASTREE_STATE.md`.
* [ ] Display text owned by the build, not the issue file (as of Issue 6 feedback): remove "Grouped by manager. Gold marks the Waiver Wire MVP, green the Desk Favorite." under Transactions, and shorten the trade-values footer to "Values: FantasyCalc dynasty trade values (superflex, 12 teams, full PPR)" (linked, no lock date or pick/FAAB sentence). Both live in the build scripts, so they need a repo change, not an issue edit.
* [ ] Issue values: after the Action builds the issue, `data/issues/<year>/values-NN.json` exists (it freezes every FantasyCalc number the issue shows).
* [ ] Manager bios: all 12 `data/bios/weekly/*.json` uploaded (new `asof`, new story tail, refreshed Nemesis and watching blurbs). - [ ] Section 7 baseline order. [ ] Section 8 bits. [ ] Sections 12 and 13 threads, predictions, poll.
* [ ] Upload the files from the table in section 1 together in one commit.
* [ ] After the Action finishes, open one manager page and confirm the new week and a new desk quote appear (manager pages rebuild automatically; no extra upload).
* [ ] Renames are now detected automatically (same Sleeper user id, new handle) and the old handle is added to `former_names`. Check the Actions log for a `rename detected:` line. Add `former_names` by hand only for an old handle the pull could not match.
* [ ] Predictions and receipts: the issue file's `rulings` settle every entry in `brief.json` > `predictions_to_rule` that now has an answer, and `receipts` holds the new hot takes. If `brief.json` > `season_end.action` is present, write the season-review issue with `"season_final": true` and add the volume `story` to `history.json`.
* [ ] Market: read `brief.json` > `market_portfolios` (crash watch, biggest movers, IR exposure) and use it where it adds to the issue.
* [ ] If scripts, the workflow, a page, or a convention changed this session: update the README and the matching sections of `DYNASTREE_REFERENCE.md` (14b).
* [ ] Re-download a fresh zip once a month and keep it somewhere outside GitHub as a backup.

