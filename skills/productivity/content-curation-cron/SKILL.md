---
name: content-curation-cron
description: Set up daily automated content curation pipelines that publish to a continuously-updating html dashboard and notify users via messaging platforms.
tags: [cron, content, daily, dashboard, curation, html]
---

# Content Curation Cron Pipeline

Use when the user wants recurring, accumulated content delivered as a single, continuously-updating webpage (not separate per-day pages) with a daily summary notification via messaging (QQ / Telegram / Discord / etc.).

## Pattern Overview

```
┌──────────────┐    daily 9:00     ┌─────────────────────┐
│  Cron Job    │ ───────────────→  │  1. Web search      │
│  (@daily)    │                   │  2. Format cases     │
└──────────────┘                   │  3. Update HTML      │
                                   │  4. Notify user      │
                                   └─────────┬───────────┘
                                             │
                                             ▼
                                  ┌─────────────────────┐
                                  │  index.html          │
                                  │  (accumulates daily) │
                                  └─────────────────────┘
```

## Step 1: Create the HTML Template

> 📄 **Full working template:** `templates/dashboard-template.html` — includes all CSS, JavaScript-free click toggle, step-block styling, and responsive grid. Contains `{PLACEHOLDER}` markers (`{PAGE_TITLE}`, `{HEADER_TITLE}`, `{HEADER_SUBTITLE}`, `{FIRST_DAY_DATE}`, `{FOOTER_TEXT}`) for easy find-and-replace. Use as the base for new dashboards.

### Step 1: Create the HTML Template

> 📄 **Template available:** `templates/dashboard-template.html` — a complete starter HTML with dark-theme CSS, case-card layout, and `{PLACEHOLDER}` markers for easy find-and-replace.

Create a standalone HTML file with embedded CSS. The file must include two marker comments so the cron job knows exactly where to insert new daily content:

```html
<!-- DAILY_CASES_START -->

<!-- ... existing day sections go here ... -->

<!-- DAILY_CASES_END -->
```

### Design Guidelines
- **Dark theme** (background: `#0a0e14`, card: `#141b22`, accent: `#58a6ff`) — reads well on all screens and feels tech-y without being gaudy.
- **Card layout** with CSS Grid (`grid-template-columns: repeat(auto-fit, minmax(280px, 1fr))`) so cases flow naturally on mobile and desktop.
- **Stats bar** in the header showing cumulative days / cases / industries — increment these on every update.
- **Day sections** use a consistent structure:

```html
<div class="day-section">
  <div class="day-header">
    <h2>Day N</h2>
    <span class="date-badge">YYYY.MM.DD</span>
  </div>
  <div class="cases-row">
    <!-- each case-card here -->
  </div>
</div>
<!-- END Day N -->
```

### Content Structure Per Case (with click-to-expand)

**Prefer the click-to-expand pattern.** Users consistently ask for more detail than a card can show at rest — the expandable panel solves this without cluttering the initial view. The card shows a teaser; clicking reveals step-by-step instructions with actual natural-language commands they can copy.

Each case card has two layers:

**Layer 1: `.case-card-inner`** — always visible. Emoji, title, tags, scenario blurb, and a "▶ 点击展开详细操作流程" hint.

**Layer 2: `.case-detail`** — hidden by default (`max-height: 0; overflow: hidden`), expands on click via `onclick="this.classList.toggle('active')"`. Contains numbered `.step-block` elements, each with a `.step-header` (title) and `.step-body` (explanation + a concrete natural-language command in `<code>` tags).

```html
<div class="case-card" onclick="this.classList.toggle('active')">
  <div class="case-card-inner">
    <div class="emoji">📘</div>
    <div class="case-title">标题</div>
    <div class="case-subtitle">一句话概括</div>
    <div class="tags">
      <span class="tag industry">行业</span>
      <span class="tag role">角色</span>
      <span class="tag">任务类型</span>
    </div>
    <div class="case-section">
      <h4>📖 场景</h4>
      <p>2-3句场景描述</p>
    </div>
    <div class="click-hint">
      <span class="arrow">▶</span> 点击展开详细操作流程
    </div>
  </div>
  <div class="case-detail">
    <div class="case-detail-inner">
      <h3>🔍 详细操作流程</h3>
      <div class="step-block">
        <div class="step-header">
          <span class="step-number">1</span> 步骤标题
        </div>
        <div class="step-body">
          在终端输入：<code>具体的自然语言指令示例</code>。说明 Hermes 将如何执行。
        </div>
      </div>
      <!-- repeat step-block for each step (4-5 total) -->
      <div class="highlight-box">
        💡 <strong>效果：</strong>实际收益总结
      </div>
    </div>
  </div>
</div>
```

