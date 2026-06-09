# build_oh_shit_html.py
# Builds a self-contained, searchable HTML page from the parsed Hacker News thread
# "Ask HN: What was your 'oh shit' moment with GenAI?".
#   hn_comments.json    : all parsed comments (author, indent, text)
#   summaries.json      : {idx: one-line distilled summary} for every usable comment
#   categories_v2.json  : {idx: category_key | 'drop'} (Sonnet pass; drop = not a real moment)
# Output index.html: real moments as footnoted bullets grouped under collapsible
# theme sections (footnote links to the full comment + hover preview), full
# threaded comments below as footnote targets, live search. No dependencies.

import json, html, re, datetime

comments = json.load(open('hn_comments.json'))
summaries = {int(k): v for k, v in json.load(open('summaries.json')).items()}
cats = {int(k): v for k, v in json.load(open('categories_v2.json')).items()}  # Sonnet pass w/ drop
usable = [c for c in comments if len(c['text']) > 20]

URL_RE = re.compile(r'(https?://[^\s<>"\)]+)')
def linkify(text):
    esc = html.escape(text)
    return URL_RE.sub(lambda m: f'<a href="{m.group(1)}" target="_blank" rel="noopener">{m.group(1)}</a>', esc)

# (key, emoji, title, description). Order = display order (largest themes first).
CATS = [
 ("dark", "&#9888;&#65039;", "The dark &lsquo;oh shit&rsquo; (uh-oh)",
  "Weaponized exploits, surveillance and profiling, job-loss dread, the bubble and circular financing, 'AI psychosis' colleagues, deskilling, energy and climate, astroturfing, suicides."),
 ("workflow", "&#128295;", "Coding workflow, transformed",
  "Refactoring at scale, AI code review, onboarding to a strange codebase in minutes, 'I've barely written a manual line since.'"),
 ("early_awe", "&#10024;", "The early-model awe (GPT-2 &rarr; DALL-E &rarr; ChatGPT)",
  "The jolt came from the model itself: GPT-2's unicorns, the DALL-E avocado armchair, MidJourney, AlphaGo, word2vec, the first ChatGPT."),
 ("shipped", "&#128640;", "Real software, shipped fast",
  "Whole apps to the App Store, overnight rewrites, dashboards in an afternoon, games, compilers, even an OS that runs Doom &mdash; built far faster than the person thought possible."),
 ("skeptic", "&#129320;", "The skeptics &amp; the unimpressed",
  "A substantive 'no' &mdash; 'glorified autocomplete', a 'BS machine', fails outside its training distribution, only does CRUD, the illusion-breaking tests."),
 ("agentic", "&#129302;", "Agentic autonomy &amp; tool use",
  "Left it running unattended and came back to a finished result; watching it drive the terminal, browser, or other tools in a loop; the first time it called a tool at all."),
 ("debug", "&#128027;", "Debugging the previously undebuggable",
  "Race conditions, memory bugs, cross-module state bugs that stumped senior engineers, hardware faults inferred from code, years-old bugs solved by reading live production logs."),
 ("knowledge", "&#128218;", "Knowledge work &amp; life admin",
  "Research assistant and paperwork: summarizing documents, comparing contractor bids, appealing property taxes, taming an inbox, filling government forms."),
 ("repair", "&#128736;&#65039;", "Home &amp; life repair with zero domain knowledge",
  "Non-coding wins from a photo or video: furnaces and steam heat, dishwashers, cars, koi-pond pumps, fire-alarm panels, bath taps, wiring, plants, solar and electrical work."),
 ("creative", "&#127925;", "Creative work &mdash; the line we thought was ours",
  "Suno songs that moved people, original metaphors, poems, stories, images and art."),
 ("reverse_eng", "&#129513;", "Reverse-engineering software, protocols &amp; formats",
  "Cracking the non-physical: network protocols, proprietary binary streams, decompiled apps, minified files, bytecode &rarr; idiomatic source, undocumented APIs."),
 ("hardware", "&#128268;", "Resurrecting dead / undocumented hardware",
  "Hand an LLM a binary firmware, a hex dump, or a Ghidra disassembly and get back a working driver, parser, license-key generator, or root exploit &mdash; synths, camper-van CAN buses, Firesticks, iPods, cameras, FPGAs, model trains, vintage amps."),
 ("multimodal", "&#128064;", "Vision &amp; multimodal magic",
  "Diagnosing from photos, live-video help, OCR/translation of images by writing inline code, voice mode."),
 ("science", "&#128300;", "Science, math &amp; research",
  "Counterexamples to standing conjectures, proofs in minutes, novel derivations, physics simulations and digital twins."),
 ("learning", "&#127891;", "Learning, tutoring &amp; feedback",
  "Explaining concepts, teaching, and critiquing the user's own work &mdash; anatomy sketches, writing, exam material."),
 ("local", "&#128187;", "Local &amp; open-weight models on your own machine",
  "The wow of talking to a model running on your own CPU/GPU &mdash; leaked weights, llama.cpp, quantization, dirt-cheap open models."),
 ("nontech", "&#129321;", "Non-technical people building things",
  "Someone who'd never touched code (a brother, a friend, a lawyer) shipping real, working software."),
]

