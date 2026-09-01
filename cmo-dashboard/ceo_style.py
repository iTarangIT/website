"""The console's one stylesheet.

Two type systems, on purpose. Prose is set in the humanist sans and stays
generous; every measured figure — tiles, deltas, table cells, chart axes, counts —
is set in the tabular monospace and stays tight. This console is a reading surface
and a measuring instrument, and the two never wear the same clothes.

Palette is iTarang's existing green-on-warm-paper. Only one new value was added:
a clay accent, so the chart can carry a second series without borrowing a colour
that already means something.
"""

CSS = ''':root{
--ink:#17211d;--muted:#64706a;--faint:#8b948f;
--paper:#fffdf7;--bg:#edf1ed;--sheet:#ffffff;
--green:#176b4d;--green-soft:#e6f1eb;--green-deep:#0f4a35;
--clay:#a1552a;--clay-soft:#f6e9e0;
--line:#d9ded8;--line-soft:#e8ece7;
--red:#9d3030;--red-soft:#f7e4e4;--amber:#936414;--amber-soft:#fff3d6;
--radius:10px;--radius-sm:7px;--radius-xs:5px;
--pad:16px;--pad-tight:11px;--gap:12px;
--shadow:0 8px 30px #24352c12;--shadow-sm:0 1px 2px #24352c14;--shadow-pop:0 12px 34px #16241d26;
--tap:44px;
--mono:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,monospace;
--sans:ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;
--f-xs:11.5px;--f-sm:12.5px;--f-base:14.5px;--f-md:16px;--f-lg:19px;--f-xl:26px}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:var(--f-base)/1.55 var(--sans);
-webkit-text-size-adjust:100%}
main{max-width:1140px;margin:auto;padding:26px 20px 96px}
h1,h2,h3,h4,p,ul,ol{margin-top:0}
a{color:var(--green-deep)}

/* ---- numerals ------------------------------------------------------------ */
/* Every measured figure in the console shares one face and one alignment. */
.num,.tile-figure,.stat,td.n,th.n,.pager-count,.chart text,.delta,.funnel-retention,kbd{
font-family:var(--mono);font-variant-numeric:tabular-nums;font-feature-settings:"tnum" 1}
td.n,th.n{text-align:right}

/* ---- chrome -------------------------------------------------------------- */
.topbar{display:flex;align-items:center;gap:var(--pad)}
.topbar h1{margin:0;font-size:22px;letter-spacing:-.01em}
.topbar-title{min-width:0}.topbar .meta{margin-left:auto}
.eyebrow{margin:0 0 3px;color:var(--green);font-size:var(--f-xs);font-weight:800;
text-transform:uppercase;letter-spacing:.18em}
.mark{display:grid;place-items:center;width:44px;height:44px;flex:0 0 44px;border-radius:12px;
background:var(--green);color:#fff;font-size:19px;font-weight:800;letter-spacing:-.02em}
.paper{background:var(--paper);border:1px solid var(--line);border-radius:var(--radius);
padding:24px;box-shadow:var(--shadow)}
.login-wrap{min-height:100vh;display:grid;place-items:center}.login-card{width:min(440px,100%)}
nav.primary{position:relative;display:flex;gap:6px;margin:18px 0 4px}
.primary button{flex:1;text-align:left;border-color:transparent;background:transparent;color:var(--green)}
.primary button.active{background:var(--green-soft);color:var(--green-deep);border-color:var(--green-soft);font-weight:700}
.tab-indicator{position:absolute;left:0;bottom:-4px;height:2px;width:0;background:var(--green);
transition:transform .18s ease,width .18s ease}
.notice{margin:12px 0 0;color:var(--muted)}
.notice:empty{margin:0}
.notice.error{color:var(--red)}
kbd{display:inline-grid;place-items:center;min-width:19px;height:19px;margin-right:6px;padding:0 5px;
border:1px solid var(--line);border-bottom-width:2px;border-radius:4px;background:#ffffffcc;
color:var(--muted);font-size:11px;font-weight:600;line-height:1}
.screen{margin-top:14px}

/* ---- controls ------------------------------------------------------------ */
.field,label.field{display:block;margin:0;color:var(--muted);font-size:var(--f-sm)}
input,textarea,select{display:block;width:100%;padding:9px 10px;margin-top:4px;border:1px solid var(--line);
border-radius:var(--radius-sm);background:#fff;color:var(--ink);font:var(--f-base)/1.4 var(--sans)}
textarea{resize:vertical}
button{min-height:var(--tap);border:1px solid var(--green);background:var(--green);color:#fff;
padding:9px 14px;border-radius:var(--radius-sm);cursor:pointer;font:600 var(--f-base)/1.3 var(--sans)}
button:disabled{opacity:.5;cursor:not-allowed}
button:focus-visible,a:focus-visible,input:focus-visible,select:focus-visible,textarea:focus-visible,
summary:focus-visible,[tabindex]:focus-visible{outline:2px solid var(--green);outline-offset:2px}
.ghost{background:transparent;color:var(--green);border-color:var(--line)}
.ghost:hover:not(:disabled){border-color:var(--green)}
.danger{background:transparent;color:var(--red);border-color:#e0c4c4}
.small{min-height:34px;padding:5px 10px;font-size:var(--f-sm)}
.section-head,.dialog-head{display:flex;align-items:flex-start;justify-content:space-between;gap:var(--pad)}
/* Renaming an article, in the head of the card it belongs to. The console's first
   icon button: transparent, sized to the tap target, and coloured only on hover, so
   it reads as an affordance on the title rather than a second control competing
   with Close. `title-row` keeps it on the baseline of a heading that wraps. */
.title-row{display:flex;align-items:baseline;gap:8px;flex-wrap:wrap}
.icon-button{display:inline-flex;align-items:center;justify-content:center;
min-height:var(--tap);min-width:var(--tap);padding:0;border:0;border-radius:var(--radius-xs);
background:transparent;color:var(--muted);cursor:pointer}
.icon-button:hover:not(:disabled){color:var(--green);background:var(--line-soft)}
.icon-button:disabled{opacity:.45;cursor:not-allowed}
.icon-button[hidden]{display:none}
.title-form{margin-top:9px;max-width:60ch}
.title-form[hidden]{display:none}
.title-form .actions{margin-top:8px}
.section-head h2{margin:0 0 3px;font-size:var(--f-lg);letter-spacing:-.01em}
.section-head .meta{max-width:62ch}
h3.rule{margin:26px 0 10px;padding-top:16px;border-top:1px solid var(--line);font-size:var(--f-md)}
h3.rule .meta{display:block;margin-top:3px;font-size:var(--f-sm);font-weight:400}
.meta{color:var(--muted);font-size:var(--f-sm)}
.subject-box{display:flex;align-items:flex-end;gap:8px;margin:14px 0 6px}
.subject-box .field{flex:1;min-width:0}
.actions{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-top:10px}

/* Toolbar: search, filters, sort and count for one list. */
.toolbar{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:14px 0 10px;
padding-bottom:10px;border-bottom:1px solid var(--line-soft)}
.toolbar .search{flex:1 1 220px;min-width:0}
.toolbar .search input{margin-top:0}
.toolbar .count{margin-left:auto;color:var(--muted);font-size:var(--f-sm);white-space:nowrap}
.chips{display:flex;gap:6px;flex-wrap:wrap;align-items:center}
.chip{min-height:32px;padding:5px 11px;border:1px solid var(--line);border-radius:999px;
background:#fff;color:var(--muted);font:600 var(--f-sm)/1.3 var(--sans);cursor:pointer}
.chip:hover{border-color:var(--green)}
.chip[aria-pressed="true"]{background:var(--green);border-color:var(--green);color:#fff}
.chip .n{margin-left:5px;font-family:var(--mono);opacity:.75}
.chip-scroll{display:flex;gap:6px;overflow-x:auto;padding-bottom:2px;scrollbar-width:thin}
.chip-group{display:flex;align-items:center;gap:6px}
.chip-group>.label{color:var(--faint);font-size:var(--f-xs);font-weight:700;
text-transform:uppercase;letter-spacing:.1em;white-space:nowrap}

/* ---- one card grammar ---------------------------------------------------- */
/* A proposal, a blog row and an opportunity are the same object at different
   stages. Same radius, same hairline, same pill vocabulary, same rhythm. */
.rows{display:flex;flex-direction:column;gap:8px}
.card{position:relative;border:1px solid var(--line);border-radius:var(--radius-sm);background:#fff;
padding:var(--pad-tight) var(--pad);box-shadow:var(--shadow-sm)}
.card.is-focused{border-color:var(--green);box-shadow:0 0 0 2px var(--green-soft)}
.card.is-pending{opacity:.55}
.card-row{display:flex;align-items:flex-start;justify-content:space-between;gap:var(--pad)}
.card-main{min-width:0;flex:1}
.card h3{margin:5px 0 3px;font-size:var(--f-md);letter-spacing:-.005em;line-height:1.35}
.card .meta{margin:0}
.card button.open{min-height:0;background:transparent;color:var(--ink);border:0;padding:0;
text-align:left;width:100%;font-weight:400;font-size:inherit;cursor:pointer}
.card .actions{margin-top:9px}
/* Why a card is stuck, in the words that were written onto it. A failure reads
   in the failure colour, because a run that did not happen is not a neutral fact. */
.blog-reason{margin-top:6px!important;max-width:78ch}
.blog-reason.is-failure{color:var(--red)}
.blog-actions{display:flex;flex-wrap:wrap;gap:8px;margin-top:9px}
.blog-actions a.ghost{display:inline-flex;align-items:center;text-decoration:none}
.card-figures{display:flex;gap:14px;flex:0 0 auto;text-align:right}
.card-figures .stat{display:block;font-size:var(--f-md);font-weight:700;line-height:1.2}
.card-figures .label{display:block;color:var(--faint);font-size:var(--f-xs);
text-transform:uppercase;letter-spacing:.08em}
.pill{display:inline-flex;align-items:center;gap:5px;padding:2px 9px;border-radius:999px;
background:var(--green-soft);color:var(--green-deep);font-size:var(--f-xs);font-weight:700;
letter-spacing:.01em;vertical-align:middle}
.pill::before{content:attr(data-glyph)}
/* A beat is where a candidate came from, not how it is doing. Quieter than a
   status pill on purpose: it labels, it does not signal. */
.pill.beat{background:var(--line-soft);color:var(--muted);font-weight:600}
.radar-status{margin:0 0 8px;display:grid;gap:4px}
.radar-status p{margin:0;color:var(--muted);font-size:var(--f-sm)}
.pill.tone-wait{background:var(--amber-soft);color:var(--amber)}
.pill.tone-stop{background:var(--red-soft);color:var(--red)}
.pill.tone-mute{background:#eceeec;color:var(--muted)}
.source{font-weight:700;color:var(--green)}
.source-missing{color:var(--amber)}
/* A measured figure reads as normal meta; the absence of one is dimmed, so a
   glance down the list separates "we know" from "we have nothing yet". */
.demand{font-variant-numeric:tabular-nums}
.demand-none{color:var(--muted);font-style:italic}
.publish-date{margin:.75rem 0}
.publish-date input[type=date]{font:inherit;padding:.35rem .5rem;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:inherit}
.keywords{display:flex;flex-wrap:wrap;gap:4px;margin:7px 0}
.keywords .pill{background:#f1f4f1;color:var(--muted);font-weight:600}
.outline{margin:6px 0 0;max-width:70ch;color:var(--ink)}
.inline-form{margin-top:10px;padding:11px;background:#f3f6f3;border-radius:var(--radius-sm)}
.history-row{padding:7px 0;border-top:1px solid var(--line-soft)}
details{margin:14px 0}
summary{min-height:38px;display:flex;align-items:center;cursor:pointer;color:var(--green);
font-weight:700;font-size:var(--f-sm)}
.list-row{display:flex;align-items:center;justify-content:space-between;gap:var(--gap);
padding:9px var(--pad);border:1px solid var(--line);border-radius:var(--radius-sm);background:#fff}
.list-row .meta{margin:0}
/* An image slot is a row that has to hold a thumbnail, a description worth
   editing, and two controls — so it stacks rather than sitting on one line. */
.slot-row{display:block}
.slot-row .slot-main{display:flex;align-items:center;gap:10px;min-width:0}
.slot-row .slot-thumb{width:72px;height:41px;object-fit:cover;flex:none;
border-radius:var(--radius-sm);border:1px solid var(--line);background:var(--line)}
.slot-row .field{margin-top:9px}
.slot-row textarea,.slot-row input[type=text]{width:100%}
/* The cover sits above the first paragraph, visibly not part of the prose. */
.cover-strip{margin:0 0 22px}
.cover-strip.is-empty{display:flex;flex-direction:column;gap:4px;padding:18px var(--pad);
border:1px dashed var(--line);border-radius:var(--radius-sm);color:var(--muted);font-size:var(--f-sm)}

/* ---- empty and loading --------------------------------------------------- */
/* An empty panel is a state, not a failure. Neutral tone, one way forward. */
.empty{margin:0;padding:22px var(--pad);border:1px dashed var(--line);border-radius:var(--radius-sm);
background:#fafbfa;text-align:center;color:var(--muted)}
.empty strong{display:block;margin-bottom:3px;color:var(--ink);font-size:var(--f-base)}
.empty p{margin:0 auto;max-width:52ch}
.empty button{margin-top:12px}
.skeleton{border:1px solid var(--line-soft);border-radius:var(--radius-sm);
background:linear-gradient(90deg,#f4f6f4 25%,#eaeee9 37%,#f4f6f4 63%);background-size:400% 100%;
animation:shimmer 1.4s ease infinite}
.skeleton.card-h{height:112px}
.skeleton.row-h{height:44px}
.skeleton.tile-h{height:92px}
.skeleton.chart-h{height:200px}
@keyframes shimmer{0%{background-position:100% 0}100%{background-position:0 0}}

/* ---- a slow action, while it runs and when it fails ----------------------- */
/* The button that started it says what it is doing and how long it has been
   doing it. Disabled, but never faded to the point of looking broken. */
button[aria-busy="true"],button.is-busy{opacity:.82;cursor:progress;
font-variant-numeric:tabular-nums}
button[aria-busy="true"]::before,button.is-busy::before{content:"";display:inline-block;
width:11px;height:11px;margin-right:7px;vertical-align:-1px;border-radius:50%;
border:2px solid currentColor;border-top-color:transparent;animation:spin .8s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
/* A failure stays on screen where the results would have been. A toast that
   vanishes before it is read is the same as no message at all. */
.failure{margin:0;padding:16px var(--pad);border:1px solid var(--red);border-left-width:3px;
border-radius:var(--radius-sm);background:var(--red-soft);color:var(--ink)}
.failure strong{display:block;margin-bottom:3px}
.failure p{margin:0;color:var(--ink);overflow-wrap:anywhere}
.row-error,.form-error{margin:8px 0 0;padding:8px 11px;border-radius:var(--radius-xs);
background:var(--red-soft);color:var(--red);font-size:var(--f-sm);overflow-wrap:anywhere}
.row-error[hidden],.form-error[hidden]{display:none}

/* ---- work that arrived while he was looking somewhere else ---------------- */
/* Never jump him to it. Count it on the tab, or offer one line he can click. */
.tab-badge{display:inline-flex;align-items:center;justify-content:center;min-width:19px;
height:19px;margin-left:7px;padding:0 6px;border-radius:999px;background:var(--green);
color:#fff;font-family:var(--mono);font-size:var(--f-xs);font-variant-numeric:tabular-nums}
.tab-badge[hidden]{display:none}
.new-line{margin:10px 0 0}
.new-line[hidden]{display:none}
.new-line button{padding:6px 12px;min-height:0;border:1px solid var(--green);
border-radius:999px;background:var(--green-soft);color:var(--green-deep);
font-size:var(--f-sm);font-weight:600}
/* Someone else saved over the article he is editing. Say so; touch nothing. */
.editor-conflict{margin:0 0 10px;padding:10px 13px;border:1px solid var(--amber);
border-radius:var(--radius-sm);background:var(--amber-soft);color:var(--ink);
font-size:var(--f-sm)}
.editor-conflict[hidden]{display:none}

/* ---- pagination ---------------------------------------------------------- */
.pager{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-top:12px;
padding-top:10px;border-top:1px solid var(--line-soft)}
.pager-count{color:var(--muted);font-size:var(--f-sm)}
.pager .spacer{margin-left:auto}
.pager select{width:auto;margin-top:0;padding:5px 8px;font-size:var(--f-sm)}
.pager label{display:flex;align-items:center;gap:6px;font-size:var(--f-sm)}

/* ---- analytics ----------------------------------------------------------- */
.tiles{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px;margin:16px 0 4px}
.tile{padding:13px var(--pad);border:1px solid var(--line);border-radius:var(--radius-sm);
background:#fff;box-shadow:var(--shadow-sm)}
.tile-label{display:block;color:var(--faint);font-size:var(--f-xs);font-weight:700;
text-transform:uppercase;letter-spacing:.1em}
.tile-figure{display:block;margin-top:5px;font-size:var(--f-xl);font-weight:700;line-height:1.05;
letter-spacing:-.02em}
.tile-figure.absent{font-size:var(--f-md);font-weight:600;color:var(--faint);letter-spacing:0}
.delta{display:block;margin-top:3px;font-size:var(--f-xs);color:var(--muted)}
.delta.up{color:var(--green)}.delta.down{color:var(--clay)}
.chart-card{margin-top:14px;padding:var(--pad);border:1px solid var(--line);
border-radius:var(--radius-sm);background:#fff;box-shadow:var(--shadow-sm)}
.chart-head{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:10px}
.legend{display:flex;gap:12px;margin-left:auto;color:var(--muted);font-size:var(--f-sm)}
.legend span{display:inline-flex;align-items:center;gap:5px}
.legend i{width:9px;height:9px;border-radius:2px;background:var(--green)}
.legend i.clicks{background:var(--clay);border-radius:999px}
.chart-wrap{position:relative}
.chart{display:block;width:100%;height:auto;overflow:visible}
.chart text{fill:var(--faint);font-size:10px}
.chart .grid{stroke:var(--line-soft);stroke-width:1}
.chart .bar{fill:var(--green);opacity:.82}
.chart .bar:hover{opacity:1}
.chart .line{fill:none;stroke:var(--clay);stroke-width:2;stroke-linejoin:round;stroke-linecap:round}
.chart .dot{fill:var(--clay)}
.chart .hit{fill:transparent}
.chart .hit:hover,.chart .hit:focus-visible{fill:var(--green-soft);opacity:.5}
.tip{position:absolute;z-index:5;min-width:150px;padding:8px 10px;border-radius:var(--radius-xs);
background:var(--ink);color:#f2f6f3;font-size:var(--f-sm);box-shadow:var(--shadow-pop);
pointer-events:none;transform:translate(-50%,-100%)}
.tip[hidden]{display:none}
.tip b{display:block;margin-bottom:3px;font-family:var(--mono);font-weight:700}
.tip dl{display:grid;grid-template-columns:1fr auto;gap:1px 12px;margin:0}
.tip dd{margin:0;font-family:var(--mono);font-variant-numeric:tabular-nums;text-align:right}

/* The bridge between Analytics and Topics. The one control worth the trip. */
.opportunity{display:flex;align-items:flex-start;gap:var(--pad);padding:12px 12px 12px 14px;
border:1px solid var(--line);border-left:3px solid var(--green);border-radius:var(--radius-sm);
background:#fff;box-shadow:var(--shadow-sm)}
.opportunity.kind-page_two{border-left-color:var(--amber)}
.opportunity.kind-weak_title{border-left-color:var(--clay)}
.opportunity .card-main strong{display:block;font-size:var(--f-md);line-height:1.35}
.opportunity .why{margin:3px 0 0;color:var(--muted);max-width:66ch}
.opportunity .card-figures{align-self:center}
.opportunity button{white-space:nowrap;align-self:center}
.opportunity.is-queued{background:var(--green-soft);border-color:#cadfd3}

/* ---- tables -------------------------------------------------------------- */
.table-scroll{overflow-x:auto;-webkit-overflow-scrolling:touch}
table.data{width:100%;min-width:520px;border-collapse:collapse;font-size:var(--f-sm)}
table.data th,table.data td{padding:8px 10px;border-bottom:1px solid var(--line-soft);text-align:left;
vertical-align:top}
table.data thead th{position:sticky;top:0;z-index:1;background:var(--paper);color:var(--muted);
font-size:var(--f-xs);font-weight:700;text-transform:uppercase;letter-spacing:.08em;
border-bottom:1px solid var(--line);white-space:nowrap}
table.data tbody tr:hover{background:#f7f9f7}
table.data th button{min-height:0;padding:0;border:0;background:transparent;color:inherit;
font:inherit;text-transform:inherit;letter-spacing:inherit;cursor:pointer}
table.data th button::after{content:"";margin-left:5px;opacity:.35}
table.data th[aria-sort="ascending"] button::after{content:"\\2191";opacity:1}
table.data th[aria-sort="descending"] button::after{content:"\\2193";opacity:1}
table.data th[aria-sort]:not([aria-sort="none"]){color:var(--green-deep)}
table.data .subject{max-width:34ch;overflow-wrap:anywhere}
.footnote{margin:14px 0 0;padding-top:10px;border-top:1px solid var(--line-soft);
color:var(--faint);font-size:var(--f-xs)}

/* ---- dialog and reader --------------------------------------------------- */
dialog{width:min(940px,calc(100% - 32px));max-height:90vh;border:1px solid var(--line);
border-radius:12px;padding:0;background:var(--paper);color:var(--ink);box-shadow:var(--shadow-pop)}
dialog::backdrop{background:#112019b0}
.dialog-head{position:sticky;top:0;z-index:2;padding:18px 22px 12px;background:var(--paper);
border-bottom:1px solid var(--line-soft)}
.dialog-body{padding:0 22px 22px}
.nested{display:flex;gap:4px;margin:0 22px;border-bottom:1px solid var(--line)}
.nested button{min-height:40px;padding:8px 12px;border:0;border-bottom:2px solid transparent;
border-radius:0;background:transparent;color:var(--muted);font-weight:600}
.nested button.active{color:var(--green-deep);border-bottom-color:var(--green)}
/* A deliberate reading surface: a white sheet on the console's warm paper.
   It is the only place in the console that is not a list. */
.article-sheet{max-width:66ch;margin:18px auto 0;padding:38px 44px;background:var(--sheet);
border:1px solid var(--line);border-radius:2px;box-shadow:0 1px 0 #fff inset,0 10px 26px #1f2b2512;
font-size:var(--f-md);line-height:1.72}
.article-sheet>*:first-child{margin-top:0}
.article-sheet h1{margin:0 0 18px;font-size:29px;line-height:1.2;letter-spacing:-.018em}
.article-sheet h2{margin:34px 0 10px;font-size:20px;line-height:1.3;letter-spacing:-.01em}
.article-sheet h3{margin:26px 0 8px;font-size:var(--f-md)}
.article-sheet p,.article-sheet ul,.article-sheet ol{margin:0 0 17px}
.article-sheet li{margin:5px 0}
.article-sheet hr{margin:28px 0;border:0;border-top:1px solid var(--line)}
.article-sheet blockquote{margin:20px 0;padding:2px 0 2px 18px;border-left:2px solid var(--green);
color:var(--muted)}
.article-sheet code{padding:1px 4px;border-radius:3px;background:#f1f4f1;font:0.88em var(--mono)}
.article-sheet pre{padding:12px 14px;border-radius:var(--radius-xs);background:#f1f4f1;
overflow-x:auto;font-size:var(--f-sm)}
.article-sheet pre code{padding:0;background:none}
.article-sheet .image-omitted{color:var(--faint);font-style:italic}
.article-sheet figure{margin:26px 0}
.article-sheet .figure-frame{display:grid;place-items:center;min-height:120px;padding:8px;
background:#fbfcfb;border:1px solid var(--line-soft);border-radius:var(--radius-xs)}
.article-sheet .figure-frame.is-empty{gap:4px;min-height:130px;border:2px dashed var(--line);
color:var(--muted);font-size:var(--f-sm);text-align:center}
.article-sheet .figure-frame img{display:block;max-width:100%;height:auto}
.article-sheet figcaption{margin-top:9px;color:var(--muted);font-size:var(--f-sm);line-height:1.5}
.article-sheet .table-scroll{margin:22px 0}
table.prose-table{width:100%;min-width:440px;border-collapse:collapse;font-size:var(--f-sm)}
table.prose-table th,table.prose-table td{padding:8px 11px;border:1px solid var(--line);
text-align:left;vertical-align:top}
table.prose-table thead th{background:#f4f7f4;color:var(--ink);font-weight:700}
table.prose-table .align-right{text-align:right;font-family:var(--mono);font-variant-numeric:tabular-nums}
table.prose-table .align-center{text-align:center}
.reader-bar{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-top:14px}
.reader-bar .meta{margin-left:auto}
/* Review notes: scaffolding the writer left for its reviewers, out of the prose. */
.review-notes{max-width:66ch;margin:18px auto 0;border:1px solid var(--line);
border-radius:var(--radius-sm);background:#f7f9f7}
.review-notes summary{padding:11px var(--pad);min-height:var(--tap)}
.review-notes .body{padding:0 var(--pad) var(--pad);font-size:var(--f-base);line-height:1.6}
.review-notes h2{margin:16px 0 6px;font-size:var(--f-md)}
.review-notes h2:first-child{margin-top:0}
.review-notes .meta{margin:0 0 10px}
/* Process: one collapsible block per recorded stage. A stage still running is
   left open, because that is the one a reader opening the tab came to see. */
.stages{display:flex;flex-direction:column;gap:8px;margin-top:12px}
.stage{border:1px solid var(--line);border-radius:var(--radius-sm);background:#fff}
.stage[open]{background:#f7f9f7}
.stage summary{padding:11px var(--pad);min-height:var(--tap);display:flex;
align-items:center;gap:8px;flex-wrap:wrap}
.stage .body{padding:0 var(--pad) var(--pad)}
.stage .body>p:first-child{margin-top:0}
.stage-detail{display:grid;grid-template-columns:minmax(9rem,auto) 1fr;gap:4px 14px;
margin:10px 0;font-size:var(--f-sm)}
.stage-detail dt{color:var(--faint);font-weight:700}
.stage-detail dd{margin:0;white-space:pre-wrap;overflow-wrap:anywhere}
.stage .list-row .num{overflow-wrap:anywhere}
.editor{max-width:min(1000px,100%);margin-top:14px}
.editor-grid{display:grid;grid-template-columns:1fr 1fr;gap:var(--gap)}
.editor-pane{display:flex;flex-direction:column;min-height:0}
.editor-pane>.label{margin-bottom:5px;color:var(--faint);font-size:var(--f-xs);font-weight:700;
text-transform:uppercase;letter-spacing:.1em}
.editor textarea{flex:1;min-height:46vh;margin-top:0;font:13px/1.65 var(--mono);tab-size:2}
.editor .preview{flex:1;min-height:46vh;max-height:60vh;overflow:auto;padding:20px 22px;
border:1px solid var(--line);border-radius:var(--radius-sm);background:var(--sheet);
font-size:var(--f-base);line-height:1.65}
.editor .preview h1{font-size:22px}.editor .preview h2{font-size:17px}
.editor .preview .table-scroll{margin:14px 0}
.editor-bar{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-top:12px}
.editor-bar .meta{margin-left:auto}
.pipeline{border-left:3px solid var(--amber);padding:12px 16px;background:#fff8e8;
border-radius:var(--radius-xs)}
.pipeline dl{display:grid;grid-template-columns:max-content 1fr;gap:7px 16px;margin:10px 0 0}
.pipeline dt{color:var(--muted);font-size:var(--f-sm)}
.pipeline dd{margin:0;overflow-wrap:anywhere}
.publish{margin-top:14px;padding-top:12px;border-top:1px solid var(--line)}
table.evidence{width:100%;border-collapse:collapse;font-size:var(--f-sm)}
table.evidence th,table.evidence td{padding:6px 9px;border-bottom:1px solid var(--line-soft);text-align:left}
table.evidence td+td,table.evidence th+th{text-align:right;font-family:var(--mono)}

/* ---- toast --------------------------------------------------------------- */
.toast{position:fixed;left:50%;bottom:20px;z-index:30;max-width:min(560px,calc(100% - 32px));
padding:11px 16px;border-radius:var(--radius-sm);background:var(--ink);color:#f2f6f3;
box-shadow:var(--shadow-pop);opacity:0;transform:translate(-50%,10px);
transition:opacity .14s ease,transform .14s ease}
.toast.show{opacity:1;transform:translate(-50%,0)}
.toast.error{background:var(--red)}
.shortcuts{display:flex;flex-wrap:wrap;gap:14px;margin-top:26px;color:var(--faint);font-size:var(--f-xs)}
/* The build stamp. Diagnostic furniture, so it is quiet — but it never hides,
   least of all on the phone, which is where a stale console is hardest to spot. */
.build{display:flex;flex-wrap:wrap;align-items:center;gap:7px;margin:10px 0 0;
padding-top:9px;border-top:1px solid var(--line-soft);color:var(--faint);font-size:var(--f-xs)}
.build-label{font-weight:700;text-transform:uppercase;letter-spacing:.11em}
.build-value{font-family:var(--mono);font-variant-numeric:tabular-nums;
-webkit-user-select:all;user-select:all}
.build-sep{opacity:.5}
.visually-hidden{position:absolute;width:1px;height:1px;margin:-1px;padding:0;overflow:hidden;
clip:rect(0 0 0 0);white-space:nowrap;border:0}

/* ---- share bars ---------------------------------------------------------- */
/* One channel's share of sessions, drawn in the cell rather than in a legend.
   The number is still there in mono beside it -- the bar is for the ranking at a
   glance, never instead of the figure. */
.share-cell{display:flex;align-items:center;gap:9px;min-width:132px}
.share-bar{flex:1 1 auto;height:6px;border-radius:999px;background:var(--line-soft);overflow:hidden}
.share-bar i{display:block;height:100%;border-radius:999px;background:var(--green);
transition:width .18s ease}
.share-cell .num{flex:0 0 auto;min-width:44px;text-align:right}

/* ---- tiered analytics ---------------------------------------------------- */
/* The Search Console strip is five tiles and stays five. The Google Analytics
   strip is six and its drill-down is four, so the count is a modifier rather
   than a change to the shared default -- otherwise every strip on the tab
   reflows to suit whichever one grew last. */
.tiles.six{grid-template-columns:repeat(6,minmax(0,1fr))}
.tiles.four{grid-template-columns:repeat(4,minmax(0,1fr))}
/* Every rate on this tab shows what it was computed over. */
.tile-note{display:block;margin-top:3px;color:var(--faint);font-size:var(--f-xs);line-height:1.35}

/* New against returning, as one bar rather than two figures. */
.split{display:flex;align-items:center;gap:12px;margin:12px 0 2px;font-size:var(--f-sm);
color:var(--muted)}
.split-label b{color:var(--ink);font-family:var(--mono);font-variant-numeric:tabular-nums}
.split-bar{flex:1 1 auto;height:8px;border-radius:999px;background:var(--clay);overflow:hidden}
.split-bar i{display:block;height:100%;border-radius:999px 0 0 999px;background:var(--green)}

/* Drill-downs. Closed by default: the strip above is the answer, this is the
   working behind it. */
.drill{margin-top:14px;border-top:1px solid var(--line-soft);padding-top:10px}
.drill>summary{cursor:pointer;color:var(--green-deep);font-size:var(--f-sm);font-weight:700}
.drill>summary:focus-visible{outline:2px solid var(--green);outline-offset:3px;border-radius:3px}
.drill[open]>summary{margin-bottom:8px}

/* The funnel. A step with no event is drawn as an empty track, never a zero bar
   -- a full-width zero and an unwired step must not look alike. */
.funnel{list-style:none;margin:4px 0 0;padding:0;display:grid;gap:8px}
.funnel-step{display:grid;grid-template-columns:minmax(140px,1.1fr) minmax(90px,2fr) auto;
align-items:center;gap:10px;row-gap:2px}
.funnel-label{font-size:var(--f-sm);font-weight:600}
.funnel-bar{height:10px;border-radius:999px;background:var(--line-soft);overflow:hidden}
.funnel-bar i{display:block;height:100%;border-radius:999px;background:var(--green)}
.funnel-step.absent .funnel-label,.funnel-step.absent .num{color:var(--faint);font-weight:500}
.funnel-step.absent .funnel-bar{background:repeating-linear-gradient(135deg,
var(--line-soft) 0 5px,transparent 5px 10px)}
.funnel-step .num{min-width:64px;text-align:right;font-size:var(--f-sm)}
.funnel-retention{grid-column:2/-1;color:var(--faint);font-size:var(--f-xs)}
tr.is-intent td.subject{font-weight:700;color:var(--green-deep)}

/* The day-by-day trend. Engaged sessions are drawn inside the total, so the
   engaged bar sits on top of the same baseline rather than beside it. */
.chart.trend{height:150px}
.chart.trend .bar{fill:var(--clay);opacity:.35}
.chart.trend .bar.engaged{fill:var(--green);opacity:.9}
.legend i.engaged{background:var(--green)}
.source-examples{color:var(--faint);font-size:var(--f-xs);font-family:var(--mono)}

/* ---- social drafts ------------------------------------------------------- */
/* A draft is a card inside a card: it carries its own status pill, its own
   error strip and its own textarea, because the three platforms fail
   independently and a shared error line would say the wrong thing about two of
   them. Spacing and borders are the `.inline-form` grammar, not a new one. */
.drafts{display:flex;flex-direction:column;gap:10px;margin-top:11px}
.draft{border:1px solid var(--line);border-radius:var(--radius-sm);background:#fff;
padding:11px 13px}
.draft.is-queued{border-color:#cfe0d6;background:var(--green-soft)}
.draft.is-failed{border-color:#e6cccc;background:var(--red-soft)}
.draft-head{display:flex;align-items:center;justify-content:space-between;gap:9px;flex-wrap:wrap}
.draft-name{display:flex;align-items:center;gap:8px;font-weight:700;font-size:var(--f-sm)}
.draft-mark{width:20px;height:20px;border-radius:var(--radius-xs);flex:0 0 auto;
display:inline-flex;align-items:center;justify-content:center;color:#fff;
font-size:10px;font-weight:800;letter-spacing:0}
.draft-mark.linkedin{background:#0a66c2}
.draft-mark.x{background:#101418}
.draft-mark.instagram{background:linear-gradient(135deg,#c13584,#e1306c 55%,#f56040)}
.draft textarea{margin-top:8px;min-height:104px;font-size:var(--f-sm);line-height:1.55;resize:vertical}
.draft-foot{display:flex;align-items:center;justify-content:space-between;gap:9px;
flex-wrap:wrap;margin-top:8px}
.counter{font-family:var(--mono);font-variant-numeric:tabular-nums;color:var(--faint);
font-size:var(--f-xs)}
.counter.over{color:var(--red);font-weight:700}
.thread-item{display:flex;gap:8px;align-items:flex-start;padding:6px 0;
border-top:1px solid var(--line-soft)}
.thread-index{font-family:var(--mono);color:var(--faint);font-size:var(--f-xs);
padding-top:2px;flex:0 0 auto}
.thread-text{flex:1 1 auto;font-size:var(--f-sm);line-height:1.55;white-space:pre-wrap}
.draft-note{margin:7px 0 0;color:var(--muted);font-size:var(--f-xs)}
.send-bar{display:flex;align-items:center;gap:9px;flex-wrap:wrap;margin-top:11px;
padding-top:10px;border-top:1px solid var(--line)}
.send-bar .meta{margin-left:auto}

/* ---- print --------------------------------------------------------------- */
@media print{
body{background:#fff}body>*{display:none}
dialog[open]{display:block;position:static;max-height:none;width:100%;border:0;box-shadow:none;background:#fff}
.dialog-head,.nested,.reader-bar,.editor,.review-notes{display:none}
.article-sheet{max-width:none;margin:0;padding:0;border:0;box-shadow:none}
}

/* ---- phone --------------------------------------------------------------- */
@media(max-width:820px){
.tiles,.tiles.six,.tiles.four{grid-template-columns:repeat(2,minmax(0,1fr))}
.tiles .tile:first-child{grid-column:1/-1}
.editor-grid{grid-template-columns:1fr}
.editor textarea,.editor .preview{min-height:34vh}
}
@media(max-width:640px){
main{padding:14px 12px 88px}.paper{padding:15px}
.topbar{flex-wrap:wrap;gap:9px}.topbar h1{font-size:18px}
.topbar .meta{order:3;flex-basis:100%;margin-left:0}
.mark{width:38px;height:38px;flex-basis:38px;font-size:16px}
nav.primary{gap:3px}
.primary button{flex:1;min-width:0;padding:9px 6px;font-size:var(--f-sm);text-align:center;
overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.primary kbd{display:none}
.section-head{display:block}.section-head .meta{margin-top:5px}
#credit-meter{display:block;margin-top:8px}
.subject-box{display:block}.subject-box button{width:100%;margin-top:9px}
.toolbar{gap:7px}.toolbar .count{margin-left:0;flex-basis:100%}
.chips{flex-wrap:nowrap;overflow-x:auto;padding-bottom:3px}
/* Thumbs, not cursors: the small controls grow to a comfortable target. */
.chip{flex:0 0 auto;min-height:40px;padding:8px 13px}
.small{min-height:40px;padding:8px 12px}
.card-row{display:block}
.card-figures{margin-top:9px;gap:18px;text-align:left}
.card .actions button{flex:1 1 auto;min-width:calc(50% - 4px)}
.opportunity{display:block}
.opportunity .card-figures{margin-top:8px}
.opportunity button{width:100%;margin-top:10px}
.tiles,.tiles.six,.tiles.four{grid-template-columns:1fr 1fr;gap:8px}
.tile-figure{font-size:21px}
.legend{margin-left:0;flex-basis:100%}
.pager{gap:8px}.pager .spacer{margin-left:0;flex-basis:100%;height:0}
.list-row{display:block}.list-row button{width:100%;margin-top:8px}
.draft-head{align-items:flex-start}
.send-bar{display:block}.send-bar button{width:100%;margin-top:8px}
.send-bar .meta{display:block;margin:8px 0 0}
.share-cell{min-width:0}
.pipeline dl{display:block}.pipeline dt{margin-top:8px}
.shortcuts{display:none}
.build{margin-top:16px;gap:6px}
dialog{width:100%;max-width:none;max-height:100dvh;height:100dvh;margin:0;border:0;border-radius:0}
.dialog-head{padding:14px 15px 10px}.nested{margin:0 15px;overflow-x:auto}
.nested button{white-space:nowrap}
.dialog-body{padding:0 15px 20px}
.article-sheet{margin-top:14px;padding:20px 17px;font-size:15.5px;border-radius:0}
.article-sheet h1{font-size:23px}.article-sheet h2{font-size:18px}
.review-notes{margin-top:14px}
.tip{position:fixed;left:12px;right:12px;bottom:12px;top:auto;min-width:0;transform:none}
}
@media(prefers-reduced-motion:reduce){
*,*::before,*::after{animation-duration:.001ms!important;animation-iteration-count:1!important;
transition-duration:.001ms!important;scroll-behavior:auto!important}
}'''

# Compatibility for existing page modules; new pages import CSS.
STYLE = CSS
