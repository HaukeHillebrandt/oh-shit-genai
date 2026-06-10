# build_fable_html.py
# Builds a self-contained page from the HN "Claude Fable 5" release thread:
# instances where commenters reported Fable 5 outperforming other LLMs,
# plus mixed verdicts and the counterpoint (underperformed), each bullet
# footnoted to the full comment with hover preview. Same design language as
# the "oh shit moments" page.
#   fable_usable.json : parsed comments (user, indent, text), idx = position
#   verdicts.json     : {idx: {verdict, domain, vs, summary}}

import json, html, re, datetime

usable = json.load(open('fable_usable.json'))
rows = {int(k): v for k, v in json.load(open('verdicts.json')).items()}

URL_RE = re.compile(r'(https?://[^\s<>"\)]+)')
def linkify(text):
    esc = html.escape(text)
    return URL_RE.sub(lambda m: f'<a href="{m.group(1)}" target="_blank" rel="noopener">{m.group(1)}</a>', esc)

def ids_for(verdict, domains=None):
    out = []
    for i in range(len(usable)):
        r = rows.get(i)
        if not r or r['verdict'] != verdict: continue
        if domains and r['domain'] not in domains: continue
        out.append(i)
    return sorted(out, key=lambda i: (usable[i]['indent'] > 0, i))

SECTIONS = [
 ("&#128027;", "Won at debugging", "Solved bugs and reverse-engineering problems that Opus, Codex or its predecessors couldn't.",
  ids_for('outperform', {'debug'}), 'win'),
 ("&#129302;", "Won at agentic work", "Longer unattended runs, better tool use, less hand-holding than the alternatives.",
  ids_for('outperform', {'agentic'}), 'win'),
 ("&#128064;", "Won at vision &amp; multimodal", "Better results on image, diagram and visual tasks than the models compared against.",
  ids_for('outperform', {'vision'}), 'win'),
 ("&#9997;&#65039;", "Won at writing", "Prose, summaries and creative output judged better than Opus / GPT in side-by-sides.",
  ids_for('outperform', {'writing'}), 'win'),
 ("&#129518;", "Won at reasoning &amp; analysis", "Math, logic and analysis where Fable made progress its predecessors or rivals didn't.",
  ids_for('outperform', {'reasoning'}), 'win'),
 ("&#128187;", "Won at coding", "Code generation and refactoring judged better than the comparison model.",
  ids_for('outperform', {'coding'}), 'win'),
 ("&#127942;", "Other wins", "Long-context, instruction-following and miscellaneous victories.",
  ids_for('outperform', {'context', 'instruct', 'speed_cost', 'other', '-'}), 'win'),
 ("&#9878;&#65039;", "Mixed verdicts", "Better at one thing, worse at another — or wins that came with substantive caveats.",
  ids_for('mixed'), 'mixed'),
 ("&#128683;", "Counterpoint: the safety-fallback complaints", "The single biggest gripe: Fable silently switching to Opus mid-session on 'sensitive' topics, defeating the comparison entirely.",
  ids_for('underperform', {'instruct'}), 'loss'),
 ("&#128201;", "Counterpoint: worse at agentic / coding work", "First-hand reports of Fable losing to Opus 4.x, GPT-5.5/Codex, or cheaper open-weight models on real tasks.",
  ids_for('underperform', {'agentic', 'coding', 'debug'}), 'loss'),
 ("&#129335;", "Counterpoint: no improvement, not worth it", "'Can't tell the difference from Opus 4.6', price/quota complaints with capability framing, and other regressions.",
  ids_for('underperform', {'other', 'speed_cost', 'reasoning', 'vision', 'context', 'writing', '-'}), 'loss'),
]