by_cat = {k: [] for k, _, _, _ in CATS}
n_drop = 0
for i in range(len(usable)):
    k = cats.get(i, 'drop')
    if k in by_cat:
        by_cat[k].append(i)
    else:
        n_drop += 1   # 'drop' = not a real moment (questions, meta, banter) — excluded from bullets

def bullet(idx):
    c = usable[idx]
    summ = html.escape(summaries.get(idx, '(no summary)'))
    user = html.escape(c['user']) if c['user'] else 'anon'
    top = ' top' if c['indent'] == 0 else ''
    blob = html.escape((user + ' ' + summaries.get(idx, '') + ' ' + c['text']).lower())
    return (f'<li class="b{top}" data-blob="{blob}"><span class="s">{summ}</span> '
            f'<a class="fn" href="#c{idx}" data-t="c{idx}">[{idx+1}]</a> '
            f'<span class="who">{user}</span></li>')

sections = []
for k, emoji, title, desc in CATS:
    ids = sorted(by_cat[k], key=lambda i: (usable[i]['indent'] > 0, i))
    if not ids: continue
    bl = '\n'.join(bullet(i) for i in ids)
    sections.append(f'''<details class="cat" data-cat="{k}" id="cat-{k}">
  <summary>
    <span class="chev" aria-hidden="true">&#9656;</span>
    <span class="emoji">{emoji}</span>
    <span class="t">{title}</span>
    <span class="n">{len(ids)}</span>
  </summary>
  <div class="body">
    <p class="desc">{desc}</p>
    <ul class="bullets">
{bl}
    </ul>
  </div>
</details>''')
sections_html = '\n'.join(sections)

# full comment cards (footnote targets)
def render_full(c, idx):
    ind = min(c['indent'], 7)
    user = html.escape(c['user']) if c['user'] else 'anon'
    paras = [p for p in c['text'].split('\n') if p.strip()]
    body = '\n'.join(f'<p>{linkify(p)}</p>' for p in paras)
    top = ' top' if c['indent'] == 0 else ''
    tag = '' if c['indent'] == 0 else ' <span class="reply">reply</span>'
    return (f'<div class="c lvl{ind}{top}" id="c{idx}">\n'
            f'  <div class="meta"><span class="fnum">{idx+1}</span> '
            f'<span class="u">{user}</span>{tag}</div>\n  {body}\n</div>')
full_html = '\n'.join(render_full(c, i) for i, c in enumerate(usable))

n_total = len(comments)
n_top = sum(1 for c in comments if c['indent'] == 0)
n_reply = n_total - n_top
n_kept = len(usable) - n_drop
today = datetime.date(2026, 6, 9).strftime('%-d %b %Y')

chips = '\n'.join(
    f'<a class="chip" href="#cat-{k}" data-jump="{k}">{emoji} {t} <b>{len(by_cat[k])}</b></a>'
    for k, emoji, t, _ in CATS if by_cat[k])

page = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>"Oh shit" moments with GenAI — every comment, categorized</title>
<style>
  :root {{
    --ink:#22201c; --mut:#7a7468; --acc:#d4502e; --acc-soft:#fbe9e2;
    --bg:#f7f4ee; --card:#fffdf9; --line:#e7e0d2; --gold:#f1c40f;
    --shadow:0 1px 2px rgba(60,50,30,.06), 0 6px 18px rgba(60,50,30,.06);
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --ink:#ece7dd; --mut:#9b948a; --acc:#ff7a52; --acc-soft:#3a2620;
      --bg:#16140f; --card:#1f1c16; --line:#322d24; --gold:#b08d12;
      --shadow:0 1px 2px rgba(0,0,0,.4), 0 8px 24px rgba(0,0,0,.35);
    }}
  }}
  * {{ box-sizing:border-box; }}
  html {{ scroll-behavior:smooth; }}
  body {{ margin:0; background:var(--bg); color:var(--ink);
          font:16px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;
          -webkit-font-smoothing:antialiased; }}
  .wrap {{ max-width:900px; margin:0 auto; padding:48px 22px 100px; }}

  /* hero */
  .hero h1 {{ font-family:Charter,Georgia,"Times New Roman",serif; font-size:clamp(30px,5vw,44px);
              line-height:1.12; margin:0 0 12px; letter-spacing:-.01em; }}
  .hero h1 em {{ color:var(--acc); font-style:normal; }}
  .hero .sub {{ color:var(--mut); margin:0 0 6px; max-width:66ch; }}
  .hero .sub strong {{ color:var(--ink); }}
  .stats {{ display:flex; gap:10px; flex-wrap:wrap; margin:20px 0 4px; }}
  .stat {{ background:var(--card); border:1px solid var(--line); border-radius:12px;
           padding:8px 16px; box-shadow:var(--shadow); font-size:13px; color:var(--mut); }}
  .stat b {{ display:block; font-size:21px; color:var(--ink); font-variant-numeric:tabular-nums; }}
  .stat.hot b {{ color:var(--acc); }}

  /* chips nav */
  .chips {{ display:flex; gap:7px; flex-wrap:wrap; margin:22px 0 2px; }}
  .chip {{ font-size:12.5px; color:var(--ink); text-decoration:none; background:var(--card);
           border:1px solid var(--line); border-radius:999px; padding:4px 11px;
           transition:border-color .15s, transform .15s; }}
  .chip:hover {{ border-color:var(--acc); transform:translateY(-1px); }}
  .chip b {{ color:var(--acc); font-weight:700; margin-left:2px; }}

  /* sticky controls */
  .controls {{ position:sticky; top:0; z-index:10; display:flex; gap:10px; align-items:center;
               flex-wrap:wrap; padding:12px 0; margin-top:16px;
               background:color-mix(in srgb, var(--bg) 84%, transparent);
               backdrop-filter:blur(10px); -webkit-backdrop-filter:blur(10px);
               border-bottom:1px solid var(--line); }}
  #q {{ flex:1; min-width:210px; padding:10px 14px; font-size:15px; color:var(--ink);
        background:var(--card); border:1px solid var(--line); border-radius:12px; outline:none;
        transition:border-color .15s, box-shadow .15s; }}
  #q:focus {{ border-color:var(--acc); box-shadow:0 0 0 3px var(--acc-soft); }}
  .controls label {{ font-size:13.5px; color:var(--mut); display:flex; gap:6px;
                     align-items:center; cursor:pointer; user-select:none; }}
  .btn {{ font-size:12.5px; color:var(--mut); background:var(--card); border:1px solid var(--line);
          border-radius:9px; padding:6px 11px; cursor:pointer; transition:border-color .15s, color .15s; }}
  .btn:hover {{ border-color:var(--acc); color:var(--acc); }}
  #count {{ font-size:12.5px; color:var(--mut); font-variant-numeric:tabular-nums; }}

  /* collapsible category sections */
  details.cat {{ background:var(--card); border:1px solid var(--line); border-radius:16px;
                 margin:14px 0; box-shadow:var(--shadow); overflow:hidden; scroll-margin-top:76px; }}
  details.cat summary {{ list-style:none; cursor:pointer; display:flex; align-items:center; gap:11px;
                         padding:15px 18px; user-select:none; }}
  details.cat summary::-webkit-details-marker {{ display:none; }}
  details.cat summary:hover {{ background:color-mix(in srgb, var(--acc-soft) 45%, transparent); }}
  .chev {{ color:var(--acc); font-size:14px; transition:transform .2s ease; flex:none; }}
  details[open] > summary .chev {{ transform:rotate(90deg); }}
  .emoji {{ font-size:19px; flex:none; }}
  summary .t {{ font-family:Charter,Georgia,serif; font-size:19px; font-weight:600; line-height:1.25; }}
  summary .n {{ margin-left:auto; flex:none; background:var(--acc-soft); color:var(--acc);
                font-size:12.5px; font-weight:700; border-radius:999px; padding:2px 11px;
                font-variant-numeric:tabular-nums; }}
  details.cat .body {{ padding:2px 18px 14px; border-top:1px dashed var(--line); }}
  .desc {{ color:var(--mut); font-size:13.5px; margin:10px 0 6px; max-width:75ch; }}
  ul.bullets {{ margin:0; padding:0; list-style:none; }}
  ul.bullets li.b {{ padding:7px 6px 7px 22px; position:relative; border-radius:8px; }}
  ul.bullets li.b + li.b {{ border-top:1px solid color-mix(in srgb, var(--line) 55%, transparent); }}
  ul.bullets li.b:before {{ content:"\\2023"; position:absolute; left:6px; color:var(--acc); opacity:.7; }}
  ul.bullets li.b:hover {{ background:color-mix(in srgb, var(--acc-soft) 38%, transparent); }}
  ul.bullets li.b .who {{ color:var(--mut); font-size:12px; }}
  ul.bullets li.b.top .s {{ }}
  a.fn {{ color:var(--acc); text-decoration:none; font-size:11.5px; vertical-align:super;
          font-weight:700; cursor:pointer; white-space:nowrap; }}
  a.fn:hover {{ text-decoration:underline; }}

  /* full comments */
  h2 {{ font-family:Charter,Georgia,serif; font-size:26px; margin:54px 0 8px; }}
  .secsub {{ color:var(--mut); font-size:14px; margin:0 0 14px; }}
  .c {{ background:var(--card); border:1px solid var(--line); border-radius:14px;
        padding:13px 17px; margin:10px 0; box-shadow:var(--shadow); }}
  .c.top {{ border-left:4px solid var(--acc); }}
  .c p {{ margin:0 0 8px; }} .c p:last-child {{ margin-bottom:0; }}
  .meta {{ font-size:12.5px; color:var(--mut); margin-bottom:6px; display:flex; gap:8px; align-items:center; }}
  .meta .u {{ font-weight:600; color:var(--ink); }}
  .meta .fnum {{ background:var(--acc-soft); color:var(--acc); font-weight:700; border-radius:6px;
                 padding:0 7px; font-variant-numeric:tabular-nums; }}
  .reply {{ background:color-mix(in srgb, var(--line) 60%, transparent); border-radius:5px;
            padding:0 7px; font-size:10.5px; text-transform:uppercase; letter-spacing:.04em; }}
  .lvl1{{margin-left:20px}} .lvl2{{margin-left:40px}} .lvl3{{margin-left:60px}}
  .lvl4{{margin-left:80px}} .lvl5{{margin-left:96px}} .lvl6{{margin-left:108px}} .lvl7{{margin-left:118px}}
  @media(max-width:640px){{ .lvl1,.lvl2,.lvl3,.lvl4,.lvl5,.lvl6,.lvl7{{margin-left:10px}} }}
  .c a {{ color:var(--acc); word-break:break-word; }}
  .c:target {{ outline:3px solid var(--gold); outline-offset:2px; }}
  .hidden {{ display:none !important; }}

  /* hover preview tooltip */
  #tip {{ position:absolute; display:none; max-width:440px; max-height:330px; overflow:auto;
          background:var(--card); border:1px solid var(--line); border-radius:14px;
          padding:13px 16px; box-shadow:0 12px 40px rgba(0,0,0,.25); z-index:50;
          font-size:14px; line-height:1.55; }}
  #tip p {{ margin:0 0 7px; }} #tip p:last-child {{ margin:0; }} #tip .meta {{ margin-bottom:6px; }}

  footer {{ margin-top:60px; color:var(--mut); font-size:13px; border-top:1px solid var(--line); padding-top:16px; }}
  footer a {{ color:var(--acc); }}
