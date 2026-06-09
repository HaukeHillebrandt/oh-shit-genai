# build_oh_shit_html.py
# Builds a self-contained, searchable HTML page from the parsed Hacker News thread
# "Ask HN: What was your 'oh shit' moment with GenAI?".
#   - hn_comments.json : all parsed comments (author, indent, text)
#   - summaries.json   : {idx: one-line distilled summary} for every usable comment
# Output: an exhaustive one-line index of all moments, each with a footnote that
# links to the full comment and shows a hover preview, plus the full threaded
# comments below as footnote targets. No external dependencies.

import json, html, re, datetime

comments = json.load(open('hn_comments.json'))
summaries = {int(k): v for k, v in json.load(open('summaries.json')).items()}
usable = [c for c in comments if len(c['text']) > 20]   # indexing matches summaries.json + card ids

URL_RE = re.compile(r'(https?://[^\s<>"\)]+)')

def linkify(text):
    esc = html.escape(text)
    return URL_RE.sub(lambda m: f'<a href="{m.group(1)}" target="_blank" rel="noopener">{m.group(1)}</a>', esc)

# ---- full comment cards (footnote targets) ----
def render_full(c, idx):
    ind = min(c['indent'], 7)
    user = html.escape(c['user']) if c['user'] else 'anon'
    paras = [p for p in c['text'].split('\n') if p.strip()]
    body = '\n'.join(f'<p>{linkify(p)}</p>' for p in paras)
    top = ' top' if c['indent'] == 0 else ''
    tag = '' if c['indent'] == 0 else ' <span class="reply">reply</span>'
    return f'''<div class="c lvl{ind}{top}" id="c{idx}">
  <div class="meta"><span class="fnum">{idx+1}.</span> <span class="u">{user}</span>{tag}</div>
  {body}
</div>'''

full_html = '\n'.join(render_full(c, i) for i, c in enumerate(usable))

# ---- exhaustive one-line index (with footnotes + hover preview) ----
def render_index_row(c, idx):
    summ = html.escape(summaries.get(idx, '(no summary)'))
    user = html.escape(c['user']) if c['user'] else 'anon'
    top = ' top' if c['indent'] == 0 else ''
    blob = html.escape((user + ' ' + summaries.get(idx, '') + ' ' + c['text']).lower())
    return (f'<li class="row{top}" data-blob="{blob}">'
            f'<span class="s">{summ}</span> '
            f'<a class="fn" href="#c{idx}" data-t="c{idx}">[{idx+1}]</a> '
            f'<span class="who">&mdash; {user}</span></li>')

index_html = '\n'.join(render_index_row(c, i) for i, c in enumerate(usable))

n_total = len(comments)
n_top = sum(1 for c in comments if c['indent'] == 0)
n_reply = n_total - n_top
today = datetime.date(2026, 6, 9).strftime('%-d %b %Y')

