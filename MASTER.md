# DYNASTREE CHRONICLES — MASTER SAVE STATE

Draft v0.1. Seeded from the repo (Issues 1–4, scripts, data). Lines marked **[CONFIRM]** are my reading of the pattern, not something you told me. Lines marked **[FILL]** I can't know. Edit freely; this file is the source of truth, and anything not in it, Claude should ask about instead of inventing.

---

## 0. The weekly contract

**You provide:** (1) Sleeper chat log(s) for the week, pasted or as a .txt; (2) this file; (3) the repo zip (or just `data/` + `scripts/` after the Tuesday/Wednesday Action has run); (4) any notes of your own ("make Zygon the Zero", "skip the poll").

**Claude returns:**
1. `data/issues/issue-NN.json` — prose only (schema in section 6).
2. An added entry in `data/issues.json` with `"web": true` and **no `pdf` field**.
3. A short "needs your eyes" list: every claim Claude could not verify from `data/` or the chat log.
4. Updated sections 8 (history) and 9 (open bits) of this file, so next week starts where this one ended.

**You do:** commit, let the Action rebuild, publish.

## 1. Decisions needed before this file is final

1. **MAXPF: DECIDED.** MAXPF is Sleeper's own Max PF (the app's Standings, More Details, MAX PF): the points of each week's best possible lineup, summed over the season. It is **not** starters plus bench. Lowest MAXPF = 1.01 in the linear 2027 rookie draft. The commissioner uses Sleeper's number, so it is the one non-debatable line.
   - **Source of truth:** Sleeper's figure (`settings.ppts` + `ppts_decimal` on each roster, from the rosters endpoint). The site shows that number.
   - **Cross-check:** our own optimal-lineup calculation from the matchup data stays in the pull as a check and as the per-week number. The pull must print a mismatch warning, and any mismatch is resolved in Sleeper's favor.
   - **Known gap to fix:** `sleeper_maxpf` came back empty for all 12 managers in the current data, so the cross-check has never run. First job on the pull script is to confirm `ppts` is actually being read. Until then, the app is the check: compare any manager's app figure to our computed total (Through Week 3, ours: Hades9mm 613.32, Darkspaces 390.56).
   - **Stale data to flush:** the weekly files in the uploaded zip store starters plus bench in their `maxpf` field. The pull script already computes the optimal lineup, so the next Action run should regenerate them. Check that after the run.
   - **Wording rule:** never describe MAXPF as "starters + bench," "total roster points," or "everything your whole roster scores." Say "best possible lineup" or "Max PF."
2. **Projections:** tie to Sleeper (your call). Sleeper's projections endpoint is undocumented, so it has to be tested from the Action before we depend on it (section 12). Win percentages are not a Sleeper figure; they would be our own calculation from projections and get labeled that way. Until the pull works, projections are marked "desk estimate" on the page.
3. **Issue 1–3 on the web.** Backfill later, after the infrastructure work. **[FILL: infrastructure list to come]**

## 2. League facts (from `data/league.json` and Issue 4)

- Sleeper league "DYNASTREE", id `1389008727859806208`, season 2026, 12 teams, dynasty, 23-round startup draft.
- Lineup: QB, 2 RB, 2 WR, TE, 2 FLEX, SUPER_FLEX, DEF; 10 bench.
- FAAB: $500 budget per manager. Waiver priority shown as PRI.
- Commissioner: Darkspaces.
- 2027 rookie draft: **linear**, ordered by Sleeper's Max PF (best possible lineup each week, summed), lowest = 1.01, highest = 12th. (Set in Issue 4.)
- Trade vetoes: on (as of Issue 4). Hypothetical Trade Machine open through Week 12.
- Payouts go to the playoff winner, not to draft position.
- Playoffs: seeds 1–2 get the Week 15 bye; seeds 3–6 play in. **[CONFIRM weeks and format]**
- Standings terms used on the site: PF, PA, MOV (rank movement), PRI, FAAB, FUT CAP, MAXPF, DRFT.
- Other league rules (scoring format, trade deadline, keeper/cap rules, taxi/IR): **[FILL]**

## 3. The cast