def bullet(idx):
    c = usable[idx]
    r = rows[idx]
    summ = html.escape(r['summary'])
    user = html.escape(c['user']) if c['user'] else 'anon'
    top = ' top' if c['indent'] == 0 else ''
    vs = r.get('vs', '-')
    vs_tag = f' <span class="vs">vs {html.escape(vs)}</span>' if vs and vs != '-' else ''
    blob = html.escape((user + ' ' + r['summary'] + ' ' + vs + ' ' + c['text']).lower())
    return (f'<li class="b{top}" data-blob="{blob}"><span class="s">{summ}</span>{vs_tag} '
            f'<a class="fn" href="#c{idx}" data-t="c{idx}">[{idx+1}]</a> '
            f'<span class="who">{user}</span></li>')

sections_html_parts = []
for si, (emoji, title, desc, ids, kind) in enumerate(SECTIONS):
    if not ids: continue
    bl = '\n'.join(bullet(i) for i in ids)
    sections_html_parts.append(f'''<details class="cat k-{kind}" id="sec-{si}">
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
sections_html = '\n'.join(sections_html_parts)

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

n_total = len(usable)
n_win = len(ids_for('outperform'))
n_mixed = len(ids_for('mixed'))
n_loss = len(ids_for('underperform'))
today = datetime.date(2026, 6, 10).strftime('%-d %b %Y')

chips = '\n'.join(
    f'<a class="chip ck-{kind}" href="#sec-{si}" data-jump="sec-{si}">{emoji} {t} <b>{len(ids)}</b></a>'
    for si, (emoji, t, _, ids, kind) in enumerate(SECTIONS) if ids)

page = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Did Fable 5 beat the field? — HN reports, categorized</title>
<style>
  :root {{
    --ink:#22201c; --mut:#7a7468; --acc:#d4502e; --acc-soft:#fbe9e2;
    --win:#1e7d4f; --win-soft:#e3f3ea; --loss:#a23333; --loss-soft:#f9e6e4;
    --mix:#8a6d1f; --mix-soft:#f7efd8;
    --bg:#f7f4ee; --card:#fffdf9; --line:#e7e0d2; --gold:#f1c40f;
    --shadow:0 1px 2px rgba(60,50,30,.06), 0 6px 18px rgba(60,50,30,.06);
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --ink:#ece7dd; --mut:#9b948a; --acc:#ff7a52; --acc-soft:#3a2620;
      --win:#5fd49a; --win-soft:#15301f; --loss:#ff8d7d; --loss-soft:#3a1d1a;
      --mix:#e0bf63; --mix-soft:#33290f;
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
  .hero h1 {{ font-family:Charter,Georgia,"Times New Roman",serif; font-size:clamp(30px,5vw,44px);
              line-height:1.12; margin:0 0 12px; letter-spacing:-.01em; }}
  .hero h1 em {{ color:var(--acc); font-style:normal; }}
  .hero .sub {{ color:var(--mut); margin:0 0 6px; max-width:68ch; }}
  .hero .sub strong {{ color:var(--ink); }}
  .stats {{ display:flex; gap:10px; flex-wrap:wrap; margin:20px 0 4px; }}
  .stat {{ background:var(--card); border:1px solid var(--line); border-radius:12px;
           padding:8px 16px; box-shadow:var(--shadow); font-size:13px; color:var(--mut); }}
  .stat b {{ display:block; font-size:21px; color:var(--ink); font-variant-numeric:tabular-nums; }}
  .stat.win b {{ color:var(--win); }} .stat.loss b {{ color:var(--loss); }} .stat.mix b {{ color:var(--mix); }}
  .chips {{ display:flex; gap:7px; flex-wrap:wrap; margin:22px 0 2px; }}
  .chip {{ font-size:12.5px; color:var(--ink); text-decoration:none; background:var(--card);
           border:1px solid var(--line); border-radius:999px; padding:4px 11px;
           transition:border-color .15s, transform .15s; }}
  .chip:hover {{ border-color:var(--acc); transform:translateY(-1px); }}
  .chip b {{ font-weight:700; margin-left:2px; }}
  .chip.ck-win b {{ color:var(--win); }} .chip.ck-loss b {{ color:var(--loss); }} .chip.ck-mixed b {{ color:var(--mix); }}
  .controls {{ position:sticky; top:0; z-index:10; display:flex; gap:10px; align-items:center;
               flex-wrap:wrap; padding:12px 0; margin-top:16px;
               background:color-mix(in srgb, var(--bg) 84%, transparent);
               backdrop-filter:blur(10px); -webkit-backdrop-filter:blur(10px);
               border-bottom:1px solid var(--line); }}
  #q {{ flex:1; min-width:210px; padding:10px 14px; font-size:15px; color:var(--ink);
        background:var(--card); border:1px solid var(--line); border-radius:12px; outline:none;
        transition:border-color .15s, box-shadow .15s; }}
  #q:focus {{ border-color:var(--acc); box-shadow:0 0 0 3px var(--acc-soft); }}
  .btn {{ font-size:12.5px; color:var(--mut); background:var(--card); border:1px solid var(--line);
          border-radius:9px; padding:6px 11px; cursor:pointer; transition:border-color .15s, color .15s; }}
  .btn:hover {{ border-color:var(--acc); color:var(--acc); }}
  #count {{ font-size:12.5px; color:var(--mut); font-variant-numeric:tabular-nums; }}
  details.cat {{ background:var(--card); border:1px solid var(--line); border-radius:16px;
                 margin:14px 0; box-shadow:var(--shadow); overflow:hidden; scroll-margin-top:76px; }}
  details.cat.k-win {{ border-left:4px solid var(--win); }}
  details.cat.k-loss {{ border-left:4px solid var(--loss); }}
  details.cat.k-mixed {{ border-left:4px solid var(--mix); }}
  details.cat summary {{ list-style:none; cursor:pointer; display:flex; align-items:center; gap:11px;
                         padding:15px 18px; user-select:none; }}
  details.cat summary::-webkit-details-marker {{ display:none; }}
  details.cat summary:hover {{ background:color-mix(in srgb, var(--acc-soft) 45%, transparent); }}
  .chev {{ color:var(--acc); font-size:14px; transition:transform .2s ease; flex:none; }}
  details[open] > summary .chev {{ transform:rotate(90deg); }}
  .emoji {{ font-size:19px; flex:none; }}
  summary .t {{ font-family:Charter,Georgia,serif; font-size:19px; font-weight:600; line-height:1.25; }}
  summary .n {{ margin-left:auto; flex:none; font-size:12.5px; font-weight:700; border-radius:999px;
                padding:2px 11px; font-variant-numeric:tabular-nums; background:var(--acc-soft); color:var(--acc); }}
  .k-win summary .n {{ background:var(--win-soft); color:var(--win); }}
  .k-loss summary .n {{ background:var(--loss-soft); color:var(--loss); }}
  .k-mixed summary .n {{ background:var(--mix-soft); color:var(--mix); }}
  details.cat .body {{ padding:2px 18px 14px; border-top:1px dashed var(--line); }}
  .desc {{ color:var(--mut); font-size:13.5px; margin:10px 0 6px; max-width:75ch; }}
  ul.bullets {{ margin:0; padding:0; list-style:none; }}
  ul.bullets li.b {{ padding:7px 6px 7px 22px; position:relative; border-radius:8px; }}
  ul.bullets li.b + li.b {{ border-top:1px solid color-mix(in srgb, var(--line) 55%, transparent); }}
  ul.bullets li.b:before {{ content:"\\2023"; position:absolute; left:6px; color:var(--acc); opacity:.7; }}
  ul.bullets li.b:hover {{ background:color-mix(in srgb, var(--acc-soft) 38%, transparent); }}
  ul.bullets li.b .who {{ color:var(--mut); font-size:12px; }}
  .vs {{ font-size:11px; font-weight:600; color:var(--mut); background:color-mix(in srgb, var(--line) 50%, transparent);
         border-radius:6px; padding:1px 7px; white-space:nowrap; }}
  a.fn {{ color:var(--acc); text-decoration:none; font-size:11.5px; vertical-align:super;
          font-weight:700; cursor:pointer; white-space:nowrap; }}
  a.fn:hover {{ text-decoration:underline; }}
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
    <h1>Did <em>Fable&nbsp;5</em> beat the field?</h1>
    <p class="sub">Every first-hand performance comparison in the Hacker News
    <em>&ldquo;Claude Fable 5&rdquo;</em> release thread &mdash; where commenters found Fable&nbsp;5
    <strong>outperforming</strong> other LLMs, where results were <strong>mixed</strong>, and, for balance,
    where it <strong>underperformed</strong>. Benchmark quotes, pricing chat and vibes without a comparison are excluded.
    Each bullet's footnote &mdash; <strong>hover</strong> to preview the full comment, <strong>click</strong> to jump. Built {today}.</p>
    <div class="stats">
      <div class="stat"><b>{n_total}</b> comments parsed</div>
      <div class="stat win"><b>{n_win}</b> outperformed</div>
      <div class="stat mix"><b>{n_mixed}</b> mixed</div>
      <div class="stat loss"><b>{n_loss}</b> underperformed</div>
    </div>
    <nav class="chips">
{chips}
    </nav>
  </header>

  <div class="controls">
    <input id="q" type="search" placeholder="Search comparisons — refactor, opus, codex, fallback…" autocomplete="off">
    <button class="btn" id="expand">Expand all</button>
    <button class="btn" id="collapse">Collapse all</button>
    <span id="count"></span>
  </div>

  {sections_html}

  <h2>Full comments</h2>
  <p class="secsub">The footnote targets &mdash; all {n_total} parsed comments in thread order (replies indented).</p>
  <div id="full">
  {full_html}
  </div>

  <footer>Source: a saved copy of the HN &ldquo;Claude Fable 5&rdquo; thread. Extraction, summaries and verdicts are
  LLM-generated &mdash; and yes, the model doing the summarizing is Fable&nbsp;5 itself, so follow the footnotes and
  judge the originals (see <a href="https://github.com/HaukeHillebrandt/oh-shit-genai">repo</a> for the pipeline).</footer>
</div>
<div id="tip"></div>
<script>
  const q=document.getElementById('q'), count=document.getElementById('count');
  const bullets=Array.from(document.querySelectorAll('li.b')), secs=Array.from(document.querySelectorAll('details.cat'));
  function run(){{
    const term=q.value.trim().toLowerCase(); let shown=0;
    bullets.forEach(b=>{{
      const ok=(!term||b.dataset.blob.includes(term));
      b.classList.toggle('hidden',!ok); if(ok)shown++;
    }});
    secs.forEach(s=>{{
      const any=s.querySelector('li.b:not(.hidden)');
      s.classList.toggle('hidden',!any);
      if(term && any) s.open=true;
    }});
    count.textContent=shown+' shown';
  }}
  q.addEventListener('input',run); run();
  secs.forEach((s,i)=>{{ if(i<7) s.open=true; }});  // open the win sections by default
  document.getElementById('expand').addEventListener('click',()=>secs.forEach(s=>s.open=true));
  document.getElementById('collapse').addEventListener('click',()=>secs.forEach(s=>s.open=false));
  document.querySelectorAll('.chip').forEach(a=>a.addEventListener('click',()=>{{
    const s=document.getElementById(a.dataset.jump); if(s) s.open=true;
  }}));
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

open('fable_vs_field.html', 'w', encoding='utf-8').write(page)
print('wrote fable_vs_field.html (', len(page)//1024, 'KB )')
print(f'win {n_win} / mixed {n_mixed} / loss {n_loss} of {n_total}')
for emoji, t, _, ids, kind in SECTIONS:
    if ids: print(f'  {len(ids):4d}  [{kind}] {html.unescape(t)}')
