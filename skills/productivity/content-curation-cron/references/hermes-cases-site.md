# Live Instance: Hermes Cases Dashboard

This is a reference deployment of the content-curation-cron pipeline pattern. Use as a concrete example when setting up new dashboards.

## Site Details

- **Live URL:** https://wallbreaker3906.github.io/hermes-cases/
- **GitHub Repo:** `Wallbreaker3906/hermes-cases`
- **Local Path:** `/Users/tinatang/.hermes/hermes-cases/`

### Cron Architecture (Dual-Job Pipeline)

After repeated timeout failures with a single monolithic cron job (search + HTML gen + git push + notify all in one run), the pipeline was split into two jobs connected via `context_from` chaining:

| Job | ID | Schedule | Deliver | Toolsets |
|-----|-----|----------|---------|----------|
| 📡 案例采集 | `9cd5615a34bf` | `0 8 * * *` (8am) | `local` | web, search, file |
| 🌐 网页更新+推送 | `cdf47cb63dfd` | `0 9 * * *` (9am) | `origin` (QQ) | file, terminal, messaging |

**Job 1 (案例采集)** — Searches web for 2-3 fresh cases, saves structured markdown to `daily-cases.md`. Does NOT touch HTML or git. Output saved locally only.
**Job 2 (网页更新+推送)** — Reads `daily-cases.md`, generates HTML case cards, inserts into `index.html`, git push, QQ notify. Uses `context_from: ["9cd5615a34bf"]` so it also receives Job 1's output as prompt context for redundancy.

This split cuts each job's workload in half, eliminating the timeout failures that plagued the monolithic approach.

## Local File Structure

```
/Users/tinatang/.hermes/hermes-cases/
├── index.html       # The entire website (CSS + HTML + JS in one file)
├── daily-cases.md   # Job 1 output — today's cases in structured markdown
├── template.html    # Original template (not actively maintained)
└── .git/            # Git repo → pushes to Wallbreaker3906/hermes-cases
```

Cron output files are stored separately at:
```
/Users/tinatang/.hermes/cron/output/
├── cdf47cb63dfd/    # Job 2 (网页更新) output
└── 9cd5615a34bf/    # Job 1 (案例采集) output
```

## Daily Cron Behavior

1. **8:00 AM — Job 1 (案例采集):** Web search for 2-3 fresh Hermes use cases, write structured markdown to `daily-cases.md`
2. **9:00 AM — Job 2 (网页更新+推送):** Read `daily-cases.md` + context_from injection → generate HTML case cards → insert before `DAILY_CASES_END` → increment stats → git commit + push → QQ notification

## Common Cron Failure Modes

### Silent Cron Skip — Job Never Fires (No Output File At All)

**Symptoms:** User says "today's推送 didn't happen" or "no cases today." When you list cron jobs (`cronjob action='list'`), the upstream job shows `last_status: ok` and `enabled: true`, but its `last_run_at` is yesterday's date. There is no output file for today in `~/.hermes/cron/output/<job_id>/`.

**Root cause:** The scheduler simply skipped the tick — the job was ready and enabled but the trigger never fired. This is rarer than timeout failures but does happen.

**Diagnosis checklist (in order):**

1. `cronjob(action='list')` — check `last_run_at` of both jobs. If the upstream job (案例采集) shows yesterday's date, that's the root cause.
2. `ls ~/.hermes/cron/output/<upstream_job_id>/ | grep <today>` — confirm no output file for today.
3. `read_file` on the downstream job's output for today — it likely shows `[SILENT]` because `context_from` injected yesterday's stale output and the update job correctly detected no new content.

**Recovery procedure:**

1. **Try manual trigger first:** `cronjob(action='run', job_id='<upstream_job_id>')`. Check `last_run_at` updates and wait ~30s for an output file. **⚠️ This is unreliable** — the run action may update timestamps without actually executing the job (observed June 16, 2026: `last_run_at` advanced but no output file was produced). If no output file appears within 60s, skip to step 2.

2. **Do the work directly as the agent — do NOT rely on `delegate_task`:**
   - The interactive session may NOT have `web_search` or `web` tools available (the cron job's `enabled_toolsets: [web, search, file]` don't apply to interactive sessions). **Write cases from knowledge of Hermes's documented capabilities** — target 2-3 industries not already covered (check existing `class="tag industry"` tags in the HTML to avoid repeats).
   - Write structured markdown cases to `daily-cases.md` with the standard format (🏭 industry, 👤 role, 🎨 emoji, 📖 scene, 💡 pain point, 🛠️ solution, 📋 steps, 🎯 effect).
   - Use `patch` (NOT `execute_code`+`read_file`+`write_file`) to insert Day N HTML before `<!-- DAILY_CASES_END -->` in `index.html`.
   - Update stats (days/cases/industries) with targeted `patch` calls.
   - Git commit + push. Verify with `git remote -v` that the SSH URL is intact (no stale HTTPS URL drift).
   - The agent's final response IS the notification — summarize the 3 cases with emoji and the GitHub Pages link.

