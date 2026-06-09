# build_oh_shit_html.py
# Builds a self-contained, searchable HTML page from the parsed Hacker News thread
# "Ask HN: What was your 'oh shit' moment with GenAI?".
#   hn_comments.json : all parsed comments (author, indent, text)
#   summaries.json   : {idx: one-line distilled summary} for every usable comment
#   categories.json  : {idx: category_key} assigning every comment to a theme
# Output index.html: every moment as a footnoted bullet grouped under its theme
# (footnote links to the full comment + shows a hover preview), plus the full
# threaded comments below as footnote targets, plus live search. No dependencies.

import json, html, re, datetime

comments = json.load(open('hn_comments.json'))
summaries = {int(k): v for k, v in json.load(open('summaries.json')).items()}
cats = {int(k): v for k, v in json.load(open('categories.json')).items()}
usable = [c for c in comments if len(c['text']) > 20]

URL_RE = re.compile(r'(https?://[^\s<>"\)]+)')
def linkify(text):
    esc = html.escape(text)
    return URL_RE.sub(lambda m: f'<a href="{m.group(1)}" target="_blank" rel="noopener">{m.group(1)}</a>', esc)

# (key, title, description). Order = display order.
CATS = [
 ("hardware", "Resurrecting dead / undocumented hardware",
  "Hand an LLM a binary firmware, a hex dump, or a Ghidra disassembly and get back a working driver, parser, license-key generator, or root exploit — synths, camper-van CAN buses, Firesticks, iPods, cameras, FPGAs, model trains, vintage amps."),
 ("reverse_eng", "Reverse-engineering software, protocols & formats",
  "Cracking the non-physical: network protocols, proprietary binary streams, decompiled apps, minified files, bytecode → idiomatic source, undocumented APIs."),
 ("repair", "Home & life repair with zero domain knowledge",
  "Non-coding wins from a photo or video: furnaces and steam heat, dishwashers, cars, koi-pond pumps, fire-alarm panels, bath taps, wiring, plants, solar and electrical work."),
 ("debug", "Debugging the previously undebuggable",
  "Race conditions, memory bugs, cross-module state bugs that stumped senior engineers, hardware faults inferred from code, years-old bugs solved by reading live production logs."),
 ("shipped", "Real software, shipped fast",
  "Whole apps to the App Store, overnight rewrites, dashboards in an afternoon, games, compilers, even an OS that runs Doom — built far faster than the person thought possible."),
 ("nontech", "Non-technical people building things",
  "Someone who'd never touched code (a brother, a friend, a lawyer) shipping real, working software."),
 ("science", "Science, math & research",
  "Counterexamples to standing conjectures, proofs in minutes, novel derivations, physics simulations and digital twins."),
 ("multimodal", "Vision & multimodal magic",
  "Diagnosing from photos, live-video help, OCR/translation of images by writing inline code, voice mode."),
 ("creative", "Creative work — the line we thought was ours",
  "Suno songs that moved people, original metaphors, poems, stories, images and art."),
 ("agentic", "Agentic autonomy & tool use",
  "Left it running unattended and came back to a finished result; watching it drive the terminal, browser, or other tools in a loop; the first time it called a tool at all."),
 ("workflow", "Coding workflow, transformed",
  "Refactoring at scale, AI code review, onboarding to a strange codebase in minutes, 'I've barely written a manual line since.'"),
 ("knowledge", "Knowledge work & life admin",
  "Research assistant and paperwork: summarizing documents, comparing contractor bids, appealing property taxes, taming an inbox, filling government forms."),
 ("learning", "Learning, tutoring & feedback",
  "Explaining concepts, teaching, and critiquing the user's own work — anatomy sketches, writing, exam material."),
 ("local", "Local & open-weight models on your own machine",
  "The wow of talking to a model running on your own CPU/GPU — leaked weights, llama.cpp, quantization, dirt-cheap open models."),
 ("early_awe", "The early-model awe (GPT-2 → DALL-E → ChatGPT)",
  "The jolt came from the model itself: GPT-2's unicorns, the DALL-E avocado armchair, MidJourney, AlphaGo, word2vec, the first ChatGPT."),
 ("dark", "The dark 'oh shit' (uh-oh)",
  "Weaponized exploits, surveillance and profiling, job-loss dread, the bubble and circular financing, 'AI psychosis' colleagues, deskilling, energy and climate, astroturfing, suicides."),
 ("skeptic", "The skeptics & the unimpressed",
  "No 'oh shit' at all: 'glorified autocomplete', a 'BS machine', fails outside its training distribution, only does CRUD, the illusion-breaking tests."),
 ("other", "Other moments, meta & hard to classify",
  "Everything that didn't fit one bucket cleanly — generic 'first time I tried it' awe, mixed multi-part stories, jokes, and meta commentary about the thread itself."),
]

