# DYNASTREE CHRONICLES: MASTER STATE (v5, web only, one-file data brief, manager pages)

**Last updated:** after Issue 4 (final), plus the web-only rebuild and the one-file brief (v4), the retro-build of Issue 3 as a web page, and the **manager pages** (one page per manager, rebuilt automatically on every issue upload). **Next issue:** Volume 1, Issue 5 (Week 4 post-game + Week 5 pre-game).

> This file is the whole memory of the project. If every chat is gone, this file + `brief.json` (the one data file) + the new chat log is enough to continue. PDFs are fully retired: no PDF links, buttons, or fields anywhere on the site, and there is no `build_pdf.py`. All issues are web pages (Issues 2 and 3 were retro-built from their old PDFs and chat logs).

**Fill in once (then never lose it):**
* GitHub repo: `https://github.com/DynastreeChronicles/Dynastree-Chronicles` (public)
* Live site (GitHub Pages): `https://dynastreechronicles.github.io/Dynastree-Chronicles/` (**confirm this is the real address and correct it here if not**)
* Brief file, always the latest: `<live site>/data/brief.json`
* Zip backup: repo page > green **Code** button > **Download ZIP**.

---

## 1. COLD START (what to share, what Claude does first)

Share **three things** in a new chat. Nothing else is needed.
1. **This file** (`DYNASTREE_MASTER_STATE.md`).
2. **`brief.json`**: one file the Action writes every Tuesday and Wednesday. Get it by opening `<live site>/data/brief.json` and saving it, or on GitHub: `data` folder > `brief.json` > **Download raw file**. If the live-site address works for Claude's fetch tool, pasting that link instead of the file is enough.
3. **The new chat log** (the narrative source).

`brief.json` already contains: whether a new issue is ready, the issue number and weeks to cover, the week's games (scores, MVPs, bench points), perfect lineups, top and bottom score, standings with MAXPF and draft order, FAAB balances, next week's matchups with records, every trade and claim from the week on, FUT CAP, handles with team names, the league settings, the full JSON of the previous issue (format and voice reference), and the empty issue template.