**CSS requirements for the expand animation:**
```css
.case-detail { max-height: 0; overflow: hidden; transition: max-height 0.45s ease, opacity 0.25s ease; opacity: 0; }
.case-card.active .case-detail { max-height: 3000px; opacity: 1; }
.case-card.active .click-hint .arrow { transform: rotate(180deg); }
```

> 📄 **Full working template:** `templates/dashboard-template.html` — includes all CSS, JavaScript-free click toggle, step-block styling, and responsive grid. Use as the base for new dashboards.

## Step 2: Create the Cron Job

### Schedule
`0 9 * * *` (daily at 9 AM) — gives the user a morning read. Adjust to user's timezone.

### Job Prompt (key requirements)

The prompt must be self-contained and instruct the agent to:

1. **Search for diverse content** — web search for fresh cases. The prompt should enforce variety: different from previous days (which the agent can see by reading the existing HTML), different industries, different roles, different task types.
2. **Read the existing HTML** — find the insertion point near `<!-- DAILY_CASES_START -->`.
3. **Insert new day section** — insert the new day block at the right position:
   - **Chronological (append after last day section, before `DAILY_CASES_END`):** For dashboards where readers scroll down through history (e.g., GitHub Pages). Use `patch` with `old_string='<!-- DAILY_CASES_END -->'` and prepend the new block before the marker. This is the safer default — it won't reorder existing content.
   - **CSS reverse-display (RECOMMENDED for "newest on top"):** Keep the chronological insertion order (append before `DAILY_CASES_END`) but make the `<main>` container display newest first with a single CSS rule: `main { display: flex; flex-direction: column-reverse; }`. This is simpler and less error-prone than the reverse-chronological prepend below — no block-shifting, no reordering bugs, and future cron runs continue appending at the bottom as normal. The user sees Day N, Day N-1, Day N-2 from top to bottom automatically.
   - **Reverse-chronological (prepend after `DAILY_CASES_START`):** For dashboards where newest content should appear first without scrolling and CSS reversal isn't suitable. Use `patch` with `old_string='<!-- DAILY_CASES_START -->'` and append the new block after the marker. Be careful: this shifts the relative position of all existing day blocks and is more fragile across cron runs.
4. **Increment stats** — update the day count and total case count in the header.
5. **Write back** — overwrite the file with updated content.
6. **Deliver summary** — the final response (set for `deliver: origin`) should be a short summary of the 2-3 new cases, formatted for the target chat platform.

### Delivery
Set `deliver: origin` so the summary automatically goes to the same chat where the cron was created. The agent's final response IS the delivered message — keep it short and scannable.

## Step 3: First Run

Do an immediate first run manually (via `delegate_task` or direct work) so the user sees an instant result. An empty page is discouraging. The first batch can be a bit larger (3 cases) to give the page substance.

## Step 4: Optional — Deploy to GitHub Pages

If the user wants to share the dashboard with friends (rather than keeping it local), GitHub Pages is the best free option:

