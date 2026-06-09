# "Oh shit" moments with GenAI

Every comment from the Hacker News thread *"Ask HN: What was your 'oh shit' moment with GenAI?"* distilled to a single line.

**1,104 comments** (472 top-level answers + 632 replies) → 1,093 substantive ones, each distilled to one line and sorted into **18 themes** (from "Resurrecting dead / undocumented hardware" to "The skeptics & the unimpressed").

👉 **[View the page](https://haukehillebrandt.github.io/oh-shit-genai/)**

Every moment is a bullet under its category, ending in a footnote: **hover** it to preview the full comment, **click** to jump to it. There's a live search box, a category jump-bar, and a "top-level only" toggle. The full threaded comments sit below as the footnote targets.

## How it was built

1. `hn_thread_source.html` — the saved HN thread page.
2. Parsed with BeautifulSoup into `hn_comments.json` (author, indent depth, text).
3. Each comment distilled to one line → `summaries.json`, and assigned a theme → `categories.json` (both produced by a fan-out of 10 parallel agents over the comment chunks).
4. `build_oh_shit_html.py` renders the categorized bullets + threaded full comments + hover-preview footnotes into `index.html`.

Regenerate:

```bash
python3 build_oh_shit_html.py   # reads hn_comments.json + summaries.json, writes index.html
```

The thematic summary at the top is a human synthesis; the per-comment one-liners cover all 1,093 comments exhaustively.
