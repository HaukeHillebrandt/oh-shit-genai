# "Oh shit" moments with GenAI

Every comment from the Hacker News thread *"Ask HN: What was your 'oh shit' moment with GenAI?"* distilled to a single line.

**1,104 comments** (472 top-level answers + 632 replies). A classifier pass keeps the **634 that are actual "oh shit" moments** and filters out 459 non-moments (questions, "can you share how?", thread meta, banter). Each kept moment is distilled to one line and sorted into **17 themes** (from "Resurrecting dead / undocumented hardware" to "The skeptics & the unimpressed").

👉 **[View the page](https://haukehillebrandt.github.io/oh-shit-genai/)**

Every moment is a bullet under its category, ending in a footnote: **hover** it to preview the full comment, **click** to jump to it. There's a live search box, a category jump-bar, and a "top-level only" toggle. The full threaded comments (all 1,093) sit below as the footnote targets.

## How it was built

1. `hn_thread_source.html` — the saved HN thread page.
2. Parsed with BeautifulSoup into `hn_comments.json` (author, indent depth, text).
3. Each comment distilled to one line → `summaries.json` (fan-out of 10 parallel agents).
4. Each comment assigned a theme — or flagged as a non-moment — by a second fan-out (10 Sonnet agents) → `categories_v2.json`. (`categories.json` is the earlier, looser Haiku pass, kept for reference.)
5. `build_oh_shit_html.py` renders the categorized bullets (drops excluded) + the full threaded comments + hover-preview footnotes into `index.html`.

Regenerate:

```bash
python3 build_oh_shit_html.py   # reads hn_comments.json + summaries.json, writes index.html
```

The thematic summary at the top is a human synthesis; the per-comment one-liners cover all 1,093 comments exhaustively.

## Second page: Did Fable 5 beat the field?

Same pipeline applied to the HN **"Claude Fable 5"** release thread (1,661 comments): every first-hand report of Fable 5 **outperforming** other LLMs (48), **mixed** verdicts (21), and — for balance — where it **underperformed** (114, dominated by safety-fallback complaints).

👉 **[View it](https://haukehillebrandt.github.io/oh-shit-genai/fable5/)** · sources & data in [`fable5/`](fable5/)