| Manager | Team name | Running bit (as used in Issues 1–4) |
|---|---|---|
| Darkspaces | First Down Syndrome | Commissioner. "Jerry" / Jerry Jones spending energy, perpetual trade block |
| Zygon | IR Predictor | The nickname that keeps printing; "the formula / the algorithm" |
| StealingGas | Future Therapy Bills | "The laboratory", the announced tank, RB "science experiment" |
| Hades9mm | The sleeper puss | Big FAAB spender, London deal |
| C33DeezNutzz | BBQnBBWs | "The constellation" of studs |
| Painty69 | (none) | "The crime family" |
| Sarge71 | (none) | Elite RBs, no supporting cast |
| Snipe58 | (none) | Buys vets (Stafford), win-now moves |
| Cassellrole, CMac91, YesChef23, fumbduckdumbfuck | (none) | **[FILL: bits, if any]** |

Rule: a running bit only gets reused if it's still true that week. Retire it when the facts change.

## 4. Voice and tone

Distilled from Issues 1–4. **[CONFIRM all]**

- Sports-desk voice: dry, confident, a little cruel, affectionate underneath. "The desk" is a character and speaks in first-person plural or third person ("The desk has receipts").
- Short declaratives. Punchlines at the end of a paragraph. One joke per beat, then move on.
- Roast the move, not the person's life. Targets are lineup decisions, trades, FAAB, chat takes. **[PROPOSED RULE]** Nothing about real-life topics, family, health, work, or money outside the league, even if it appears in chat.
- Profanity: the league chat is crude; the newsletter is mostly clean. Don't reprint slurs or anything a manager would be embarrassed to see on a public site. Redact or paraphrase. **[CONFIRM level]**
- Grades are earned: no automatic B's. Use the full scale (A+ to F, see section 7).
- The published site is public (GitHub Pages). Write as if every manager and their families will read it.

## 5. Sourcing rules (non-negotiable)

0. **MAXPF is Sleeper's Max PF.** See section 1. Never restate it as starters + bench.