1. **Check GitHub access** — verify `gh` CLI or git with a token. If the GITHUB_TOKEN is a placeholder (`REPLACE_ME`), guide the user through creating one at https://github.com/settings/tokens (classic token with `repo` scope, no expiration).
2. **Initialize repo** in the dashboard directory, commit the HTML, create a GitHub repo via REST API (if gh CLI unavailable), push.
3. **Enable Pages** — set the repo's Pages source to `main` branch, root directory via the GitHub API. The URL will be `https://<username>.github.io/<repo-name>/`.
4. **Add auto-push to the cron job** — extend the daily cron prompt to also `git add`, `git commit`, and `git push` after updating the HTML.

   **HTTPS method (token-based):** Use `git remote set-url origin https://<token>@github.com/<user>/<repo>.git` so push doesn't prompt for credentials.

   **SSH method (key-based):** If the user has a dedicated deploy key set up, use `GIT_SSH_COMMAND="ssh -i ~/.ssh/id_ed25519_hermes -o StrictHostKeyChecking=no"` as a prefix to git commands. This avoids token management and works with GitHub Deploy Keys (repo-scoped, no 2FA issues). Example push command:
   ```bash
   cd /path/to/repo && \
   GIT_SSH_COMMAND="ssh -i ~/.ssh/id_ed25519_hermes -o StrictHostKeyChecking=no" \
   git add index.html && \
   GIT_SSH_COMMAND="ssh -i ~/.ssh/id_ed25519_hermes -o StrictHostKeyChecking=no" \
   git commit -m "📅 Day N: ..." && \
   GIT_SSH_COMMAND="ssh -i ~/.ssh/id_ed25519_hermes -o StrictHostKeyChecking=no" \
   git push origin main
   ```