Claude must, in this order:
1. Open `brief.json`. If `ready_for_new_issue` is `false`, stop and say why (read `warnings`). Do not draft from stale data.
2. Check `data_pulled_at` is after the last Monday game. If not, ask for a fresh Action run (section 4, step 1).
3. Show a short **data summary** (records, top and bottom score, MAXPF top and bottom, trades and FAAB moves, next week's matchups) and wait for a nod before writing copy.
4. Write the deliverables in section 3's return table, then say which `note (issue NN): ...` lines a build would print (section 4).

**Claude's limits:** Claude's sandbox has no internet, so it can never call Sleeper. The GitHub Action does that. `github.com` pages and `raw.githubusercontent.com` links are blocked or unreachable for Claude, so share the file or the live-site link, not the repo link. If Claude needs code (only for style or script changes), attach the zip.

### Prompt to paste
```
Prepare the next issue. Follow DYNASTREE_MASTER_STATE.md. Numbers come only from the attached brief.json
(never type a record, score, FAAB, or pick). Check ready_for_new_issue, show me a short data summary
first, then write issue-NN.json in the same schema as previous_issue_json, the new data/issues.json
entry, an updated fut_cap.json if pick ownership changed, and the updated master. Chat log is the
narrative source. Tell me the GitHub path for every file.
```

---

## 2. HOW THE SITE WORKS (one source of truth)

```
Sleeper API --scripts/sleeper_pull.py (GitHub Action)--> data/*.json          all numbers (incl. schedule.json)
data/ + data/issues/*.json --scripts/build_managers.py--> managers/index.html + managers/<handle>/index.html   manager pages
data/ --scripts/make_brief.py (GitHub Action)--> data/brief.json             the one file you share with Claude
chat log + this file --Claude--> data/issues/issue-NN.json + data/issues.json   all words
data/ + scripts/templates/issue.html --scripts/build_site.py--> index.html + issues/2026/issue-NN/index.html
```

* **Numbers:** Sleeper data wins over anything in this file or the chat.
* **Words:** issue JSON only. No hand-edited HTML, ever. Pages are regenerated from the template on every build, so manual edits to an issue page are overwritten.
* **Look:** `css/dynastree.css` and `js/issue.js` (rendering), `scripts/templates/issue.html` (page shell). Change style there, never in an issue.
* If a page looks wrong, the data or JSON is wrong or stale. Fix the source, rebuild.

### The Action (`.github/workflows/update-data.yml`)
Runs the Sleeper pull, then `build_site.py`, then `build_managers.py`, then `make_brief.py`, then commits `data/`, `index.html`, `issues/`, `managers/`, `assets/avatars/`. It triggers:
* Tuesday 11:00 UTC and Wednesday 13:00 UTC (after Monday Night Football, then after stat corrections);
* by hand: GitHub > **Actions** > "Update league data" > **Run workflow**;
* automatically when a push touches `data/issues/**`, `data/issues.json`, `data/fut_cap.json`, `data/managers.json`, `scripts/**`, `css/**`, or `js/**`.

So: **upload the issue files, wait about a minute, and the site is rebuilt, including every manager page** (records, game logs, transactions and desk quotes refresh from the new data and the new issue JSON). If the site does not change, open the Actions tab and read the failed run's log.

---

## 3. REPO MAP (where everything lives)

| Path | What it is | Who writes it |
|---|---|---|
| `DYNASTREE_MASTER_STATE.md` | this file (keep it in the repo root so it is in every zip) | Claude returns it, you upload |
| `README.md` | short how-it-works | static |
| `index.html` | home page: banner, ticker, leaderboard, standings, archive, rules | build_site.py (never by hand) |
| `issues/2026/issue-NN/index.html` | one page per issue | build_site.py (never by hand) |
| `data/league.json` | league id, roster slots, budget, `generated_at`, weeks with scores | Action |
| `data/managers.json` | handle, team name, avatar path; optional `former_names` (old handles, see section 6) | Action writes it; `former_names` is added by hand |
| `data/standings.json` | live standings, MAXPF, draft pick, FAAB | Action |
| `data/efficiency.json` | points vs optimal per manager | Action |
| `data/transactions.json` | every trade, waiver claim, bid | Action |
| `data/schedule.json` | every matchup for weeks 1 to 18 (this is where next week's pre-game games come from) | Action |
| `data/brief.json` | **the one file to share with Claude** (see section 1) | Action |
| `data/weeks/week-NN.json` | per-team scores, optimal lineup, bench, MVP; `"final"` flag | Action |
| `data/issues.json` | issue index (title, dek, banner, ticker, weeks, `wire_week`) | **Claude** |
| `data/issues/issue-NN.json` | all prose for issue NN | **Claude** |
| `data/issues/issue-template.json` | empty schema to copy | static |
| `data/fut_cap.json` | future-capital score per manager | **Claude** (per issue, see section 5) |
| `scripts/sleeper_pull.py` | Sleeper pull + standings/MAXPF logic | static |
| `scripts/build_site.py` | builds home + issue pages | static |
| `scripts/build_managers.py` | builds the manager hub and one page per manager; imports `build_site.py`, so it must run after it | static |
| `scripts/make_brief.py` | builds `data/brief.json` | static |
| `scripts/templates/issue.html` | issue page shell with `{{TOKENS}}` | static |
| `css/dynastree.css` | the stylesheet in use | static |
| `css/managers.css` | styles for the manager pages (loaded only by them) | static |
| `managers/index.html`, `managers/<handle>/index.html` | manager hub and one page per manager (avatar, record, stat tiles, game log, transactions, desk quotes). `managers/<old handle>/` is a redirect stub after a rename | build_managers.py (never by hand) |
| `css/style.css` | **legacy, unused**; safe to delete | none |
| `js/issue.js`, `js/site.js` | render issue cards; icons and sort toggle | static |
| `assets/` | crests, badges, grade images, trophies, icons | static |
| `assets/avatars/*.webp` | manager avatars | Action |
| `pdf/` folder | old PDFs, no longer linked anywhere; safe to delete | frozen |
| `.github/workflows/update-data.yml` | the Action | static |

### Where to put files Claude hands back

For a normal issue Claude returns **three files** (a fourth only if a style or code change was requested). Upload each to the same path in GitHub (**Add file > Upload files**, or the pencil icon on an existing file; for a new folder, type the path in the filename box). Commit to `main`.

| File Claude returns | Upload to | New or replace |
|---|---|---|
| `issue-NN.json` | `data/issues/issue-NN.json` | new |
| `issues.json` | `data/issues.json` | replace |
| `fut_cap.json` | `data/fut_cap.json` | replace |
| `DYNASTREE_MASTER_STATE.md` (updated per section 11) | repo root | replace |

Never upload `index.html`, `issues/.../index.html`, anything in `managers/`, `data/brief.json`, or anything else the Action writes; it is rebuilt on every push. If Claude changed `scripts/`, `css/`, `js/`, or `scripts/templates/`, it will say so and give the exact path for each file.

---

## 4. MAKING AN ISSUE (step by step)

1. **Wait for final data.** Monday night games done, then the Tuesday 11:00 UTC or Wednesday 13:00 UTC Action run. To force it earlier: GitHub > **Actions** > "Update league data" > **Run workflow**. Then open `brief.json` and check `ready_for_new_issue` is `true` and `data_pulled_at` is after the games. You never run any script yourself.
2. **Start a chat** with the three items in section 1 and the prompt there.
3. **Claude shows the data summary.** You confirm or add narrative notes.
4. **Claude writes** `issue-NN.json`, the `issues.json` entry, `fut_cap.json` if needed, and the updated master.
5. **You upload** the files to the paths in section 3 (one commit). The Action rebuilds the site and a new `brief.json` automatically.
6. **Check the live site:** home page banner and ticker, the new issue page, standings order, one or two manager pages (new week in the game log, new quotes under "What the desk said"), and that no section says "failed to load". Open the Actions tab if anything is off.
7. **Update this file** (section 14 checklist) so the next chat starts correct.

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
* **FUT CAP weights:** Early 1st (1.01 to 1.04) 100, Mid/Late 1st 75, 2nd-year 1st 60, 3rd-year 1st 50, any 2nd 30, any 3rd 10. Stored in `data/fut_cap.json` as `{"Handle": number}`. It is hand-maintained: recompute it from pick ownership each issue (use `transactions.json` trades since the last update) and return the file. Current values after Issue 4: Zygon 85, Hades9mm 55, C33DeezNutzz 70, Johnny4Skins 65, YesChef23 80, Darkspaces 140, fumbduckdumbfuck 90, CMac91 75, Snipe58 40, StealingGas 175, Sarge71 95, Painty69 100.
* **Computed by the builder (do not type):** records, scores, bench points, left-on-bench, MVPs, Match of the Week stats (record, PF rank, best week, average PF), trade assets, waiver claims, bankroll balances and weekly change, final-score banner (biggest margin), and the previous Match of the Week result card.

## 6. LEAGUE IDENTITY
* **League:** DYNASTREE. Newsletter: **Dynastree Chronicles**. Dynasty, 12 teams, 23-round startup. Sleeper league ID `1389008727859806208`, season 2026. Lineup: QB, 2 RB, 2 WR, TE, 2 FLEX, SUPER_FLEX, DEF, 10 bench. FAAB budget $500.
* **Commissioner:** Darkspaces (team First Down Syndrome).
* **Voice:** independent desk, not the commissioner. Clever, roast-heavy (about 70/30), dynasty-first. Inside jokes beat generic advice. Managers call the desk "AI" in chat; answer with an aside when it fits.
* **Naming:** handles are bolded in prose (the builder does this automatically in `desk`; elsewhere just use the exact handle). Never bold NFL player names. Never swap a handle for "the manager" or "last place". Handle spelling is exact: `C33DeezNutzz`, `fumbduckdumbfuck`, `CMac91`. **Cassellrole is now `Johnny4Skins`** (renamed in Sleeper, Oct 2026). Renames are handled by `"former_names": ["Cassellrole"]` on the Johnny4Skins entry in `data/managers.json`: `build_site.py` swaps every old handle (dict keys and exact-match values) for the current one in the weeks, transactions, standings, fut_cap and issue JSON, so history stays attached to the person and the build does not break. New issues must still use the current handle. When anyone else renames: add their old handle to `former_names` in `data/managers.json`, and the old `managers/<old>/` address redirects to the new page. Free-text prose that mentions the old handle is left as written.
* **Roster id to handle (fallback):** 1 Darkspaces, 2 Snipe58, 3 StealingGas, 4 Zygon, 5 Hades9mm, 6 Johnny4Skins, 7 Sarge71, 8 C33DeezNutzz, 9 Painty69, 10 CMac91, 11 YesChef23, 12 fumbduckdumbfuck.

## 6b. MANAGER PAGES
* One page per manager at `managers/<handle lowercased>/`, plus the hub at `managers/`. Linked from the home nav, the standings tables and the leaderboard.
* **Numbers** (record, rank, PF/PA, MAXPF, efficiency, draft slot, FAAB, game log, every trade and claim) come from `data/`. **Desk quotes** are mined from every `data/issues/issue-*.json`: `wire.desk[handle]`, trade/post/pre/motw/draft/trade-machine `desk` lines where the manager is a party, `drama` entries that name them, `quote` (by), `hero`/`zero`, `bank.notes[handle]`, and sentences in the `desk` column that name them.
* **Writing rule for new issues:** use the exact handle in every `desk` line and keep `wire.desk` and `bank.notes` filled for all managers, because those lines become the manager pages' quotes. A manager with no desk lines shows an empty-state message.
* Nothing to upload: the Action rebuilds the `managers/` folder on every issue upload. A failed `build_managers.py` step shows as its own red step in the Actions log.

## 7. POWER RANKINGS BASELINE (Issue 5 MOV "from")
Desk order after Issue 4: 1 Zygon, 2 Hades9mm, 3 C33DeezNutzz, 4 Johnny4Skins, 5 YesChef23, 6 Darkspaces, 7 fumbduckdumbfuck, 8 CMac91, 9 Snipe58, 10 StealingGas, 11 Sarge71, 12 Painty69. Power rankings are desk judgment and should differ from the standings; say why where they do. (The web page does not yet render a power-rankings table; if used, put it in `bottom.paras`.)

## 8. ACTIVE BITS (voice continuity)
* **StealingGas:** open tank ("Future Therapy Bills"), laboratory energy.
* **Zygon:** IR Predictor, algorithm-first, handcuffs on the block as a dare.
* **Darkspaces:** Jerry Jones, block-and-negotiate, commissioner who also competes.
* **Hades9mm:** "Sleeper puss", life after dealing London. **Johnny4Skins:** dual-QB identity.
* **Painty69 and YesChef23:** the rivalry that may resurface. **Sarge71 and Painty69:** star RB, thin supporting cast.
* Retire or rotate overused lines (Jerry Jones, "the laboratory", "classic") so each appears at most once per issue.

## 9. ISSUE JSON SCHEMA (`data/issues/issue-NN.json`)
Copy the latest issue file; `data/issues/issue-template.json` is the empty skeleton. Every key below is read by `js/issue.js` or `build_site.py`.

| Key | Shape | Notes |
|---|---|---|
| `desk` | list of strings | From the Desk paragraphs. Handles auto-bolded. Required. |
| `pull` | string, optional | Hero pull quote. Default: first sentence of `desk[0]`. |
| `hero`, `zero` | `{manager, text, desk}` | `text` = the take, `desk` = one-line aside. Score and "perfect lineup" label come from data. If omitted: hero = perfect lineup first, else top score; zero = lowest score. Always supply them. |
| `prev_motw` | `{issue, a, b, note}` | The previous issue's Match of the Week; the builder adds scores and winner. |
| `prev_poll` | `{issue, q, opts, result, note}`, optional | Template has it; the web page does not render it yet. Put poll results in `drama` or `bottom`. |
| `bank.notes` | `{handle: line}` for all 12 | One line per manager under their FAAB balance. |
| `wire.block` | optional list of `{mgr, players:["Name (POS, TEAM)"], desk}` | Trade-block listings for the week (used by Issues 2 and 3). |
| `wire.trades` | list of `{a, b, ai, bi, ah, bh, ga, gb, desk}` | `ai/bi` immediate impact, `ah/bh` dynasty horizon, `ga/gb` letter grades (A+ to F). Assets (`ar/br`) are filled from the feed. Optional `match` (a player name) tells apart two trades between the same pair of managers. |
| `wire.waivers` | list of `{mgr, player, flag, note}` | `flag` is `mvp` (exactly 1), `fav` (about 3), or `note`. Matched to the feed by manager + player. |
| `wire.desk` | `{handle: line}` | One aside per manager who made a claim. |
| `post` | list of `{a, b, tag, aged, means, key, ga, gb, desk}` | One per Week-N game, `aged/means/key` are 3-line lists. Scores, records, bench, MVPs are filled from data. |
| `quote` | `{text, by, desk}` | Quote of the week. |
| `drama` | list of `{h, heat, p, desk}` | About 4; `heat` 0 to 100+. |
| `hits` | list of `[quote, who]` | Chat greatest hits. |
| `trades` | `{note, items:[{t, a, as, b, bs, ay, by, desk}]}` | Hypothetical trade machine. `as/bs` are asset lists, `ay/by` the reasons. |
| `pre` | list of `{a, b, pa, pb, wa, wb, ma, mb, la, lb, edge, desk}` | One per Week N+1 game. `pa/pb` projections, `wa/wb` win % (sum 100), `ma/mb` must-get-right, `la/lb` landmines. Records are filled from data. |
| `motw` | same as `pre` plus `stakes`, `sw`, `verdict` | `sw` = `[[handle, [strengths x3], [weak links x3]], [other handle, ...]]`. `stats` is computed. |
| `bottom` | `{paras:[...]}` | Bottom line. The MAXPF explainer is appended automatically. |
| `bold` | list of `[headline, text]` | Bold predictions, each with a deadline so the ledger can score it next issue. |
| `poll` | `{id, endpoint, q, opts, desk}` | `id` like `issue-05`; `endpoint` empty (votes happen in the Sleeper app). Optional: with no `poll`, the Poll nav link and section are left out (Issues 1 to 3 have none). |

### `data/issues.json` entry (newest first)
```
{"no": 5, "year": 2026, "title": "...", "weeks": "Week 4 post-game and Week 5 pre-game",
 "web": true, "month": "October 2026", "dek": "...", "banner": "...", "ticker": ["...", "...", "...", "..."],
 "wire_week": 4, "standings_week": 4}
```
* `wire_week` = the post-game week; the pre-game week is `wire_week + 1`. `web: true` for every new issue. There is no `pdf` field.
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

## 12. OPEN THREADS (update after every issue)
* Achane and Swift on Darkspaces' block; public price was a 1st. Zygon: Emmett Johnson and Blake Corum listed.
* StealingGas: tank optics vs big scoring weeks. Snipe58: Stafford must convert. Hades9mm: life after London. Dart ($298) usage on StealingGas.
* Sarge71 and Painty69 need a supporting cast.
* Capital moves (verify against `transactions.json`): London deal (StealingGas gets London, Green, a 2027 1st; Hades9mm gets Johnston, Ward, Henderson, a 2027 3rd; Sleeper logs it in Week 2). Stafford deal (Darkspaces gets 2028 2nd, 2029 2nd, $100 FAAB; Snipe58 gets Stafford).
* Issue 4 predictions to score in Issue 5: "Achane moves before Week 5" (Darkspaces, price a 1st or better). Check `bold` in `issue-04.json` for the rest.

## 13. POLL MEMORY
Issue 4: which 0-3 team is most likely to still be bottom-three at the deadline? (StealingGas / Painty69 / Sarge71 / None.) Carry results forward only if votes appear in the chat log; otherwise write a fresh poll.

## 14. AFTER PUBLISH (checklist, then return an updated master)
- [ ] Change "Last updated" and "Next issue" at the top.
- [ ] Section 5 FUT CAP numbers = what `fut_cap.json` now says.
- [ ] Section 7 baseline order. [ ] Section 8 bits. [ ] Sections 12 and 13 threads, predictions, poll.
- [ ] Upload the files from the table in section 3 together in one commit.
- [ ] After the Action finishes, open one manager page and confirm the new week and a new desk quote appear (manager pages rebuild automatically; no extra upload).
- [ ] If anyone renamed in Sleeper, add their old handle to `former_names` in `data/managers.json` (section 6).
- [ ] Re-download a fresh zip once a month and keep it somewhere outside GitHub as a backup.

## 15. IF THINGS GO WRONG
* **Whole chat history lost:** nothing is lost. Start a new chat with the three items in section 1.
* **Claude cannot open the live-site link:** download `brief.json` yourself and attach it. If the site is down, Actions > latest run > the `data` folder in the repo has the same file.
* **Repo lost or deleted:** this file records the data model and the rules but not the code. Restore from a saved zip (this is why the monthly backup in section 14 matters). GitHub may also let you restore a recently deleted repo from your account settings, but do not count on it. Without the code, a new build of `sleeper_pull.py`, `build_site.py`, the issue template, CSS, and JS would have to be recreated from the schema in section 9.
* **Site did not update after upload:** Actions tab > open the latest "Update league data" run > read the red step. Common causes: invalid JSON (missing comma or quote), a handle typo, or `issues.json` missing `wire_week`.
* **Numbers look wrong:** wrong or stale data; run the Action by hand, re-download the zip, rebuild. Never patch a number in the JSON prose to match.
* **Manager page looks wrong or is missing:** open the Actions run and read the "Build manager pages" step. It needs `scripts/build_managers.py`, `css/managers.css` and `data/managers.json` in the repo. Style changes go in `css/managers.css`.
* **Style change wanted:** edit `css/dynastree.css` or `scripts/templates/issue.html`; it applies to every issue on the next build.

## 16. BRAND FOOTER
DYNASTREE CHRONICLES: Documenting your worst takes and archiving your receipts, because time heals all wounds but screenshots last forever. Questions, corrections, or demands for a higher ranking: settle it on the field (or the trade screen).