1. **Numbers come from `data/`, never from prose.** Scores, records, standings, FAAB, MAXPF, draft slots, bench points, MVPs, trade assets, and waiver claims are computed by the build. Claude doesn't type them into the JSON. Where a number appears inside a sentence, Claude copies it from `data/`.
2. **Quotes are verbatim from the chat log**, trimmed only at the ends, attributed to the right username, with the context line in `by`. If a quote can't be found in the log, it doesn't run.
3. **Chat events must appear in the log.** Offers, "I'll give him for free," block listings: Claude cites what was said, and doesn't characterize an offer as accepted/declined unless the log or transactions show it.
4. **Pending trades:** treat as not happened until `transactions.json` shows them completed (Issue 3 treated a pending trade as completed; that was a one-off, so don't repeat it unless you say so).
5. **Unknowns go on the "needs your eyes" list**, not into the issue.
6. **Player status/injury claims** are checked against the chat log or flagged. Claude doesn't assert injuries from memory.

## 6. Issue structure (maps 1:1 to `issue-NN.json`)

Section order on the page: Desk, Standings, Wire, Post-Game, Drama, Trade Machine, Pre-Game, Bottom Line, Poll.

| Section | JSON key | Computed by build? | Claude writes |
|---|---|---|---|
| From the Desk | (in `issues.json`: `title`, `dek`, `banner`, `ticker[]`) | no | headline, 1–2 sentence dek, banner, 4 ticker lines |
| Hero & Zero / final-score banner | — | yes | nothing (auto from scores) |
| Standings, bankroll | `bank.notes` | yes (balances, change) | one short note per manager |
| Quote of the Week | `quote {text, by, desk}` | no | verbatim quote, context, desk line |
| Wire: trades | `wire.trades[]` | assets yes | `ai/bi` (immediate impact), `ah/bh` (horizon), `ga/gb` grades, `desk` |
| Wire: waivers | `wire.waivers[]`, `wire.desk{mgr}` | claims yes | `flag`, `note`, one desk aside per manager with claims |
| Post-Game | `post[]` | scores, records, bench, MVP yes | `tag`, `aged[3]`, `means[3]`, `key[3]`, grades `ga/gb`, `desk` |
| Drama of the Week | `drama[]` (4) | no | `h`, `heat` (0–100), `p`, `desk`. Heat above 100 pulses on the site. |
| Hits | `hits[]` | no | 6 verbatim `[quote, username]` pairs |
| Trade Machine | `trades.items[]`, `trades.note` | no | hypothetical trades (a/as, b/bs, ay, by, desk) |
| Pre-Game | `pre[]` (5 matchups) | records yes | `ma/mb`, `la/lb`, `edge`, `desk`; projections per decision 1.2 |
| Match of the Week | `motw`, `prev_motw` | stats yes | `ma/mb/la/lb/edge/desk/stakes/verdict`; recap previous MOTW |
| Bottom Line | `bottom.paras[]` | no | 3 short paragraphs ending on the poll CTA |
| Bold Predictions | `bold[]` (4) | no | `[prediction, reasoning]`; these get graded next issue |
| Poll | `poll {id, q, opts[4], desk}` | no | question, 4 options, desk line |
| Poll recap | `prev_poll {issue, q, opts, result, note}` (**new, build support needed**) | no | last issue's question, the winning option and vote split taken from the chat log, one line of reaction |

Lengths: Drama paragraphs 3–5 sentences; desk asides 1–2 sentences; Bottom Line 3 paragraphs. **[CONFIRM]**

## 7. Grading and awards

- Letter scale: A+, A, A-, B+, B, B-, C+, C, C-, D+, D, D-, F (matches the grade images in `assets/`).
- Trade grades are given per side, using immediate impact (this season) and dynasty horizon (2027–28).
- Hero = best manager of the week (highest score relative to optimal, as the build computes it). Zero = lowest score. **[CONFIRM exact award criteria: Issue 2 used "% of optimal" and lowest score]**
- Bold predictions: every one from last issue gets a Hit / Miss / Pending line in this issue's Bottom Line. **[PROPOSED]**

## 8. History ledger (seed; Claude appends each week)

- **Issue 1 (post-draft, Sep 2026):** 23-round startup draft done. Power rankings Top/Bottom 5. Darkspaces already down to $399 ($101 Ferguson claim). Typo in the masthead ("Dysnatree"), fixed from Issue 2.
- **Issue 2 (Wk 1 post / Wk 2 pre):** C33DeezNutzz 195.82 and Zygon 195.7 Hero. StealingGas 83.32 Zero, "worst manager." Darkspaces put Drake Maye on the block and won anyway. Quote: "some call it an overreaction. some call it genius."
- **Issue 3 (Wk 2 post / Wk 3 pre):** Zygon 172.96, best manager. StealingGas 77.18 Zero, announced the tank, spent $99–100 FAAB anyway. Darkspaces–Snipe58 trades (Deebo Samuel for a 2027 2nd; Ferguson for Loveland). London trade pending.
- **Issue 4 (Wk 3 post / Wk 4 pre), "Tank You for Your Service":** London trade cleared (StealingGas gets London, Taylen Green, 2027 1st; Hades9mm gets Johnston, Ward, Henderson, 2027 3rd). Stafford to Snipe58 for two future 2nds and $100 FAAB. StealingGas 152.42 and a win by 83 over Darkspaces (69.16) while "tanking." Commish went linear/MAXPF rookie draft and vetoes on. Achane block, Emmett/Corum block (Zygon). Match of the Week: Zygon vs Hades9mm (both 3-0).

## 9. Open bits carried forward (Claude updates weekly)

- Issue 4's MAXPF wording was corrected (7 edits in `issue-04.json`). Commit the patched file; the Action rebuild updates the issue page. If the commish's original announcement used "starters + bench" language, mention the clarification in Issue 5.

- Bold predictions from Issue 4 (grade in Issue 5): Achane moves before Week 5; StealingGas bottom-2 in MAXPF; Zygon top-2 through Week 6; Painty69 stays quiet in chat.
- Issue 4 poll (carry into Issue 5 as `prev_poll`): "Which 0-3 team is most likely to still be in the bottom three at the trade deadline?" Options: StealingGas (the tank is already capitalized); Painty69 (the crime family stays quiet); Sarge71 (elite RBs, no supporting cast); None (one of them spikes and climbs). Result: **[FILL from the Issue 5 chat log]**. The site's poll box doesn't collect votes (`endpoint` is empty); voting happens on Sleeper, so results come from the chat log.
- Achane trade block still open at last report.
- Trade Machine closes after Week 12.

## 10. Weekly checklist for Claude

1. Read this file, then the new chat log, then `data/` for the week. Confirm `weeks_with_scores` includes the week being covered.
2. Run the sanity checks: Sleeper pull printed no MAXPF mismatch; every manager named in the JSON exists in `managers.json`; every trade in `wire.trades` exists in `transactions.json`.
3. Draft the JSON in the schema above. No placeholder text.
4. Verify every quote against the log. Cut anything unverifiable. Pull the previous poll's result from the log into `prev_poll`.
5. Return the "needs your eyes" list, then update sections 8 and 9.

---

## 11. Resources and restart procedure

**Where things live**
- Live site: https://dynastreechronicles.github.io/Dynastree-Chronicles/ (GitHub Pages, so every file in the repo that ships with the site is also fetchable at that base URL, e.g. `.../data/standings.json`, `.../data/weeks/week-05.json`, `.../data/transactions.json`, `.../data/managers.json`, `.../data/issues.json`, `.../data/issues/issue-04.json`).
- Repo: **[FILL: github.com/<owner>/Dynastree-Chronicles URL]**. Commit this file as `MASTER.md` and `issue-template.json` in the repo root so the repo is the full backup.
- Code: `scripts/sleeper_pull.py` (Sleeper to `data/`), `scripts/build_site.py` (data + issue JSON to HTML). Workflow: `.github/workflows/update-data.yml`.

**What Claude needs each week**
1. This file.
2. The chat log.
3. Current `data/` for the week. Either say "the Action has run" and give the Pages URL, or upload the zip.
4. The previous issue's JSON (for `prev_motw`, bold predictions to grade, the previous poll question to recap, and continuity). Fetchable at `.../data/issues/issue-NN.json`.

**What Claude does NOT need:** anything in `assets/` (badges, grades, avatars, crest). The build references them by path. Only needed if you ask for new art or layout changes.

**Starting over in a fresh chat**
1. Upload `MASTER.md` and the latest chat log.
2. Either upload the repo zip once, or paste the Pages base URL so Claude can fetch `data/` files.
3. Claude then rebuilds context from: section 2 (rules), section 6 (schema), `issue-template.json` (exact JSON shape), and section 8 (history).
4. If the zip is not provided and the Pages files can't be reached, Claude can still write the prose but flags every number as unverified.

**Limits to know about**
- Claude's sandbox has no internet. It can read files you upload, or fetch pages from URLs you give it, but it can't `git pull` or push. You commit the result.
- Fetching `data/` from Pages shows only what the Action last committed. If the Action hasn't run since the games ended, the data is stale. Run it manually from the Actions tab first.

---

## 12. Links to ping and pull from

All Sleeper endpoints below are public GET requests with no login. League ID: `1389008727859806208`. Season 2026. Commissioner account used by the script: `StealingGas`.

| What | URL | Used for |
|---|---|---|
| Current NFL week/state | `https://api.sleeper.app/v1/state/nfl` | Which week is live; what counts as final |
| League settings | `https://api.sleeper.app/v1/league/1389008727859806208` | Roster slots, FAAB budget, scoring |
| Managers | `https://api.sleeper.app/v1/league/1389008727859806208/users` | Usernames, team names, avatar IDs |
| Rosters | `https://api.sleeper.app/v1/league/1389008727859806208/rosters` | Records, PF/PA, FAAB used, and `settings.ppts` + `ppts_decimal` (Sleeper's Max PF / potential points) |
| Weekly matchups | `https://api.sleeper.app/v1/league/1389008727859806208/matchups/{week}` | Scores, starters, every player's points (bench included) |
| Transactions | `https://api.sleeper.app/v1/league/1389008727859806208/transactions/{week}` | Trades, waivers, FAAB bids |
| Player names | `https://api.sleeper.app/v1/players/nfl` | ID to name/position/team. Large file; pull once a day at most |
| Avatars | `https://sleepercdn.com/avatars/{avatar_id}` | Manager images |
| Projections (**unverified**) | `https://api.sleeper.com/projections/nfl/2026/{week}?season_type=regular` | Pre-game projections. Undocumented and unconfirmed; first job is a test pull from the Action, then map to our starters |

Site and repo:

| What | URL |
|---|---|
| Live site | `https://dynastreechronicles.github.io/Dynastree-Chronicles/` |
| Data files on the site | `.../data/standings.json`, `.../data/league.json`, `.../data/managers.json`, `.../data/transactions.json`, `.../data/issues.json`, `.../data/weeks/week-NN.json`, `.../data/issues/issue-NN.json` |
| Repo | **[FILL]** |
| Actions page (run the pull by hand) | **[FILL: repo URL]**`/actions/workflows/update-data.yml` |
| Raw files from the repo | **[FILL: repo URL]** converted to `raw.githubusercontent.com/<owner>/Dynastree-Chronicles/main/<path>` |

How Claude uses these: in a chat where I can fetch pages, I can open the site's data files if you paste the base URL in your message. I can't call the Sleeper API from inside the sandbox, so the GitHub Action does the Sleeper pull and I read what it committed.