If GitHub.com downloads are timing out (common behind certain networks), try ghproxy.com mirrors or use the REST API directly (which often works even when large binary downloads don't).

## Supplemental References

- **`references/interactive-patterns.md`** — Dropdowns, tag filtering, search, CSS newest-first, z-index layering pitfalls. Apply these patterns to any curation dashboard.
- **`references/hermes-cases-site.md`** — Live deployment reference: the hermes-cases dashboard at wallbreaker3906.github.io/hermes-cases. Paths, cron job ID, CSS architecture, SSH push workflow, and stacking-context pitfalls specific to this instance.
- **`references/qq-notification-template.md`** — QQ daily notification format.

## Pitfalls

- **SSH keys unavailable in cron environments.** Cron jobs run without the user's SSH agent, so `git push` with an SSH remote (`git@github.com:...`) will fail with "Permission denied (publickey)". Two fixes:
  1. **HTTPS + token (simplest):** Before pushing, set the remote to HTTPS with the token inline: `git remote set-url origin https://<username>:<GITHUB_TOKEN>@github.com/<user>/<repo>.git`. After push, restore the SSH remote: `git remote set-url origin git@github.com:<user>/<repo>.git`. The token should be sourced from `~/.hermes/.env`.
  2. **Dedicated deploy key:** Set up a GitHub Deploy Key with write access and use `GIT_SSH_COMMAND="ssh -i ~/.ssh/id_ed25519_hermes -o StrictHostKeyChecking=no"` prefix on all git commands.

- **CRITICAL: HTTPS remote URL drift breaks future pushes.** If the HTTPS+token method above sets the remote to HTTPS but the restore step is omitted or fails, the remote stays as HTTPS indefinitely. All subsequent pushes (from other sessions, manual git push, or future cron runs) will fail because the HTTPS URL no longer has a valid token in it. Symptoms: `SSL connection timeout` or `Authentication failed`. **Always verify after push:** check `git remote -v` shows the SSH URL (`git@github.com:...`), not HTTPS. If the SSH key is available in-session, prefer the `GIT_SSH_COMMAND` approach (option 2 above) which never mutates the remote URL and avoids this entire class of bug.
- **SSH key not loaded in interactive sessions.** Even outside cron, the SSH agent may not have the deploy key loaded. Before any `git push`, verify with `ssh-add -l` and load the key if missing: `ssh-add ~/.ssh/id_ed25519_hermes`. Symptom: `git@github.com: Permission denied (publickey)` even though the key file exists at `~/.ssh/`. This is distinct from the cron SSH issue — in cron the agent isn't running at all; in interactive sessions the agent exists but the key isn't cached.
- **Cron job needs `messaging` toolset for `send_message`.** Setting `deliver: origin` only handles auto-delivery of the final response. If the cron prompt explicitly calls `send_message` to send a notification, the job must have the `messaging` toolset in `enabled_toolsets` — otherwise the tool won't be available and the notification step silently fails. Similarly, ensure `file` and `terminal` are enabled for HTML patching and git operations. A typical cron job `enabled_toolsets` for a curation pipeline: `["web", "terminal", "file", "messaging"]`.

- **Heavy cron tasks time out on slower providers.** When the prompt combines web search, HTML generation, patching, git push, and notification in a single cron run with a slower model (e.g., DeepSeek), the task can exceed the 600s cron timeout. Symptoms in the cron output: `TimeoutError: Cron job idle for Ns (limit 600s)` or `RuntimeError: Response remained truncated after 3 continuation attempts`.

  **Recommended fix: Split into two jobs with `context_from` chaining.** This is the most reliable mitigation:

  ```
  Job 1 (8:00 AM): Case collection only
    - Web search → structured markdown → save to file
    - deliver: local (no notification yet)
    - enabled_toolsets: ["web", "search", "file"]

  Job 2 (9:00 AM): HTML update + push + notify
    - Read markdown file → generate HTML → patch index.html → git push → QQ notify
    - context_from: ["<Job 1 ID>"]  ← redundancy: content available both via file and context
    - deliver: origin
    - enabled_toolsets: ["file", "terminal", "messaging"]
  ```

  Key design decisions:
  - **Job 1 never touches HTML or git** — keeps response short, avoids truncation
  - **Job 2 never searches the web** — avoids the slowest part of the pipeline
  - **`context_from` provides redundancy** — even if the file write fails, Job 2 sees the content in context
  - **1-hour gap (8am→9am)** — gives Job 1 time to complete even if slightly slow
  - **Each job has minimal toolsets** — reduces token overhead and keeps prompts focused

  **If truncation persists even after the split (single Job 1 still too heavy):** reduce the prompt's output requirements. Trim from 3 cases to 2, add explicit per-case word limits (`控制在 200 字以内`), and set a total-output cap (`输出总长度控制在 1500 字以内`). Update Job 2's stats-increment from `+3` to `+2` cases per day to match. This is the lightest-weight fix and was sufficient for DeepSeek v4 after a 3→2 case reduction + length guardrails.

  Other mitigations (less reliable alone): (a) increase timeout if the scheduler supports it, (b) use a faster model/provider for the cron job.

- **Stale context_from data when upstream job fails.** `context_from` injects the most recent *completed* output of the upstream job. If Job 1 fails silently (e.g., web search returns empty), Job 2 receives the *last successful* Job 1 output — which could be yesterday's cases. Mitigations: (a) Job 2 should always check the intermediate file's modification time before trusting context_from content; (b) have Job 1 write a sentinel line (e.g., `# Generated: 2026-06-11`) that Job 2 can verify; (c) use the file as primary source and context_from only as a redundancy fallback.

- **Web search may return stale, irrelevant, or completely empty results.** DuckDuckGo HTML search (`html.duckduckgo.com/html/?q=...`) has been observed to return zero results on macOS even for broad queries — curl with `-L` and User-Agent headers didn't help. When this happens, do NOT loop retrying; instead, fall back to constructing realistic cases grounded in Hermes's documented capabilities. Load the `hermes-agent` skill via `skill_view(name='hermes-agent')` to see the full toolset (terminal, file, web, vision, image_gen, delegation, cronjob, skills, gateway, etc.) and build cases that use real features in plausible industry scenarios. Check existing case tags in the HTML to avoid industry repeats.
- **HTML injection errors.** The agent MUST locate the correct insertion point.
  - **If appending chronologically:** target `<!-- DAILY_CASES_END -->` and insert the new day block (including its closing `<!-- END Day N -->`) immediately before it. Use the `patch` tool (mode='replace') with `old_string='<!-- DAILY_CASES_END -->'`.
  - **If prepending reverse-chronologically:** target `<!-- DAILY_CASES_START -->` and insert after it. Use `patch` with `old_string='<!-- DAILY_CASES_START -->'`.
  - **PREFER the `patch` tool directly.** Do NOT use `execute_code` with `read_file` + `write_file` for HTML modifications. The `read_file` tool used inside `execute_code` returns content with line-number prefixes (e.g., `    1|<!DOCTYPE html>`), and `write_file` will write these prefixes into the file — corrupting the entire document with embedded line numbers. This bug renders the page as unstyled plain text because the browser can't parse `1|<style>` as a valid `<style>` tag. Always use the standalone `patch` tool for targeted edits to the HTML file.
- **Stats drift.** After 10+ days the agent might miscount. Instruct it to read the old stats from the HTML header `<span>` tags and increment.
- **Duplicate industries.** The prompt must remind the agent to check existing case tags (visible in the HTML) and avoid repeats. This is the most common failure mode.
- **The user's browser cache may show stale content.** The HTML is a local file regenerated by the cron job. The user should hard-refresh (Cmd+Shift+R) if they keep the page open overnight.

- **Non-programmer users expect interactive browsing, not just a static page.** When the user is not technical, offer to add lightweight JavaScript enhancements to the dashboard:
  - **Date jump dropdown:** Click the stats bar "累计 N 天" to pick a date and auto-scroll. Needs `id="day-N"` on each `.day-section` + a dropdown populated from the DOM.
  - **Industry/tag filtering:** Click "覆盖 N 个行业" to see all industry tags, or click any tag on a case card to filter globally. Uses `.filtered-out` (opacity 0.15) on non-matching cards and `.filtered-empty` (display:none) on day sections with no matches. A "清除筛选" button resets.
  - **Real-time search:** A search box between header and main that filters case cards as the user types. Wrap in `.search-wrap` with a `.search-box` containing an input, clear button, and result count. Use `.search-hidden { display: none; }` on non-matching cards. The `<script>` should listen for `input` events, match against `card.textContent.toLowerCase()`, and hide empty day sections. Add search clear button that resets input and re-focuses.
  - **CSS newest-on-top:** `main { display: flex; flex-direction: column-reverse; }` — the simplest way to show latest content first without reordering HTML on every cron run.
  - **Implementation method:** Apply each change individually with the `patch` tool — add `id` attributes to day-sections, insert CSS before `</style>`, replace stats HTML, insert filter-bar before `<main>`, and insert `<script>` before `</body>`. Do NOT use `execute_code` with `read_file` + `write_file` (see HTML injection errors pitfall above). The JavaScript should be wrapped in an IIFE to avoid global scope pollution and auto-populate date/industry dropdowns from the DOM.
  These features make the page feel like a real product, not a dumping ground for cron output, and dramatically improve the sharing experience when the user sends the GitHub Pages link to friends.
- **CRITICAL: CSS stacking context blocks dropdown overlays.** When adding dropdown menus that appear inside `<header>` and need to overlay `<main>` content, the `main` element MUST NOT have `position: relative` — it creates an independent stacking context, and since `<main>` comes after `<header>` in the DOM, `main`'s stacking context always paints on top regardless of z-index values. The header's dropdowns (even with `z-index: 999`) will be trapped behind `main`. Fix: remove `position: relative` from `main`. If `main` needs a stacking context for other reasons, give `header` a higher `z-index`. Symptom: user reports "下拉内容被遮挡" / dropdown content is hidden behind the main content area. Also ensure dropdowns are placed inside `position: relative` wrappers for correct horizontal alignment — orphaned `position: absolute` dropdowns (children of `<header>` directly rather than the stat button wrapper) will position relative to the wrong ancestor and appear in the page center rather than below the button.
- **Click-to-expand doesn't work.** If `.case-card` is missing `onclick="this.classList.toggle('active')"`, the detail panel never opens. The cron prompt must explicitly require this attribute on every card.
- **Empty step-body code examples.** Users want concrete commands they can copy — not just "use X to do Y". Every `.step-body` must include a real natural-language instruction wrapped in `<code>` tags, e.g. `<code>帮我搜索《红楼梦》核心人物关系，生成 Markdown 知识库</code>`.
- **GITHUB_TOKEN is a placeholder.** If the token is `REPLACE_ME` or similar, the user hasn't configured it yet. Guide them to https://github.com/settings/tokens to create a classic token with `repo` scope, then store it in `~/.hermes/.env`.

## Delivery Format

The daily QQ/chat notification should be concise:

```
📬 今日案例速递（2026.05.29）

1. 🏷️ 标题 — 一句话亮点
2. 🏷️ 标题 — 一句话亮点
3. 🏷️ 标题 — 一句话亮点

📄 完整网页已更新：/path/to/index.html
```

No markdown tables, no code blocks, no HTML. Just plain text that renders cleanly in a mobile chat bubble.

> 📄 **QQ-specific template:** `references/qq-notification-template.md` — preferred format with emoji-delimited lines, GitHub Pages link, and rules for ensuring the notification fires.