THEMES = [
    ("Resurrecting dead / undocumented hardware",
     "The single most common 'oh shit'. People handed an LLM a binary firmware, a hex dump, or a Ghidra disassembly and got back a working driver, parser, or exploit: a 90s Alesis synth, a camper van's CAN bus, a bricked iPad, an old Firestick rooted via a kernel zero-write primitive, a FujiFilm camera's transfer protocol, N64 cheat codes from a decomp, license-key generators for vintage test equipment, Rockbox on an M2 Mac, model-train wiring, a vintage amp."),
    ("Home & life repair with zero domain knowledge",
     "Non-coding wins: diagnosing a furnace mid-winter from attic videos, restarting 100-year-old steam heat, fixing a dishwasher the repairman couldn't, identifying a koi-pond pump by measuring it, silencing a faulty fire-alarm panel from a photo, reassembling a broken bath tap, matching wood stain from a sunlit photo, reviving plants/petunias, reverse-engineering a turntable PSU's schematic from two PCB photos."),
    ("Debugging the previously undebuggable",
     "Race conditions, cross-module state bugs that stumped multiple senior engineers, memory bugs in C, a stack-alignment bug found from objdump output, hardware faults inferred from driver code, multi-second Wi-Fi stalls fixed by disabling power management after years of pain, production bugs found by reading live cloud logs. 'A week of debugging took 10 minutes.'"),
    ("Real software, shipped, fast",
     "Whole apps to the App Store in 2 weeks with no Swift knowledge; an overnight Django rewrite of a NextJS micro-service mess; an OS with TCP/IP and a GUI that runs Doom in a week; SDL 1.2 reimplemented in Rust; a from-scratch C++ compiler; dashboards done in hours; 200 failing integration tests fixed in a week via an automated loop."),
    ("Non-technical people building things",
     "A brother who'd never touched code shipping a complex app via Codex; a friend with 130+ active users on an app he doesn't understand; a lawyer's redline tool, a sales guy's golf-trip site, 3D-printing jigs, a full mobile game — friends showing childlike excitement over micro-projects."),
    ("Science, math & research",
     "ChatGPT finding a counterexample to a 2-year conjecture; o3 solving a 6-hour RL derivation in 15 minutes; proving a prize-winning paper's theorem in 5 minutes; fixing dimension-dependent sign bugs in quantum field theory code; deriving a novel optimizer in Einstein notation that ran first try; a quarter-million-dollar-equivalent electrolyzer digital twin."),
    ("The early-model awe (GPT-2 → DALL-E → ChatGPT)",
     "For many the real jolt was years ago: GPT-2's unicorn article ('history is now divided into before and after'), the DALL-E avocado armchair, AI Dungeon, MidJourney v3 'understanding what words look like', AlphaGo/Lee Sedol, word2vec king-queen, or simply talking to a 7GB model running locally on their own CPU."),
    ("Creative work — the line we thought was ours",
     "Suno songs that made spouses laugh out loud or moved people to tears, a Claude metaphor ('fighting to unlock a door that opened onto a wall'), depressing-death-metal cat songs, King-James-Bible Postgres poems, novel-in-an-afternoon experiments. 'Creating art was supposed to be what separated us from machines.'"),
    ("Agentic autonomy — 'I went to sleep, it was done'",
     "Left it running overnight / while cooking dinner / at lunch and came back to a trained model, a finished rewrite, a compiled-and-deployed fix. One 8-hour, $200 GPT-Pro run fixed a bug that beat every other model. The recursive-self-improvement realisation scared a former transformer-paper author."),
    ("Vision & multimodal magic",
     "Live video call debugging a kid's science-fair electromagnet (spotting un-scraped wire insulation the eye missed), critiquing a hand-drawn anatomy sketch better than any human teacher, translating hand-painted Kanji rally signs by writing inline Python to crop the image, identifying fridge-magnet travel souvenirs."),
    ("The dark 'oh shit' (uh-oh)",
     "Weaponising a proof-of-concept exploit against a default config ('a blinking cursor on a nuclear information bomb'); one-prompt profiling of a person from their post history; colleagues in 'AI psychosis' shipping un-reviewable slop; deskilling juniors who'll 'never get better than they are right now'; energy/climate cost; teen suicides; astroturfing; the financial bubble; an agent that ran chmod 644 /usr/bin and bricked a system."),
    ("The skeptics & the unimpressed",
     "A meaningful minority report no 'oh shit' at all: 'glorified autocomplete', a 'complete BS machine telling us what we want to hear', fails on SIMD/GPGPU expertise, 'only CRUD apps', the scrambled-type-signature test that broke the illusion of understanding, and 'the only thing I say oh shit to is the deranged capital debt.'"),
]
theme_html = '\n'.join(
    f'<div class="theme"><h3>{html.escape(t)}</h3><p>{html.escape(d)}</p></div>'
    for t, d in THEMES)

page = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>"Oh shit" moments with GenAI — HN thread, every comment distilled</title>
<style>
  :root {{ --fg:#1a1a1a; --mut:#666; --acc:#c0392b; --bg:#fdfdfb; --card:#fff; --line:#eadfca; }}
  * {{ box-sizing:border-box; }}
  body {{ font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;
         color:var(--fg); background:var(--bg); margin:0; }}
  .wrap {{ max-width:860px; margin:0 auto; padding:32px 20px 90px; }}
  h1 {{ font-size:30px; line-height:1.2; margin:0 0 6px; }}
  .sub {{ color:var(--mut); margin:0 0 22px; }}
  .sub a, a.src {{ color:var(--acc); }}
  h2 {{ font-size:21px; margin:42px 0 12px; border-bottom:2px solid var(--line); padding-bottom:6px; }}
  .theme {{ margin:0 0 15px; }}
  .theme h3 {{ font-size:16px; margin:0 0 3px; color:var(--acc); }}
  .theme p {{ margin:0; color:#333; }}
  .controls {{ position:sticky; top:0; background:var(--bg); padding:12px 0; z-index:5;
               border-bottom:1px solid var(--line); display:flex; gap:12px; align-items:center; flex-wrap:wrap; }}
  #q {{ flex:1; min-width:220px; padding:9px 12px; font-size:15px; border:1px solid #ccc; border-radius:8px; }}
  .controls label {{ font-size:14px; color:var(--mut); display:flex; gap:5px; align-items:center; cursor:pointer; }}
  #count {{ font-size:13px; color:var(--mut); }}
  ol.index {{ list-style:none; margin:14px 0 0; padding:0; counter-reset:none; }}
  ol.index li {{ padding:7px 10px; border-bottom:1px solid #f0ead9; }}
  ol.index li.top {{ border-left:3px solid var(--acc); background:#fffdf8; }}
  ol.index li .s {{ }}
  ol.index li .who {{ color:var(--mut); font-size:13px; }}
  a.fn {{ color:var(--acc); text-decoration:none; font-size:12px; vertical-align:super;
          font-weight:600; cursor:pointer; white-space:nowrap; }}
  a.fn:hover {{ text-decoration:underline; }}
  .c {{ background:var(--card); border:1px solid var(--line); border-radius:10px;
        padding:12px 16px; margin:10px 0; }}
  .c.top {{ border-left:4px solid var(--acc); }}
  .c p {{ margin:0 0 8px; }}  .c p:last-child {{ margin-bottom:0; }}
  .meta {{ font-size:13px; color:var(--mut); margin-bottom:6px; }}
  .meta .u {{ font-weight:600; color:#444; }}
  .meta .fnum {{ color:var(--acc); font-weight:700; }}
  .reply {{ background:#eee; border-radius:4px; padding:0 6px; font-size:11px; }}
  .lvl1{{margin-left:18px}} .lvl2{{margin-left:36px}} .lvl3{{margin-left:54px}}
  .lvl4{{margin-left:72px}} .lvl5{{margin-left:90px}} .lvl6{{margin-left:104px}} .lvl7{{margin-left:116px}}
  @media(max-width:640px){{ .lvl1,.lvl2,.lvl3,.lvl4,.lvl5,.lvl6,.lvl7{{margin-left:8px}} }}
  .c a {{ color:var(--acc); word-break:break-word; }}
  .c:target {{ outline:3px solid #f1c40f; outline-offset:2px; }}
  .hidden {{ display:none; }}
  /* hover preview tooltip */
  #tip {{ position:absolute; display:none; max-width:430px; max-height:320px; overflow:auto;
          background:#fff; border:1px solid #d8cba6; border-radius:10px; padding:12px 14px;
          box-shadow:0 8px 30px rgba(0,0,0,.18); z-index:50; font-size:14px; line-height:1.5; }}
  #tip p {{ margin:0 0 7px; }}  #tip p:last-child {{ margin:0; }}
  #tip .meta {{ margin-bottom:6px; }}
</style>
</head>
<body>
<div class="wrap">
  <h1>&ldquo;Oh shit&rdquo; moments with GenAI</h1>
  <p class="sub">Every comment from the Hacker News thread
  <em>&ldquo;Ask HN: What was your &lsquo;oh shit&rsquo; moment with GenAI?&rdquo;</em> distilled to one line.
  {n_total} comments ({n_top} top-level answers, {n_reply} replies). Built {today}.<br>
  Each line ends with a footnote &mdash; <strong>hover it</strong> to preview the full comment, or click to jump to it below.</p>

  <h2>The patterns</h2>
  {theme_html}

  <h2>Every moment, one line each ({len(usable)})</h2>
  <div class="controls">
    <input id="q" type="search" placeholder="Search all moments (e.g. furnace, ghidra, suno, bricked)…" autocomplete="off">
    <label><input type="checkbox" id="toponly"> top-level only</label>
    <span id="count"></span>
  </div>
  <ol class="index" id="index">
  {index_html}
  </ol>

  <h2>Full comments</h2>
  <p class="sub">The footnote targets, in thread order (replies indented).</p>
  <div id="full">
  {full_html}
  </div>
</div>
<div id="tip"></div>
<script>
  const q = document.getElementById('q');
  const toponly = document.getElementById('toponly');
  const rows = Array.from(document.querySelectorAll('#index li'));
  const count = document.getElementById('count');
  function run(){{
    const term = q.value.trim().toLowerCase();
    const top = toponly.checked;
    let shown = 0;
    rows.forEach(r => {{
      const okTop = !top || r.classList.contains('top');
      const okTerm = !term || r.dataset.blob.includes(term);
      if (okTop && okTerm) {{ r.classList.remove('hidden'); shown++; }}
      else r.classList.add('hidden');
    }});
    count.textContent = shown + ' shown';
  }}
  q.addEventListener('input', run);
  toponly.addEventListener('change', run);
  run();

  // hover preview
  const tip = document.getElementById('tip');
  let hideT;
  function showTip(a){{
    const t = document.getElementById(a.dataset.t);
    if(!t) return;
    clearTimeout(hideT);
    tip.innerHTML = t.innerHTML;
    tip.style.display = 'block';
    const r = a.getBoundingClientRect();
    const th = tip.offsetHeight, tw = tip.offsetWidth;
    let top = r.bottom + 8;
    if (top + th > window.innerHeight - 6) top = Math.max(6, r.top - th - 8);
    let left = Math.min(r.left, window.innerWidth - tw - 12);
    left = Math.max(8, left);
    tip.style.top = (top + window.scrollY) + 'px';
    tip.style.left = (left + window.scrollX) + 'px';
  }}
  function hideTip(){{ hideT = setTimeout(()=>{{ tip.style.display='none'; }}, 120); }}
  document.querySelectorAll('a.fn').forEach(a => {{
    a.addEventListener('mouseenter', () => showTip(a));
    a.addEventListener('mouseleave', hideTip);
  }});
  tip.addEventListener('mouseenter', () => clearTimeout(hideT));
  tip.addEventListener('mouseleave', hideTip);
</script>
</body>
</html>'''

open('oh_shit_moments.html', 'w', encoding='utf-8').write(page)
print('wrote oh_shit_moments.html (', len(page)//1024, 'KB )  index rows:', len(usable))
