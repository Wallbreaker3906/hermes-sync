# Interactive Dashboard Patterns

JavaScript/HTML/CSS patterns for adding interactivity to content curation dashboards. These are the building blocks; apply them with the `patch` tool (never `execute_code` + `read_file`/`write_file`).

## Safe Editing (CRITICAL)

**NEVER use `read_file` + `write_file` in `execute_code` to edit HTML files.** `read_file` returns content with line-number prefixes (`  123|actual content`). Writing this back embeds the prefixes into the file, corrupting it. Always use the standalone `patch` tool for targeted edits.

**Recovery if corrupted:**
```bash
cd /path/to/repo && git show HEAD~1:filename > filename
```

## Pattern: Dropdown Menu (Date Picker / Industry Selector)

### HTML Structure
Wrap each trigger + dropdown in a `position: relative` container:

```html
<span class="stat-btn-wrap">
  <span class="stat-btn" id="trigger-btn">📅 点击 <span class="arrow-down">▾</span></span>
  <div class="dropdown" id="the-dropdown"></div>
</span>
```

### CSS

```css
.stat-btn-wrap { position: relative; display: inline-flex; }
.stat-btn { cursor: pointer; user-select: none; }

.dropdown {
  display: none;
  position: absolute; top: 100%; left: 0;  /* left:0 aligns with button, not page center */
  z-index: 100;
  background: #1a2232; border: 1px solid var(--border);
  border-radius: 10px; padding: 0.5rem;
  min-width: 140px; max-height: 240px; overflow-y: auto;
  box-shadow: 0 8px 32px rgba(0,0,0,0.5);
}
.dropdown.show { display: block; }
```

### z-index Layering Pitfall

If the dropdown is hidden behind page content, check stacking contexts:

- Parent elements with `z-index` create stacking contexts. A child's `z-index` only works within its parent's context.
- If `header { z-index: 1 }` and `main { z-index: 1 }`, and `main` comes after `header` in DOM, `main` will overlay `header`'s children — even ones with `z-index: 999`.
- **Fix:** raise the parent's `z-index` (e.g., `header { z-index: 10 }`) and remove unnecessary `z-index` from competing siblings.
- Additionally: `position: relative` on `<main>` creates an independent stacking context. If dropdowns are in `<header>`, remove `position: relative` from `<main>`.

### Dropdown Positioning
- **Symptom:** Dropdown appears centered on page instead of below its button → use `left: 0`, not `left: 50%`.
- **Symptom:** Dropdown misaligned horizontally → ensure dropdown is child of a `position: relative` wrapper (not `<header>` directly).

### JavaScript (Populate + Toggle)

```javascript
// Populate dropdown from DOM data
var dropdown = document.getElementById('the-dropdown');
document.querySelectorAll('.day-section').forEach(function(section) {
  var item = document.createElement('button');
  item.className = 'dropdown-item';
  item.textContent = section.querySelector('h2').textContent;
  item.addEventListener('click', function(e) {
    e.stopPropagation();
    section.scrollIntoView({ behavior: 'smooth', block: 'start' });
    dropdown.classList.remove('show');
  });
  dropdown.appendChild(item);
});

// Toggle
document.getElementById('trigger-btn').addEventListener('click', function(e) {
  e.stopPropagation();
  dropdown.classList.toggle('show');
});

// Close on outside click
document.addEventListener('click', function() {
  dropdown.classList.remove('show');
});
```

## Pattern: Tag-Based Filtering

### HTML: Each card carries tags

```html
<div class="case-card">
  <div class="tags">
    <span class="tag industry">教育</span>
    <span class="tag role">教师</span>
    <span class="tag">多媒体备课</span>
  </div>
  ...
</div>
```

### CSS: Filter states

```css
.case-card.filtered-out { opacity: 0.15; pointer-events: none; }
.day-section.filtered-empty { display: none; }

/* Tags become clickable */
.case-card .tag { cursor: pointer; transition: background 0.2s; }
.case-card .tag:hover { background: rgba(88,166,255,0.2); }
.case-card .tag.tag-active { background: rgba(88,166,255,0.25); color: #fff; }

/* Filter bar */
.filter-bar {
  display: none; align-items: center; gap: 0.6rem;
  padding: 0.6rem 1rem; border-radius: 10px;
  background: var(--card-bg); border: 1px solid var(--border);
}
.filter-bar.show { display: flex; }
```

