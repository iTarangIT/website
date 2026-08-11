CSS = ''':root{
--ink:#17211d;--muted:#64706a;--paper:#fffdf7;--green:#176b4d;--green-soft:#e6f1eb;
--line:#d9ded8;--bg:#edf1ed;--red:#9d3030;--red-soft:#f7e4e4;--amber:#936414;--amber-soft:#fff3d6;
--radius:10px;--radius-sm:7px;--pad:16px;--gap:12px;
--shadow:0 8px 30px #24352c12;--shadow-sm:0 1px 2px #24352c14;
--tap:44px}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 ui-sans-serif,system-ui,sans-serif}
main{max-width:1120px;margin:auto;padding:28px 20px 80px}
h1,h2,h3,h4,p{margin-top:0}
h3.rule{margin:26px 0 10px;padding-top:18px;border-top:1px solid var(--line);font-size:15px}
.topbar{display:flex;align-items:center;gap:var(--pad)}
.topbar h1{margin:0;font-size:22px}.topbar-title{min-width:0}.topbar .meta{margin-left:auto}
.eyebrow{margin:0 0 4px;color:var(--green);font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:.17em}
.paper{background:var(--paper);border:1px solid var(--line);border-radius:var(--radius);padding:26px;box-shadow:var(--shadow)}
.login-wrap{min-height:100vh;display:grid;place-items:center}.login-card{width:min(440px,100%)}
.mark{display:grid;place-items:center;width:46px;height:46px;flex:0 0 46px;border-radius:12px;background:var(--green);color:white;font-size:20px;font-weight:800}
.field,label{display:block;margin:12px 0;color:var(--muted)}
input,textarea,select{display:block;width:100%;padding:10px;margin-top:5px;border:1px solid var(--line);border-radius:var(--radius-sm);background:white;color:var(--ink);font:inherit}
textarea{resize:vertical}
button{min-height:var(--tap);border:1px solid var(--green);background:var(--green);color:white;padding:9px 14px;border-radius:var(--radius-sm);cursor:pointer;font:inherit}
button:disabled{opacity:.55;cursor:not-allowed}
button:focus-visible,a:focus-visible,input:focus-visible,select:focus-visible,textarea:focus-visible,summary:focus-visible{outline:2px solid var(--green);outline-offset:2px}
.ghost,nav button:not(.active){background:transparent;color:var(--green)}
.danger{background:transparent;color:var(--red);border-color:var(--red)}
/* One tab bar, one sliding indicator. Motion is functional: it shows which tab you left. */
nav.primary{position:relative;display:flex;gap:6px;margin:20px 0}
.primary button{flex:1;text-align:left;border-color:transparent}
.primary button.active{background:var(--green-soft);color:var(--green);border-color:var(--green-soft)}
.tab-indicator{position:absolute;left:0;bottom:-1px;height:2px;width:0;background:var(--green);transition:transform .18s ease,width .18s ease}
kbd{display:inline-grid;place-items:center;min-width:20px;height:20px;margin-right:6px;padding:0 5px;border:1px solid var(--line);border-bottom-width:2px;border-radius:4px;background:#ffffffcc;color:var(--muted);font:600 11px/1 ui-monospace,monospace}
.section-head,.dialog-head{display:flex;align-items:flex-start;justify-content:space-between;gap:var(--pad)}
/* ---- one card grammar: proposals, blog rows and competitor findings share it ---- */
.rows{display:flex;flex-direction:column;gap:10px}
.card{border:1px solid var(--line);border-radius:var(--radius-sm);background:white;padding:var(--pad);box-shadow:var(--shadow-sm)}
.card.is-focused{border-color:var(--green);box-shadow:0 0 0 2px var(--green-soft)}
.card.is-pending{opacity:.6}
.card-row{display:flex;align-items:flex-start;justify-content:space-between;gap:var(--pad)}
.card h3{margin:6px 0 4px;font-size:16px}
.card button.open{min-height:0;background:transparent;color:var(--ink);border:0;padding:0;text-align:left;width:100%}
.meta,.empty,.notice{color:var(--muted)}
.notice.error,.meta.error{color:var(--red)}
.empty{margin:0;padding:22px var(--pad);border:1px dashed var(--line);border-radius:var(--radius-sm);text-align:center}
.empty strong{display:block;margin-bottom:4px;color:var(--ink)}
.empty button{margin-top:10px}
.actions,.controls,.keyword-box,.subject-box{display:flex;align-items:flex-end;gap:8px;flex-wrap:wrap;margin-top:10px}
.controls label{min-width:150px;margin:0}
.keyword-box .field,.subject-box .field{flex:1;min-width:200px;margin:0}
/* Status is colour plus a glyph plus a word — never colour alone. */
.pill{display:inline-flex;align-items:center;gap:5px;padding:3px 9px;border-radius:999px;background:var(--green-soft);color:var(--green);font-size:12px;font-weight:600}
.pill::before{content:attr(data-glyph)}
.pill.tone-wait{background:var(--amber-soft);color:var(--amber)}
.pill.tone-stop{background:var(--red-soft);color:var(--red)}
.pill.tone-mute{background:#eceeec;color:var(--muted)}
.source{font-weight:700;color:var(--green)}.source-missing{color:var(--red)}
.keywords{display:flex;flex-wrap:wrap;gap:5px;margin:8px 0}
.outline{margin:8px 0;max-width:68ch}
.inline-form{margin-top:10px;padding:12px;background:#f2f5f2;border-radius:var(--radius-sm)}
.inline-form .field{margin:0}
.history-row{padding:8px 0;border-top:1px solid var(--line)}
details{margin:14px 0}summary{min-height:var(--tap);display:flex;align-items:center;cursor:pointer;color:var(--green);font-weight:700}
.analytics-grid{display:grid;grid-template-columns:1fr 1fr;gap:var(--gap);margin-top:22px}
.tile{border:1px solid var(--line);border-radius:var(--radius-sm);background:white;padding:18px;box-shadow:var(--shadow-sm)}
.metrics{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
.metric{padding:12px;background:#f2f5f2;border-radius:var(--radius-sm)}
.metric strong{display:block;font-size:20px}
.delta{font-size:12px;color:var(--green)}
dl{display:grid;grid-template-columns:max-content 1fr;gap:8px 16px}dt{color:var(--muted)}dd{margin:0}
dialog{width:min(920px,calc(100% - 32px));max-height:90vh;border:1px solid var(--line);border-radius:12px;padding:24px;background:var(--paper);color:var(--ink)}
dialog::backdrop{background:#112019a8}
.nested{display:flex;gap:6px;border-bottom:1px solid var(--line)}
/* The reader stays generous; the lists above stay tight. */
.article-sheet{max-width:720px;margin:auto;padding:32px;background:white;border:1px solid var(--line);box-shadow:0 8px 24px #1f2b2510;font-size:16px;line-height:1.7}
.article-sheet.dark{background:#17211d;color:#eef4ef;border-color:#394b42}
.article-sheet img{display:block;max-width:100%;height:auto;margin:18px auto}
.article-sheet pre{white-space:pre-wrap;font:inherit}
.image-slot{display:grid;place-items:center;min-height:180px;margin:18px 0;padding:20px;border:2px dashed var(--line);text-align:center;color:var(--muted)}
.pipeline{border-left:4px solid var(--amber);padding:12px 16px;background:#fff8e8}
.file-row,.trend-row,.watch-row{display:flex;align-items:center;justify-content:space-between;gap:var(--gap);padding:10px var(--pad);border:1px solid var(--line);border-radius:var(--radius-sm);background:white}
/* Skeletons at real row height so nothing jumps when data lands. */
.skeleton{height:104px;border:1px solid var(--line);border-radius:var(--radius-sm);background:linear-gradient(90deg,#f4f6f4 25%,#eaeee9 37%,#f4f6f4 63%);background-size:400% 100%;animation:shimmer 1.4s ease infinite}
.skeleton.row{height:52px}
@keyframes shimmer{0%{background-position:100% 0}100%{background-position:0 0}}
.toast{position:fixed;left:50%;bottom:22px;transform:translate(-50%,8px);z-index:20;max-width:min(560px,calc(100% - 32px));padding:12px 16px;border-radius:var(--radius-sm);background:var(--ink);color:#f2f6f3;box-shadow:0 10px 30px #12201a40;opacity:0;transition:opacity .14s ease,transform .14s ease}
.toast.show{opacity:1;transform:translate(-50%,0)}
.toast.error{background:var(--red)}
.shortcuts{display:flex;flex-wrap:wrap;gap:14px;margin-top:26px;color:var(--muted);font-size:12px}
.gap-kind{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:12px}
table.evidence{width:100%;border-collapse:collapse}
table.evidence th,table.evidence td{padding:6px 8px;border-bottom:1px solid var(--line);text-align:left}
@media print{body{background:white}body>*{display:none}dialog[open]{display:block;position:static;max-height:none;width:100%;border:0}.dialog-head,.nested,.reader-actions{display:none}.article-sheet{border:0;box-shadow:none;max-width:none}}
@media(max-width:760px){
main{padding:16px 12px 90px}.paper{padding:16px}
.topbar{flex-wrap:wrap;gap:10px}.topbar h1{font-size:19px}.topbar .meta{margin-left:0;flex-basis:100%;order:3}
nav.primary{gap:4px}.primary button{flex:1;min-width:0;padding:9px 8px;font-size:13px;text-align:center}.primary kbd{display:none}
.analytics-grid,.metrics{grid-template-columns:1fr}
.card-row,.section-head{display:block}.section-head .meta{display:block;margin-top:6px}
.actions{gap:6px}.actions button{flex:1 1 auto;min-width:calc(50% - 3px)}
dl{display:block}dt{margin-top:9px}
.keyword-box,.subject-box{display:block}.subject-box button{width:100%;margin-top:8px}
.article-sheet{padding:18px;font-size:15px}
.file-row,.trend-row,.watch-row{display:block}.watch-row button{margin-top:8px;width:100%}
.shortcuts{display:none}
dialog{width:100%;max-width:none;max-height:100vh;margin:0;border-radius:0;padding:16px}
}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{animation-duration:.001ms!important;animation-iteration-count:1!important;transition-duration:.001ms!important}}'''

# Compatibility for existing page modules; new pages import CSS.
STYLE = CSS