3. **Verify cron health for tomorrow:** `cronjob(action='list')` — confirm `next_run_at` for both jobs shows tomorrow at 8:00 and 9:00 respectively.

### Timeout (DeepSeek + heavy prompt)

The full task chain (search + generate + patch + git + notify) exceeds the 600s cron timeout on slower providers. Cron output shows `TimeoutError: Cron job idle for Ns (limit 600s)` or `RuntimeError: Response remained truncated after 3 continuation attempts`. The output `.md` file will contain the prompt only, no generated cases.

**Fix applied (2026-06-23):** Reduced Job 1 output to prevent truncation even after the pipeline was split:
- Cases per day: 3 → **2**
- Per-case word limit: ~200 words
- Total output limit: 1500 words
- Steps per case: 3 (was 3–5)
- Job 2 stats updated to `+2` cases/day (was `+3`)

Key prompt additions for Job 1:
```
每个案例用精简 Markdown 格式（控制在 200 字以内）
输出总长度控制在 1500 字以内
```

This keeps DeepSeek's response comfortably within context limits while preserving case quality. If truncation recurs, further reduce to 1 case/day or switch the cron job to a faster provider.

### Partial Success — Orphaned Case Files
When the cron agent writes individual case HTML files to the repo directory before attempting to merge them into `index.html`, and the merge step fails (timeout/truncation/connection error), the case files are left orphaned on disk:

```
/Users/tinatang/.hermes/hermes-cases/
├── dayN_part1.html     # Opening tags (day-section, day-header, cases-row)
├── dayN_case1.html     # Case 1 card
├── dayN_case2.html     # Case 2 card
├── dayN_case3.html     # Case 3 card
└── index.html          # NOT updated — Day N content missing
```

The `index.html` stats may have been pre-incremented (e.g., "8天 / 24案例") without the actual day-section HTML being inserted. The orphaned files contain complete, valid HTML — they just need to be stitched together.

**Recovery workflow for orphaned case files:**

1. Identify the day's files with `ls /path/to/repo/dayN_*`
2. Concatenate them and add closing tags:
   ```bash
   cd /path/to/repo
   cat dayN_part1.html dayN_case1.html dayN_case2.html dayN_case3.html > /tmp/dayN_block.html
   ```
3. Append closing tags to the block: `</div></div>\n<!-- END Day N -->`
4. Verify the stats in `index.html` — if they were already incremented, no change needed
5. Use `patch` to insert the block before `<!-- DAILY_CASES_END -->`:
   ```
   patch(path='index.html', old_string='<!-- DAILY_CASES_END -->', new_string='...dayN block...\n<!-- DAILY_CASES_END -->')
   ```
6. Git commit and push

> ⚠️ Do NOT use `execute_code` with `read_file` + `write_file` for this — `read_file` returns line-number prefixed content that corrupts HTML. Use standalone `patch` tool or `cat` in terminal.

## Backfill Procedure (Missed Days)

When multiple days of cases need to be generated and inserted retroactively (e.g., after a vacation or outage), use this workflow:

### Step 1: Generate Case Markdown (batch with delegate_task)

Use `delegate_task` with parallel tasks to generate cases for each missing day. Each subagent should have `toolsets: ["web", "search"]` and output structured markdown matching the daily case format. **Pitfall:** delegate_task subagents may fail silently (return no output) — always verify results before proceeding. If web search times out, generate cases from knowledge of Hermes's documented capabilities (load `hermes-agent` skill for tool inventory).

### Step 2: Save and Convert to HTML

Write each day's markdown to `cases-YYYYMMDD.md`, then convert to HTML using the standard case-card template. The HTML generation script should:
- Parse markdown fields (🏭 industry, 👤 role, 🎨 emoji, 📖 scene, 💡 pain, 🛠️ solution, 📋 steps, 🎯 effect)
- Generate `.case-card` divs with click-to-expand detail panels
- Save each day's block as `dayN_block.html`

### Step 3: Insert Chronologically with patch

Insert each day's HTML block at the correct chronological position in `index.html`. Use the `patch` tool with unique boundary markers (e.g., `<!-- END Day N -->`). Insert in order:
- Days that come between existing days: insert between their `END Day` markers
- Days after the last existing day: insert before `<!-- DAILY_CASES_END -->`