### JavaScript: Filter Logic

```javascript
var allCards = document.querySelectorAll('.case-card');
var daySections = document.querySelectorAll('.day-section');

function applyFilter(tag) {
  document.getElementById('filter-bar').classList.add('show');
  document.getElementById('active-filter-tag').textContent = tag;

  allCards.forEach(function(card) {
    var hasTag = false;
    card.querySelectorAll('.tag').forEach(function(t) {
      t.classList.remove('tag-active');
      if (t.textContent.trim() === tag) { hasTag = true; t.classList.add('tag-active'); }
    });
    card.classList.toggle('filtered-out', !hasTag);
  });

  // Hide empty day sections
  daySections.forEach(function(section) {
    var visible = section.querySelectorAll('.case-card:not(.filtered-out)');
    section.classList.toggle('filtered-empty', visible.length === 0);
  });
}

function clearFilter() {
  document.getElementById('filter-bar').classList.remove('show');
  allCards.forEach(function(card) {
    card.classList.remove('filtered-out');
    card.querySelectorAll('.tag').forEach(function(t) { t.classList.remove('tag-active'); });
  });
  daySections.forEach(function(s) { s.classList.remove('filtered-empty'); });
}

// Click any tag to filter; click again to clear
allCards.forEach(function(card) {
  card.querySelectorAll('.tag').forEach(function(tag) {
    tag.addEventListener('click', function(e) {
      e.stopPropagation();
      if (activeFilter === this.textContent.trim()) { clearFilter(); }
      else { applyFilter(this.textContent.trim()); }
    });
  });
});
```

## Pattern: Real-Time Search

```html
<div class="search-wrap">
  <div class="search-box">
    <span class="search-icon">🔍</span>
    <input type="text" id="search-input" placeholder="搜索…">
    <button class="search-clear" id="search-clear">✕</button>
    <span class="search-count" id="search-count"></span>
  </div>
</div>
```

```css
.search-wrap { max-width: 600px; margin: 0 auto 1.5rem; }
.search-box { display: flex; align-items: center; gap: 0.5rem; background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; padding: 0.6rem 1rem; }
.search-box:focus-within { border-color: var(--accent); box-shadow: 0 0 0 3px rgba(88,166,255,0.12); }
.search-icon { opacity: 0.5; }
#search-input { flex: 1; background: none; border: none; color: var(--text); font-size: 0.95rem; outline: none; }
.search-clear { display: none; background: none; border: none; color: var(--text-muted); cursor: pointer; font-size: 1.1rem; }
.search-clear.visible { display: inline; }
.search-count { color: var(--text-muted); font-size: 0.8rem; white-space: nowrap; }
.case-card.search-hidden { display: none; }
```

Search matches against `textContent` of each card. Fire on every `input` event. Coordinate with tag filter: cards hidden by search get `.search-hidden`; day sections with zero `.case-card:not(.search-hidden)` get `.filtered-empty`.

## Pattern: CSS-Only Newest-First Display

```css
main {
  display: flex;
  flex-direction: column-reverse;
}
```

Reverses visual order of all direct children inside `<main>`. Cron jobs keep appending chronologically (before `DAILY_CASES_END`); this CSS rule shows newest content at top. No JS needed.

**Caution:** `flex-direction: column-reverse` also reverses tab order and scroll position. For accessibility, use with care.

## Quick-Reference Pitfall Table

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| `read_file` + `write_file` in execute_code | Entire file has `  123|` prefixes embedded | `git show HEAD~1:file > file` then redo with `patch` |
| Dropdown outside `position:relative` container | Dropdown appears in wrong position | Wrap trigger+dropdown in `position:relative` span |
| Competing `z-index` on parent siblings | Dropdown hidden behind content | Raise parent z-index, remove from siblings |
| `position: relative` on `<main>` | Dropdown in `<header>` hidden behind `<main>` | Remove `position: relative` from `<main>` |
| `left: 50%` on dropdown | Dropdown centered on page, not button | Use `left: 0` to align with button |
| Browser cache | Old version showing after push | Hard refresh: `Cmd+Shift+R` |