</style>
</head>
<body>
<div class="wrap">
  <header class="hero">
    <h1>&ldquo;<em>Oh shit</em>&rdquo; moments with GenAI</h1>
    <p class="sub">Every comment from the Hacker News thread
    <em>&ldquo;Ask HN: What was your &lsquo;oh shit&rsquo; moment with GenAI?&rdquo;</em>,
    distilled to one line and sorted into themes. Non-moments (questions, meta, thread banter) are filtered out.
    Each bullet ends in a footnote &mdash; <strong>hover</strong> it to preview the full comment, <strong>click</strong> to jump to it. Built {today}.</p>
    <div class="stats">
      <div class="stat"><b>{n_total}</b> comments parsed</div>
      <div class="stat"><b>{n_top}</b> top-level answers</div>
      <div class="stat hot"><b>{n_kept}</b> actual moments</div>
      <div class="stat"><b>{n_drop}</b> non-moments filtered</div>
    </div>
    <nav class="chips">
{chips}
    </nav>
  </header>

  <div class="controls">
    <input id="q" type="search" placeholder="Search all moments — furnace, ghidra, suno, bricked…" autocomplete="off">
    <label><input type="checkbox" id="toponly"> top-level only</label>
    <button class="btn" id="expand">Expand all</button>
    <button class="btn" id="collapse">Collapse all</button>
    <span id="count"></span>
  </div>

  {sections_html}

  <h2>Full comments</h2>
  <p class="secsub">The footnote targets &mdash; all {len(usable)} parsed comments in thread order (replies indented).</p>
  <div id="full">
  {full_html}
  </div>

  <footer>Source: a saved copy of the HN thread. Summaries &amp; categorization are LLM-generated
  (see <a href="https://github.com/HaukeHillebrandt/oh-shit-genai">repo</a> for the pipeline); follow the footnotes for the originals.</footer>