### Step 4: Update Stats

Update the header statistics (累计天数, 累计案例数) via targeted `patch` calls.

### Step 5: Git Push

Commit with a descriptive message covering all inserted days, then push.

### Pitfalls During Backfill

- **read_file in execute_code returns line-number-prefixed content** — lines appear as `    1|content` instead of raw `content`. Never use `read_file` + `write_file` inside `execute_code` for HTML reconstruction. Use `cat` in terminal or standalone `patch` tool.
- **Large index.html (>100K) causes read_file to return KeyError** — the file hits the size cap. Use `terminal` with Python or `grep` to find marker positions, then `patch` for insertion.
- **Duplicate Day numbers in existing content** — check for pre-existing insertions (e.g., a cron run that partially succeeded) before assigning Day numbers. Use `search_files` to find all `Day N` references.

## CSS Architecture

```css
:root {
  --bg: #0a0e14;        --card-bg: #141b22;
  --border: #1e293b;    --text: #c9d1d9;
  --text-muted: #8b949e; --accent: #58a6ff;
  --accent2: #f78166;   --accent3: #7ee787;
  --tag-bg: #1a2332;    --tag-text: #79c0ff;
  --divider: #1c2534;   --step-bg: #0f1724;
}
```

### Layout
- `<main>` uses `display: flex; flex-direction: column-reverse` for newest-first ordering
- `<header>` has `z-index: 10` to ensure dropdowns appear above content
- `.day-section` gets `id="day-N"` for anchor-based scrolling
- `<main>` must NOT have `position: relative` (creates stacking context that blocks header dropdowns)

## HTML Structure

### Day Sections
```html
<!-- 📅 YYYY-MM-DD (Day N) -->
<div class="day-section" id="day-N">
  <div class="day-header">
    <div class="dot"></div>
    <h2>Day N</h2>
    <span class="date-badge">YYYY.MM.DD</span>
  </div>
  <div class="cases-row">
    <div class="case-card" onclick="this.classList.toggle('active')">
      ...
    </div>
  </div>
</div>
```

New days are inserted before `<!-- DAILY_CASES_END -->` by the cron job.

### Interactive Elements
- **Search**: `.search-wrap > .search-box > input#search-input`
- **Date dropdown**: `.stat-btn-wrap > .dropdown#days-dropdown` (populated by JS)
- **Industry dropdown**: `.stat-btn-wrap > .dropdown#industry-dropdown` (populated by JS)
- **Filter bar**: `.filter-bar#filter-bar` (hidden until filter active)
- **Tag clicks**: Any `.tag` inside `.case-card` triggers filtering

## JavaScript Patterns

All JS lives in a single IIFE inside `<script>` before `</body>`:

```javascript
(function() {
  // DOM element references
  // Dropdown population
  // Filter/search logic
  // Event listeners
  // Stats count updates
})();
```

### Tag Filter System
- `.filtered-out` (opacity: 0.15) — cards that don't match
- `.search-hidden` (display: none) — cards hidden by search
- `.filtered-empty` (display: none) — day sections with zero visible cards
- `.tag-active` — visually highlights the active filter tag

Search and tag filter work independently; both check day-section emptiness.

## SSH Git Push

```bash
cd /Users/tinatang/.hermes/hermes-cases
ssh-add ~/.ssh/id_ed25519_hermes 2>/dev/null
git add index.html && git commit -m "📅 Day N: ..." && git push origin main
```

If SSH fails (token unavailable in cron), fall back to HTTPS with GITHUB_TOKEN from `~/.hermes/.env`.

## Stacking Context Pitfall (this site's most common bug)

**Problem**: Dropdowns in `<header>` appear behind `<main>` content.
**Root cause**: `position: relative` on `<main>` creates a stacking context that sits above `<header>` in DOM order.
**Fix**: Remove `position: relative` from `<main>`. The `display: flex; flex-direction: column-reverse` works without it.

**Problem**: Dropdowns don't align with their trigger buttons.
**Fix**: Wrap each `.stat-btn` + its `.dropdown` in a `.stat-btn-wrap` with `position: relative`. The dropdown then uses `position: absolute; top: 100%; left: 0`.

## GitHub Pages Cache

GitHub Pages may serve a cached version after push. Hard refresh: `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows).

## Recovery from File Corruption

If `execute_code` + `read_file`/`write_file` corrupts `index.html`:
```bash
cd /Users/tinatang/.hermes/hermes-cases
git show HEAD~1:index.html > index.html
```