by_cat = {k: [] for k, _, _ in CATS}
for i in range(len(usable)):
    by_cat.get(cats.get(i, 'other'), by_cat['other']).append(i)

def bullet(idx):
    c = usable[idx]
    summ = html.escape(summaries.get(idx, '(no summary)'))
    user = html.escape(c['user']) if c['user'] else 'anon'
    top = ' top' if c['indent'] == 0 else ''
    blob = html.escape((user + ' ' + summaries.get(idx, '') + ' ' + c['text']).lower())
    return (f'<li class="b{top}" data-blob="{blob}">{summ} '
            f'<a class="fn" href="#c{idx}" data-t="c{idx}">[{idx+1}]</a> '
            f'<span class="who">{user}</span></li>')

sections = []
for k, title, desc in CATS:
    ids = sorted(by_cat[k], key=lambda i: (usable[i]['indent'] > 0, i))
    if not ids: continue
    bl = '\n'.join(bullet(i) for i in ids)
    sections.append(
        f'<section class="cat" data-cat="{k}">\n'
        f'  <h3>{html.escape(title)} <span class="n">{len(ids)}</span></h3>\n'
        f'  <p class="desc">{html.escape(desc)}</p>\n'
        f'  <ul class="bullets">\n{bl}\n  </ul>\n</section>')
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
            f'  <div class="meta"><span class="fnum">{idx+1}.</span> '
            f'<span class="u">{user}</span>{tag}</div>\n  {body}\n</div>')
full_html = '\n'.join(render_full(c, i) for i, c in enumerate(usable))

n_total = len(comments)
n_top = sum(1 for c in comments if c['indent'] == 0)
n_reply = n_total - n_top
today = datetime.date(2026, 6, 9).strftime('%-d %b %Y')
toc = ' · '.join(f'<a href="#" data-jump="{k}">{html.escape(t)} ({len(by_cat[k])})</a>'
                 for k, t, _ in CATS if by_cat[k])

page = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>"Oh shit" moments with GenAI — every comment, categorized</title>
<style>
  :root {{ --fg:#1a1a1a; --mut:#666; --acc:#c0392b; --bg:#fdfdfb; --card:#fff; --line:#eadfca; }}
  * {{ box-sizing:border-box; }}
  body {{ font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif; color:var(--fg); background:var(--bg); margin:0; }}
  .wrap {{ max-width:880px; margin:0 auto; padding:32px 20px 90px; }}
  h1 {{ font-size:30px; line-height:1.2; margin:0 0 6px; }}
  .sub {{ color:var(--mut); margin:0 0 18px; }}
  .sub strong {{ color:#333; }}
  .toc {{ font-size:13px; line-height:1.9; color:var(--mut); margin:0 0 8px; }}
  .toc a {{ color:var(--acc); text-decoration:none; }} .toc a:hover {{ text-decoration:underline; }}
  .controls {{ position:sticky; top:0; background:var(--bg); padding:12px 0; z-index:5; border-bottom:1px solid var(--line); display:flex; gap:12px; align-items:center; flex-wrap:wrap; }}
  #q {{ flex:1; min-width:220px; padding:9px 12px; font-size:15px; border:1px solid #ccc; border-radius:8px; }}
  .controls label {{ font-size:14px; color:var(--mut); display:flex; gap:5px; align-items:center; cursor:pointer; }}
  #count {{ font-size:13px; color:var(--mut); }}
  section.cat {{ margin:26px 0 0; scroll-margin-top:64px; }}
  section.cat h3 {{ font-size:20px; margin:0 0 2px; border-bottom:2px solid var(--line); padding-bottom:5px; }}
  section.cat h3 .n {{ color:var(--acc); font-size:14px; font-weight:600; }}
  .desc {{ color:var(--mut); font-size:14px; margin:4px 0 8px; }}
  ul.bullets {{ margin:0; padding:0; list-style:none; }}
  ul.bullets li.b {{ padding:5px 8px 5px 16px; border-bottom:1px solid #f3eddd; position:relative; }}
  ul.bullets li.b:before {{ content:"›"; position:absolute; left:2px; color:#cbb27a; }}
  ul.bullets li.b.top {{ background:#fffdf8; }}
  .who {{ color:var(--mut); font-size:12.5px; }}
  a.fn {{ color:var(--acc); text-decoration:none; font-size:12px; vertical-align:super; font-weight:600; cursor:pointer; white-space:nowrap; }}
  a.fn:hover {{ text-decoration:underline; }}
  h2 {{ font-size:21px; margin:46px 0 10px; border-bottom:2px solid var(--line); padding-bottom:6px; }}
  .c {{ background:var(--card); border:1px solid var(--line); border-radius:10px; padding:12px 16px; margin:10px 0; }}
  .c.top {{ border-left:4px solid var(--acc); }}
  .c p {{ margin:0 0 8px; }} .c p:last-child {{ margin-bottom:0; }}
  .meta {{ font-size:13px; color:var(--mut); margin-bottom:6px; }}
  .meta .u {{ font-weight:600; color:#444; }} .meta .fnum {{ color:var(--acc); font-weight:700; }}
  .reply {{ background:#eee; border-radius:4px; padding:0 6px; font-size:11px; }}
  .lvl1{{margin-left:18px}} .lvl2{{margin-left:36px}} .lvl3{{margin-left:54px}} .lvl4{{margin-left:72px}} .lvl5{{margin-left:90px}} .lvl6{{margin-left:104px}} .lvl7{{margin-left:116px}}
  @media(max-width:640px){{ .lvl1,.lvl2,.lvl3,.lvl4,.lvl5,.lvl6,.lvl7{{margin-left:8px}} }}
  .c a {{ color:var(--acc); word-break:break-word; }}
  .c:target {{ outline:3px solid #f1c40f; outline-offset:2px; }}
  .hidden {{ display:none !important; }}
  #tip {{ position:absolute; display:none; max-width:430px; max-height:320px; overflow:auto; background:#fff; border:1px solid #d8cba6; border-radius:10px; padding:12px 14px; box-shadow:0 8px 30px rgba(0,0,0,.18); z-index:50; font-size:14px; line-height:1.5; }}
  #tip p {{ margin:0 0 7px; }} #tip p:last-child {{ margin:0; }} #tip .meta {{ margin-bottom:6px; }}
</style>
</head>
<body>
<div class="wrap">
  <h1>&ldquo;Oh shit&rdquo; moments with GenAI</h1>
  <p class="sub">Every comment from the Hacker News thread
  <em>&ldquo;Ask HN: What was your &lsquo;oh shit&rsquo; moment with GenAI?&rdquo;</em> distilled to one line and sorted into themes.
  <strong>{n_total}</strong> comments ({n_top} top-level answers, {n_reply} replies) → {len(usable)} moments.
  Built {today}. Each bullet's footnote &mdash; <strong>hover</strong> to preview the full comment, click to jump to it.</p>
  <p class="toc">{toc}</p>

  <div class="controls">
    <input id="q" type="search" placeholder="Search all moments (e.g. furnace, ghidra, suno, bricked)…" autocomplete="off">
    <label><input type="checkbox" id="toponly"> top-level only</label>
    <span id="count"></span>
  </div>

  {sections_html}

  <h2>Full comments</h2>
  <p class="sub">The footnote targets, in thread order (replies indented).</p>
  <div id="full">
  {full_html}
  </div>
</div>
<div id="tip"></div>
<script>
  const q=document.getElementById('q'), toponly=document.getElementById('toponly'), count=document.getElementById('count');
  const bullets=Array.from(document.querySelectorAll('li.b')), secs=Array.from(document.querySelectorAll('section.cat'));
  function run(){{
    const term=q.value.trim().toLowerCase(), top=toponly.checked; let shown=0;
    bullets.forEach(b=>{{
      const ok=(!top||b.classList.contains('top')) && (!term||b.dataset.blob.includes(term));
      b.classList.toggle('hidden',!ok); if(ok)shown++;
    }});
    secs.forEach(s=>{{ const any=s.querySelector('li.b:not(.hidden)'); s.classList.toggle('hidden',!any); }});
    count.textContent=shown+' shown';
  }}
  q.addEventListener('input',run); toponly.addEventListener('change',run); run();
  document.querySelectorAll('.toc a').forEach(a=>a.addEventListener('click',e=>{{
    e.preventDefault(); const s=document.querySelector('section[data-cat="'+a.dataset.jump+'"]');
    if(s) s.scrollIntoView({{behavior:'smooth'}});
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

open('oh_shit_moments.html', 'w', encoding='utf-8').write(page)
print('wrote oh_shit_moments.html (', len(page)//1024, 'KB )')
for k, t, _ in CATS:
    if by_cat[k]: print(f'  {len(by_cat[k]):4d}  {t}')