</div>
<div id="tip"></div>
<script>
  const q=document.getElementById('q'), toponly=document.getElementById('toponly'), count=document.getElementById('count');
  const bullets=Array.from(document.querySelectorAll('li.b')), secs=Array.from(document.querySelectorAll('details.cat'));
  function run(){{
    const term=q.value.trim().toLowerCase(), top=toponly.checked; let shown=0;
    bullets.forEach(b=>{{
      const ok=(!top||b.classList.contains('top')) && (!term||b.dataset.blob.includes(term));
      b.classList.toggle('hidden',!ok); if(ok)shown++;
    }});
    secs.forEach(s=>{{
      const any=s.querySelector('li.b:not(.hidden)');
      s.classList.toggle('hidden',!any);
      if(term && any) s.open=true;           // auto-open sections with matches
    }});
    count.textContent=shown+' shown';
  }}
  q.addEventListener('input',run); toponly.addEventListener('change',run); run();
  // open the first (largest) section by default
  if(secs[0]) secs[0].open=true;
  document.getElementById('expand').addEventListener('click',()=>secs.forEach(s=>s.open=true));
  document.getElementById('collapse').addEventListener('click',()=>secs.forEach(s=>s.open=false));
  // chips: open target section, then scroll
  document.querySelectorAll('.chip').forEach(a=>a.addEventListener('click',e=>{{
    const s=document.getElementById('cat-'+a.dataset.jump);
    if(s){{ s.open=true; }}
  }}));
  // hover preview
  const tip=document.getElementById('tip'); let hideT;
  function showTip(a){{ const t=document.getElementById(a.dataset.t); if(!t)return; clearTimeout(hideT);
    tip.innerHTML=t.innerHTML; tip.style.display='block';
    const r=a.getBoundingClientRect(), th=tip.offsetHeight, tw=tip.offsetWidth;
    let top=r.bottom+8; if(top+th>window.innerHeight-6) top=Math.max(6,r.top-th-8);
    let left=Math.max(8,Math.min(r.left,window.innerWidth-tw-12));
    tip.style.top=(top+window.scrollY)+'px'; tip.style.left=(left+window.scrollX)+'px'; }}
  function hideTip(){{ hideT=setTimeout(()=>tip.style.display='none',120); }}
  document.querySelectorAll('a.fn').forEach(a=>{{ a.addEventListener('mouseenter',()=>showTip(a)); a.addEventListener('mouseleave',hideTip); }});
  tip.addEventListener('mouseenter',()=>clearTimeout(hideT)); tip.addEventListener('mouseleave',hideTip);
</script>
</body>
</html>'''

open('index_out.html', 'w', encoding='utf-8').write(page)
import shutil; shutil.move('index_out.html', 'oh_shit_moments.html')
print('wrote oh_shit_moments.html (', len(page)//1024, 'KB )')
print(f'kept {n_kept} moments, dropped {n_drop}')
for k, _, t, _ in CATS:
    if by_cat[k]: print(f'  {len(by_cat[k]):4d}  {html.unescape(t)}')
