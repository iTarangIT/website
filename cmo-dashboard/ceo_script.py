SCRIPT = r'''const $=selector=>document.querySelector(selector);
const $$=selector=>[...document.querySelectorAll(selector)];
const esc=value=>String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
/* Tab order is the order the work happens, and it is fixed. The stored UI state
   below deliberately does not include the tab: every load opens on Topics. */
const VIEWS=['topics','blogs','analytics','social','archived'];
const DEFAULT_VIEW='topics';
let token=sessionStorage.getItem('cmo_token')||'';
let email=sessionStorage.getItem('cmo_email')||'';
let role=sessionStorage.getItem('cmo_role')||'';
let state=null;
let currentView=DEFAULT_VIEW;
let openTask=null;
let detailTab='read';
let blogPublishRequest='';
/* One prepared send instruction per article, keyed by task id. Minted by
   /ceo/social-check and spent by one press of Approve & schedule; a card that
   is re-prepared replaces its own entry rather than accumulating tokens. */
const socialPlans={};
/* An action he started normally owns the screen until it finishes, and the
   poller stands down for the whole of it. The news sweep has to be the
   exception. Its triager alone is allowed ten minutes, it researches up to
   three subjects after that, and it commits each subject's candidates before
   starting the next — so standing down for the duration is what made a sweep
   that was working look like a page that had frozen, and a request that died
   on the way back took the whole result with it. */
let liveWhileBusy=false;
let busy=false;
let focusIndex=-1;
let editing=false;
let editorText='';
/* The text the editor opened with. Three-way, not two: "he changed it" and "they
   changed it" are different questions, and only comparing both answers them. */
let editorBase='';
let previewTimer=0;

/* ------------------------------------------------------- staying up to date */
/* One mechanism, not two. A tiny token is polled; the whole state is refetched
   only when that token moves. The old blind 60-second reload is gone — two
   refreshers fighting each other is worse than either alone. */
const POLL_LADDER=[3000,6000,12000,30000];
let versionToken='';
let pollStep=0;
let pollTimer=0;
/* Cards that arrived from somewhere else and he has not been shown yet. He is
   never jumped to them; they are counted on the tab, or offered as one line. */
const fresh={topics:new Set(),blogs:new Set()};

/* ------------------------------------------------------- persisted list state */
/* Sort, filter, search, page and page size survive the quiet 60-second reload.
   A filter that resets is worse than no filter. */
const UI_KEY='cmo_console_ui_v2';
const UI_DEFAULTS={
 topics:{page:1,size:10,search:'',filter:'all'},
 blogs:{page:1,size:10,search:'',filter:'all'},
 archived:{page:1,size:10,search:'',filter:'all'},
 social:{page:1,size:10,search:'',filter:'all'},
 trends:{page:1,size:10},
 opportunities:{page:1,size:10},
 queries:{page:1,size:25,sort:'impressions',dir:'desc'},
 pages:{page:1,size:25,sort:'impressions',dir:'desc'},
 posts:{page:1,size:25,sort:'impressions',dir:'desc'},
 competitor:{page:1,size:10},
 analytics:{range:'28',device:'all',start:'',end:'',metric:'traffic'}
};
function loadUi(){
 let stored={};
 try{stored=JSON.parse(localStorage.getItem(UI_KEY)||'{}');}catch(error){stored={};}
 const merged={};
 for(const key of Object.keys(UI_DEFAULTS))merged[key]={...UI_DEFAULTS[key],...(stored[key]||{})};
 return merged;
}
let ui=loadUi();
function saveUi(){try{localStorage.setItem(UI_KEY,JSON.stringify(ui));}catch(error){/* private mode */}}
function setUi(key,patch,resetPage=true){
 Object.assign(ui[key],patch);
 if(resetPage&&!('page' in patch)&&'page' in ui[key])ui[key].page=1;
 saveUi();
}

function expire(){
 sessionStorage.removeItem('cmo_token');sessionStorage.removeItem('cmo_email');sessionStorage.removeItem('cmo_role');
 location.replace('/?msg=expired');
}
async function api(path,options={}){
 const raw=Boolean(options.raw);delete options.raw;
 options.headers={...(options.headers||{}),Authorization:'Bearer '+token};
 const response=await fetch(path,options);
 if(response.status===401||response.status===403){expire();throw Error('Your session ended');}
 if(raw){if(!response.ok)throw Error(response.statusText||'Request failed');return response;}
 const payload=await response.json().catch(()=>({error:response.statusText}));
 if(!response.ok)throw Error(payload.error||response.statusText||'Request failed');
 return payload;
}
function post(path,body){return api(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});}
function notice(message,error=false){const node=$('#notice');node.textContent=message||'';node.classList.toggle('error',error);}

/* Re-rendering identical markup steals focus and scroll for nothing. */
const painted=new WeakMap();
function setHtml(node,html){
 if(!node||painted.get(node)===html)return false;
 painted.set(node,html);node.innerHTML=html;return true;
}

/* ------------------------------------------------------------ keyed patching */
/* A background update replaces the rows that changed and nothing else. Blowing a
   whole list away with innerHTML is what makes an auto-updating page feel like it
   is fighting you: the scroll jumps, an open <details> snaps shut, and whatever
   had focus loses it. Rows carry data-key; a row whose markup is byte-identical
   to last time is not touched at all. */
const rowState=new WeakMap();
function canPatch(node){
 return Boolean(node&&node.children&&typeof node.insertBefore==='function'
  &&typeof node.removeChild==='function'&&typeof node.replaceChild==='function');
}
function makeRow(html){
 const stage=document.createElement('div');
 stage.innerHTML=html;
 return stage.firstElementChild;
}
function rowKey(node){return node&&node.getAttribute?node.getAttribute('data-key'):null;}
function patchRows(host,entries,fallback){
 if(!host)return;
 if(!entries.length||!canPatch(host)){
  /* Empty state, or a host that cannot be patched: one honest full paint. */
  rowState.set(host,new Map(entries.map(entry=>[entry.key,entry.html])));
  setHtml(host,entries.length?entries.map(entry=>entry.html).join(''):(fallback||''));
  return;
 }
 painted.delete(host);
 const previous=rowState.get(host)||new Map();
 const standing=new Map();
 [...host.children].forEach(node=>{const key=rowKey(node);if(key!==null)standing.set(key,node);});
 const next=new Map();
 entries.forEach((entry,index)=>{
  let node=standing.get(entry.key);
  if(!node||previous.get(entry.key)!==entry.html){
   const replacement=makeRow(entry.html);
   if(replacement&&node)host.replaceChild(replacement,node);
   if(replacement)node=replacement;
  }
  next.set(entry.key,entry.html);
  if(!node)return;
  const occupant=host.children[index];
  if(occupant!==node)host.insertBefore(node,occupant||null);
 });
 [...host.children].forEach(node=>{
  const key=rowKey(node);
  if(key===null||!next.has(key))host.removeChild(node);
 });
 rowState.set(host,next);
}

/* --------------------------------------------------- a slow action, visibly */
/* Tens of seconds pass between pressing this and anything arriving. For that
   whole time the button has to say what it is doing and how long it has been
   doing it, and a skeleton has to hold the space the results will fill, so the
   layout does not jump when they do. Every slow action on this console goes
   through here — there is no second way to look busy. */
function nodeOf(target){return typeof target==='string'?$(target):target||null;}
function runAction({button,label,slot,surface,shape='card-h',count=1,failTitle='That did not run.'}){
 const control=nodeOf(button);
 const place=nodeOf(slot);
 const line=nodeOf(surface);
 const original=control?control.textContent:'';
 const started=Date.now();
 let failed=false;
 const paint=()=>{
  if(control)control.textContent=`${label} ${Math.floor((Date.now()-started)/1000)}s`;
 };
 if(control){control.disabled=true;control.classList.add('is-busy');control.setAttribute('aria-busy','true');}
 paint();
 const ticker=setInterval(paint,1000);
 const placed=skeleton(count,shape);
 if(place){place.hidden=false;place.innerHTML=placed;painted.delete(place);}
 /* Clear the last failure, and only that: whatever the caller just wrote on this
    line to say what it is doing stays where it is. */
 if(line&&line.classList.contains('error')){line.textContent='';line.classList.remove('error');line.hidden=true;}
 busy=true;
 return {
  fail(message){
   failed=true;
   const text=String(message||'This did not say why it failed.');
   if(place){
    place.hidden=false;
    place.innerHTML=`<div class="failure" role="alert"><strong>${esc(failTitle)}</strong><p>${esc(text)}</p></div>`;
    painted.delete(place);
   }
   if(line){line.textContent=text;line.classList.add('error');line.hidden=false;}
   if(!place&&!line)toast(text,true);
  },
  done(){
   clearInterval(ticker);
   busy=false;
   if(control){
    control.textContent=original;control.disabled=false;
    control.classList.remove('is-busy');control.removeAttribute('aria-busy');
   }
   /* A failure stays on screen. Only a success clears the space it was using —
      and only if the skeleton is still what is in it: when the results render
      into the same node, taking it down again would blank the answer. */
   if(place&&!failed&&place.innerHTML===placed){place.hidden=true;place.innerHTML='';painted.delete(place);}
  }
 };
}

/* ----------------------------------------------------------------- vocabulary */
const STATUS={
 proposed:{glyph:'●',label:'awaiting you',tone:'tone-wait'},
 revising:{glyph:'↻',label:'re-researching',tone:'tone-wait'},
 approved:{glyph:'✓',label:'approved',tone:''},
 carded:{glyph:'✓',label:'queued for writing',tone:''},
 rejected:{glyph:'✗',label:'rejected',tone:'tone-stop'},
 archived:{glyph:'▤',label:'archived',tone:'tone-mute'},
 'awaiting decision':{glyph:'●',label:'awaiting you',tone:'tone-wait'},
 /* The blog chain, start to finish, in one editorial vocabulary: draft, being
    edited, waiting for review, approved, scheduled, published. Three of these
    keys are drafts at different depths and two are waiting for a reader at
    different desks; the key stays as it was so the tones and the filter chips
    keep working, and only the words a human reads were unified.

    `published` is a Gate 2 merge. `in_preview` is the branch it sits on until
    then -- the two used to be one word, and it was the wrong one. */
 queued:{glyph:'○',label:'draft — queued to be written',tone:'tone-mute'},
 researching:{glyph:'◐',label:'draft — researching',tone:'tone-wait'},
 writing:{glyph:'◑',label:'draft — writing',tone:'tone-wait'},
 failed:{glyph:'✗',label:'could not be written',tone:'tone-stop'},
 held:{glyph:'‖',label:'on hold',tone:'tone-mute'},
 checking:{glyph:'◇',label:'waiting for review',tone:'tone-wait'},
 awaiting_you:{glyph:'●',label:'waiting for review',tone:'tone-wait'},
 rewriting:{glyph:'↻',label:'being edited',tone:'tone-wait'},
 scheduled:{glyph:'◷',label:'scheduled',tone:''},
 in_preview:{glyph:'◎',label:'in preview',tone:'tone-wait'},
 published:{glyph:'▲',label:'published',tone:''},
 uncontested:{glyph:'◆',label:'uncontested',tone:''},
 weak_position:{glyph:'▲',label:'we rank weakly',tone:'tone-wait'},
 covered:{glyph:'✓',label:'we hold this',tone:'tone-mute'},
 unclicked:{glyph:'◆',label:'seen, never clicked',tone:'tone-wait'},
 page_two:{glyph:'▲',label:'page two',tone:'tone-wait'},
 weak_title:{glyph:'○',label:'ranks but loses the click',tone:'tone-mute'},
 rising:{glyph:'↑',label:'rising',tone:''},
 /* A cross-post's life. `draft` is copy nobody has sent; `queued` means Buffer
    holds a post id for it and it will go out in a scheduled slot; `failed` is a
    refusal Buffer gave, kept on the row with its reason. */
 draft:{glyph:'○',label:'not sent',tone:'tone-mute'},
 queued:{glyph:'◷',label:'queued in Buffer',tone:''},
 failed_send:{glyph:'✗',label:'Buffer refused it',tone:'tone-stop'}
};
function pill(key,override){const item=STATUS[key]||{glyph:'●',label:key||'unknown',tone:'tone-mute'};
 return `<span class="pill ${item.tone}" data-glyph="${item.glyph}">${esc(override||item.label)}</span>`;}

let toastTimer=0;
function toast(message,error=false){
 const node=$('#toast');node.textContent=message;node.classList.toggle('error',error);
 node.hidden=false;requestAnimationFrame(()=>node.classList.add('show'));
 clearTimeout(toastTimer);toastTimer=setTimeout(()=>{node.classList.remove('show');setTimeout(()=>{node.hidden=true;},220);},3200);
}
function skeleton(count,shape){return Array.from({length:count},()=>`<div class="skeleton ${shape}"></div>`).join('');}
function emptyState(title,text,actionLabel,actionAttribute){
 return `<div class="empty"><strong>${esc(title)}</strong><p>${esc(text)}</p>${actionLabel?`<button class="ghost" ${actionAttribute} type="button">${esc(actionLabel)}</button>`:''}</div>`;
}
const grouped=new Intl.NumberFormat('en-IN');
/* A figure that has not been measured says so. It never reads as zero. */
function figure(value,kind){
 if(value===null||value===undefined||value==='')return null;
 if(kind==='ctr')return Number(value).toFixed(2)+'%';
 if(kind==='position')return Number(value).toFixed(1);
 return typeof value==='number'?grouped.format(value):String(value);
}
function cell(value,kind){const text=figure(value,kind);return text===null?'—':esc(text);}
function deltaHtml(value,kind){
 if(value===null||value===undefined)return '';
 const better=kind==='position'?value<0:value>0;
 const worse=kind==='position'?value>0:value<0;
 const shown=(value>0?'+':'')+(kind==='ctr'||kind==='position'?Number(value).toFixed(kind==='position'?1:2):grouped.format(value));
 return `<span class="delta ${better?'up':worse?'down':''}">${esc(shown)} vs previous window</span>`;
}
function findTask(id){return (state?.blogs||[]).find(item=>item.id===id);}

/* ------------------------------------------------- work that arrived elsewhere */
function idsIn(snapshot){
 return {
  topics:new Set((((snapshot||{}).topics||{}).proposals||[]).map(item=>String(item.id))),
  blogs:new Set(((snapshot||{}).blogs||[]).map(task=>String(task.id)))
 };
}
/* Something appeared while he was looking at a different tab, or a different
   page of this one. Remember it; do not move him to it. */
function markArrivals(before,after){
 const was=idsIn(before),now=idsIn(after);
 for(const view of ['topics','blogs'])
  for(const id of now[view])if(!was[view].has(id))fresh[view].add(id);
}
/* Once a card is actually on screen it is no longer news. */
function settleArrivals(view,shownIds){
 if(currentView===view)shownIds.forEach(id=>fresh[view].delete(String(id)));
}
function paintArrivals(){
 for(const view of ['topics','blogs']){
  const count=fresh[view].size;
  const badge=document.querySelector(`[data-badge="${view}"]`);
  if(badge){
   badge.hidden=!count||currentView===view;
   badge.textContent=count?String(count):'';
  }
  const line=$(`#${view}-new`);
  if(!line)continue;
  const offer=Boolean(count)&&currentView===view;
  line.hidden=!offer;
  if(offer)setHtml(line,`<button data-arrivals="${view}" type="button">${grouped.format(count)} new — show ${count===1?'it':'them'}</button>`);
 }
}
/* He clicked the line. Clearing the filter and the search is the only thing that
   can be guaranteed to bring the new cards into view. */
function showArrivals(view){
 setUi(view,{search:'',filter:'all',page:1});
 const box=$(`#${view}-search`);if(box)box.value='';
 showView(view);renderAll();
}

/* ------------------------------------------------------------------- paging */
function page(items,key){
 const config=ui[key];
 const size=Number(config.size)||10;
 const total=items.length;
 const pages=Math.max(1,Math.ceil(total/size));
 if(config.page>pages){config.page=pages;saveUi();}
 const current=Math.min(Math.max(1,Number(config.page)||1),pages);
 return {items:items.slice((current-1)*size,current*size),total,pages,current,size};
}
function renderPager(id,key,view,noun){
 const node=$(id);if(!node)return;
 if(view.total<=view.size&&view.current===1){setHtml(node,'');return;}
 const first=(view.current-1)*view.size+1;
 const last=Math.min(view.total,view.current*view.size);
 setHtml(node,`<button class="ghost small" data-page="${key}:${view.current-1}" type="button" ${view.current<=1?'disabled':''}>‹ Previous</button>
<span class="pager-count">${first}–${last} of ${grouped.format(view.total)} ${esc(noun)}</span>
<button class="ghost small" data-page="${key}:${view.current+1}" type="button" ${view.current>=view.pages?'disabled':''}>Next ›</button>
<span class="spacer"></span>
<label>Per page <select data-size="${key}">${[10,25,50].map(size=>`<option value="${size}" ${size===view.size?'selected':''}>${size}</option>`).join('')}</select></label>`);
}
/* Attribute names must be dash-case: HTML lowercases them, so data-fooBar
   would arrive as dataset.foobar and never match. */
function chipRow(id,options,active,attribute){
 setHtml($(id),options.map(option=>`<button class="chip" data-${attribute}="${esc(option.value)}" aria-pressed="${option.value===active}" type="button">${esc(option.label)}${option.count===undefined?'':`<span class="n">${grouped.format(option.count)}</span>`}</button>`).join(''));
}

function moveIndicator(){
 const active=$('.primary button.active'),bar=$('.tab-indicator');
 if(!active||!bar)return;
 bar.style.width=active.offsetWidth+'px';
 bar.style.transform=`translateX(${active.offsetLeft}px)`;
}
function showView(name){
 if(!VIEWS.includes(name))name=DEFAULT_VIEW;
 currentView=name;focusIndex=-1;
 $$('.screen').forEach(node=>node.hidden=node.id!==`panel-${name}`);
 $$('.primary button').forEach(node=>node.classList.toggle('active',node.dataset.view===name));
 moveIndicator();applyFocus();
 /* Arriving on a tab is how its badge clears: what he can now see is not news. */
 if(state&&name==='topics')renderProposals();
 if(state&&name==='blogs')renderBlogs();
 if(state&&name==='archived')renderArchived();
 if(state&&name==='social')renderSocial();
 paintArrivals();
 if(name==='analytics')drawChart();
}
function rows(){const panel=$(`#panel-${currentView}`);return panel?[...panel.querySelectorAll('[data-row]')]:[];}
function applyFocus(){
 const all=rows();
 all.forEach((node,index)=>node.classList.toggle('is-focused',index===focusIndex));
 if(focusIndex>=0&&all[focusIndex])all[focusIndex].scrollIntoView({block:'nearest'});
}
function moveFocus(step){
 const all=rows();if(!all.length)return;
 focusIndex=focusIndex<0?(step>0?0:all.length-1):Math.min(all.length-1,Math.max(0,focusIndex+step));
 applyFocus();
}
function openFocused(){
 const node=rows()[focusIndex];if(!node)return;
 const open=node.querySelector('[data-open]');
 if(open){openDetail(open.dataset.open);return;}
 node.querySelector('details')?.toggleAttribute('open');
}

/* ---------------------------------------------------------------- proposals */
/* The five beats the radar stands on, in the words the screen should use for
   them. A slug the console has not been taught is shown as itself rather than
   hidden: an unnamed beat is still a true answer to "where did this come from". */
const BEAT_LABELS={
 'ev-industry':'EV industry',
 policy:'Government policy',
 competitors:'Competitors',
 'battery-tech':'Battery technology',
 market:'Market trends',
 solar:'Solar',
 bess:'Battery storage (BESS)',
 ess:'Grid storage',
 'inverter-batteries':'Inverter batteries',
 'energy-transition':'Energy transition',
 'deep-tech':'Deep tech',
 watchlist:'Watchlist'
};
function beatLabel(slug){return BEAT_LABELS[slug]||slug;}
function beatPill(proposal){
 const beat=(proposal.beat||'').trim();
 /* A subject typed into the box above has no beat, and saying "manual" would be
    inventing one. It simply carries no tag. */
 return beat?`<span class="pill beat">${esc(beatLabel(beat))}</span>`:'';
}
function sourceLine(proposal){
 const refs=(proposal.source_refs||[]).map(ref=>{
  if(/^https?:\/\//i.test(ref))return `<a href="${esc(ref)}" target="_blank" rel="noopener">${esc(ref.replace(/^https?:\/\//,'').slice(0,60))}</a>`;
  if(ref.startsWith('gsc:'))return `Search Console: ${esc(ref.slice(4))}`;
  if(ref.startsWith('board:'))return `board card ${esc(ref.slice(6))}`;
  return esc(ref);
 });
 const kind={search_console:'Search Console',firecrawl:'Firecrawl',cache:'cached research',legacy_board:'carried over from the board'}[proposal.source_kind]||proposal.source_kind;
 if(!refs.length)return '<p class="meta source-missing">This candidate names no source.</p>';
 return `<p class="meta">Source: <span class="source">${esc(kind)}</span> — ${refs.join(' · ')}</p>`;
}
/* What Search Console measured for this subject, or the fact that it measured
   nothing. Never a zero: "we have no data for solar" and "solar gets no
   impressions" are opposite facts, and printing the second when we mean the
   first is an invented figure. A beat the radar has only just started sweeping
   is exactly the case that hits this. */
function demandLine(proposal){
 const demand=proposal.demand||{};
 if(!demand.impressions)return '<p class="meta demand-none">No Search Console data for this subject yet</p>';
 const parts=[`${demand.impressions.toLocaleString()} impressions`,
              `CTR ${(demand.ctr*100).toFixed(1)}%`];
 if(demand.position)parts.push(`avg position ${demand.position}`);
 return `<p class="meta demand">${esc(parts.join(' \u00b7 '))}</p>`;
}
function proposalCard(proposal){
 const keywords=(proposal.keywords||[]).map(word=>`<span class="pill">${esc(word)}</span>`).join(' ')||'<span class="meta">no keywords recorded</span>';
 const round=proposal.round>1?`<span class="meta">revised ${proposal.round-1}×</span>`:'';
 const busyNote=proposal.status==='revising'?'<p class="meta">Re-researching this candidate…</p>':'';
 const history=(proposal.history||[]).length>1?`<details><summary>Earlier rounds</summary>${proposal.history.slice(0,-1).map(item=>`<div class="history-row"><strong>Round ${esc(item.round)}: ${esc(item.title)}</strong><p class="meta">${esc(item.outline)}</p></div>`).join('')}</details>`:'';
 return `<article class="card" role="listitem" data-key="${esc(proposal.id)}" data-row="${esc(proposal.id)}" data-proposal="${esc(proposal.id)}">
<div class="card-row"><div class="card-main">${pill(proposal.status)} ${beatPill(proposal)} ${round}
<h3>${esc(proposal.title)}</h3>
<p class="meta">${proposal.beat?`From the ${esc(beatLabel(proposal.beat))} beat`:'From your subject'}: ${esc(proposal.subject)}</p>
<div class="keywords">${keywords}</div>
${demandLine(proposal)}
<p class="outline">${esc(proposal.outline)}</p>
${sourceLine(proposal)}${busyNote}${history}</div></div>
<div class="actions">
<button data-approve="${esc(proposal.id)}" type="button">Approve for blog</button>
<button class="ghost" data-suggest-open="${esc(proposal.id)}" type="button">Suggest changes</button>
<button class="ghost" data-archive="${esc(proposal.id)}" type="button">Archive</button>
<button class="danger" data-reject-open="${esc(proposal.id)}" type="button">Reject</button>
</div>
<p class="row-error" data-card-error hidden></p>
<div class="inline-form" data-form="${esc(proposal.id)}" hidden>
<label class="field"><span data-form-label></span><textarea data-form-input rows="2" maxlength="1000"></textarea></label>
<div class="actions"><button data-form-submit="${esc(proposal.id)}" type="button">Send</button><button class="ghost" data-form-cancel="${esc(proposal.id)}" type="button">Cancel</button></div>
<p class="form-error" data-form-error hidden></p>
</div></article>`;
}
function matchesProposal(proposal,term){
 if(!term)return true;
 const hay=[proposal.title,proposal.subject,proposal.outline,...(proposal.keywords||[])].join(' ').toLocaleLowerCase();
 return hay.includes(term);
}
function renderProposals(){
 const topics=state.topics||{};
 const all=topics.proposals||[];
 const term=ui.topics.search.trim().toLocaleLowerCase();
 const counts=all.reduce((total,item)=>{total[item.status]=(total[item.status]||0)+1;return total;},{});
 chipRow('#topics-filter',[
  {value:'all',label:'All',count:all.length},
  {value:'proposed',label:'Awaiting you',count:counts.proposed||0},
  {value:'revising',label:'Re-researching',count:counts.revising||0}
 ],ui.topics.filter,'topics-filter');
 const filtered=all.filter(item=>(ui.topics.filter==='all'||item.status===ui.topics.filter)&&matchesProposal(item,term));
 const view=page(filtered,'topics');
 $('#topics-count').textContent=filtered.length===all.length
  ?`${grouped.format(all.length)} candidate${all.length===1?'':'s'}`
  :`${grouped.format(filtered.length)} of ${grouped.format(all.length)}`;
 patchRows($('#proposal-list'),view.items.map(item=>({key:String(item.id),html:proposalCard(item)})),all.length
  ?emptyState('Nothing matches','No candidate matches this search and filter.','Clear the filters','data-clear="topics"')
  :emptyState('No candidates yet','No topic research has run yet. Enter a rough subject above and Hermes will research it into candidates you can decide on.','Enter a subject','data-focus="subject"'));
 settleArrivals('topics',view.items.map(item=>item.id));
 paintArrivals();
 renderPager('#topics-pager','topics',view,'candidates');

 const queue=state.research_queue||[];
 $('#queued-count').textContent=queue.length?`(${queue.length})`:'(none)';
 setHtml($('#queued-list'),queue.map(item=>`<div class="list-row"><div class="card-main"><strong>${esc(item.subject)}</strong><p class="meta">${esc(item.reason||'Queued from Analytics.')}</p></div><div class="actions"><button class="small" data-research-queued="${esc(item.subject)}" type="button">Research this</button><button class="ghost small" data-unqueue="${esc(item.subject)}" type="button">Remove</button></div></div>`).join('')||'<p class="empty">Nothing is queued. The Analytics tab can send subjects here.</p>');

 const rejected=topics.rejected||[];
 $('#rejected-count').textContent=rejected.length?`(${rejected.length})`:'(none)';
 setHtml($('#rejected-list'),rejected.slice(0,25).map(item=>`<div class="list-row"><div class="card-main"><strong>${esc(item.title)}</strong><p class="meta">${esc(item.reason||'no reason recorded')} · ${esc(item.actor)} · ${esc(item.created_at)}</p></div><button class="ghost small" data-undo="${esc(item.proposal_id)}" type="button">Undo</button></div>`).join('')+(rejected.length>25?`<p class="meta">Showing the 25 most recent of ${grouped.format(rejected.length)}.</p>`:'')||'<p class="empty">Nothing has been rejected.</p>');
 const carded=topics.carded||[];
 $('#carded-count').textContent=carded.length?`(${carded.length})`:'(none)';
 setHtml($('#carded-list'),carded.slice(0,25).map(item=>`<div class="list-row"><span>${esc(item.title)}</span><span class="meta num">${esc(item.task_id)}</span></div>`).join('')||'<p class="empty">No topic has been approved yet.</p>');
 renderCredits();
}
function renderCredits(){
 const budget=(state.topics||{}).budget||{};
 const node=$('#credit-meter');
 node.classList.remove('error');
 if(budget.status==='ready'){node.innerHTML=`Firecrawl: <strong class="num">${esc(budget.remaining)}</strong> credits left · a proposal run reads up to ${esc(budget.page_cap)} pages · refuses at ${esc(budget.stop_threshold)} used`;return;}
 node.textContent=budget.message||'No proposal research has run yet, so no credit balance has been measured.';
}
/* What the sweep actually covered, not merely that one happened.

   A beat that returned nothing and a beat nobody searched produce the same thing
   on this screen — no candidates — and only one of them is a reason to change the
   query. So both lists are named. */
function radarHtml(){
 const radar=(state.topics||{}).radar;
 if(!radar)return '<p class="meta">The news radar has not run yet. It sweeps each morning, and the button above runs it now.</p>';
 const covered=(radar.beats||[]).map(beatLabel);
 const dry=new Set(radar.empty_beats||[]);
 const worked=covered.filter((_label,index)=>!dry.has((radar.beats||[])[index]));
 const empty=(radar.beats||[]).filter(slug=>dry.has(slug)).map(beatLabel);
 return `<p class="meta">Last sweep ${esc(radar.started_at)} (${esc(radar.mode)}): ${esc(radar.message||radar.status)}</p>`
  +(covered.length?`<p class="meta">Beats swept: ${worked.map(name=>`<span class="pill beat">${esc(name)}</span>`).join(' ')||'<span class="num">none returned anything</span>'}`
    +(empty.length?` · nothing new from ${empty.map(name=>esc(name)).join(', ')}`:'')+'</p>':'');
}
/* The Archived header is a span in a heading row, so it takes the one-line
   summary it always took. The coverage belongs where the beat is run from. */
function radarLine(){
 const radar=(state.topics||{}).radar;
 return radar
  ?`Last sweep ${radar.started_at} (${radar.mode}): ${radar.message||radar.status}`
  :'The news radar has not run yet.';
}
function renderRadar(){
 setHtml($('#radar-status'),radarHtml());
 const shelf=$('#archived-radar');
 if(shelf)shelf.textContent=radarLine();
}

/* ----------------------------------------------------------------- archived */
/* Set aside, not vetoed. The copy has to keep saying so, because the button
   beside Restore is Reject and those two are not degrees of the same thing. */
function archivedCard(proposal){
 const keywords=(proposal.keywords||[]).map(word=>`<span class="pill">${esc(word)}</span>`).join(' ')||'<span class="meta">no keywords recorded</span>';
 return `<article class="card" role="listitem" data-key="${esc(proposal.id)}" data-row="${esc(proposal.id)}" data-proposal="${esc(proposal.id)}">
<div class="card-row"><div class="card-main">${pill('archived')}
<h3>${esc(proposal.title)}</h3>
<p class="meta">From your subject: ${esc(proposal.subject)} · set aside ${esc(proposal.updated_at||proposal.created_at||'')}</p>
<div class="keywords">${keywords}</div>
<p class="outline">${esc(proposal.outline)}</p>
${sourceLine(proposal)}</div></div>
<div class="actions">
<button data-restore="${esc(proposal.id)}" type="button">Restore</button>
<button class="danger ghost" data-reject-open="${esc(proposal.id)}" type="button">Reject permanently</button>
</div>
<p class="row-error" data-card-error hidden></p>
<div class="inline-form" data-form="${esc(proposal.id)}" hidden>
<label class="field"><span data-form-label></span><textarea data-form-input rows="2" maxlength="1000"></textarea></label>
<div class="actions"><button data-form-submit="${esc(proposal.id)}" type="button">Send</button><button class="ghost" data-form-cancel="${esc(proposal.id)}" type="button">Cancel</button></div>
<p class="form-error" data-form-error hidden></p>
</div></article>`;
}
function renderArchived(){
 const all=(state.topics||{}).archived||[];
 const term=ui.archived.search.trim().toLocaleLowerCase();
 const filtered=all.filter(item=>matchesProposal(item,term));
 const view=page(filtered,'archived');
 $('#archived-count').textContent=filtered.length===all.length
  ?`${grouped.format(all.length)} archived topic${all.length===1?'':'s'}`
  :`${grouped.format(filtered.length)} of ${grouped.format(all.length)}`;
 /* Grouped by the subject they came from: six candidates from one subject are
    one decision that was already made, not six unrelated leftovers. Each heading
    is its own keyed entry — patchRows builds one element per entry and drops
    everything after the first, so a heading glued onto a card would eat it. */
 const entries=[];
 let lastSubject=null;
 view.items.forEach(item=>{
  const key=item.subject_id??item.subject;
  if(key!==lastSubject){
   lastSubject=key;
   entries.push({key:`subject-${key}`,html:`<h3 class="rule" data-key="subject-${esc(key)}">${esc(item.subject||'no subject recorded')}</h3>`});
  }
  entries.push({key:String(item.id),html:archivedCard(item)});
 });
 patchRows($('#archived-list'),entries,all.length
  ?emptyState('Nothing matches','No archived topic matches this search.','Clear the search','data-clear="archived"')
  :emptyState('Nothing is archived','When you approve one topic, the other candidates from the same subject move here. They are not rejected — research can surface one again.','Go to Topics & Research','data-view="topics"'));
 renderPager('#archived-pager','archived',view,'archived topics');
 renderRadar();
}

async function researchSubject(subject){
 subject=(subject||$('#subject').value).trim();
 const result=$('#propose-result');
 if(!subject){result.classList.add('error');result.textContent='Enter a rough subject first.';$('#subject').focus();return;}
 if(busy)return;
 result.classList.remove('error');
 result.textContent='Researching… Search Console first, then up to five pages of Firecrawl.';
 /* Runs for tens of seconds. The button goes dead and starts counting before the
    request leaves, and a candidate-height skeleton holds the space below it. */
 const action=runAction({
  button:'#research-subject',label:'Researching…',
  slot:'#topics-pending',shape:'card-h',count:1,
  failTitle:'The research run did not finish.'
 });
 try{
  const run=await post('/ceo/api/propose',{subject});
  const parts=[`${run.added.length} candidate${run.added.length===1?'':'s'} proposed.`];
  if(run.cache_hit)parts.push('Cached research reused — this run cost 0 credits.');
  else parts.push(`Cost ${run.credits_used} credits; ${run.credits_remaining} left.`);
  if(run.suppressed.length)parts.push(`${run.suppressed.length} suppressed as previously rejected.`);
  if(run.duplicates.length)parts.push(`${run.duplicates.length} already proposed.`);
  if((run.resurfaced||[]).length)parts.push(`${run.resurfaced.length} brought back from Archived.`);
  if(run.dropped.length)parts.push(`${run.dropped.length} dropped without a source.`);
  (run.messages||[]).forEach(message=>parts.push(message));
  $('#subject').value='';
  setUi('topics',{filter:'all',page:1});
  result.classList.remove('error');
  result.textContent=parts.join(' ');
 }catch(error){
  action.fail(error.message);
  result.classList.add('error');
  result.textContent=error.message+' Anything the run recorded before it ended is below.';
 }finally{
  action.done();
  /* Either way, for the same reason the sweep does it: a run that committed
     candidates and then lost its connection must not need a page reload.
     The skeleton comes down only once the real candidates are in the DOM. */
  await refresh();
 }
}
async function scanNews(){
 if(busy)return;
 const result=$('#propose-result');
 result.classList.remove('error');
 result.textContent='Sweeping the EV beat… headlines first, then research on at most three subjects.';
 /* As slow as a research run, and for the same reason: it ends in one. */
 const action=runAction({
  button:'#scan-news',label:'Scanning…',
  slot:'#topics-pending',shape:'card-h',count:2,
  failTitle:'The news sweep did not finish.'
 });
 /* Cleared before the sweep starts, so candidates land where he is looking
    rather than behind a filter he set earlier. */
 setUi('topics',{filter:'all',page:1});
 /* Watch it, do not wait on it: each subject's candidates are committed before
    the next one starts, so they can be on screen minutes before the request that
    started them comes back. */
 liveWhileBusy=true;schedulePoll(0);
 try{
  const sweep=await post('/ceo/api/radar/scan',{});
  const parts=[sweep.message||'The sweep finished.'];
  if((sweep.subjects||[]).length)parts.push(`Subjects: ${sweep.subjects.join('; ')}`);
  (sweep.messages||[]).forEach(message=>parts.push(message));
  result.classList.toggle('error',sweep.status!=='completed');
  result.textContent=parts.join(' ');
 }catch(error){
  action.fail(error.message);
  result.classList.add('error');
  result.textContent=error.message+' Anything the sweep recorded before it ended is below.';
 }finally{
  liveWhileBusy=false;
  action.done();
  /* Either way. A sweep that timed out on the way back still wrote what it had,
     and this is the refresh that puts it on screen without him reloading. */
  await refresh();
  schedulePoll();
 }
}
function openInlineForm(id,kind){
 const form=document.querySelector(`[data-form="${id}"]`);if(!form)return;
 form.hidden=false;form.dataset.kind=kind;
 form.querySelector('[data-form-label]').textContent=kind==='suggest'?'What should be different about this topic?':'Why are you rejecting it? (remembered, so it is not proposed again)';
 const failure=form.querySelector('[data-form-error]');
 if(failure){failure.hidden=true;failure.textContent='';}
 form.querySelector('[data-form-input]').focus();
}
async function submitInlineForm(id){
 const form=document.querySelector(`[data-form="${id}"]`);if(!form||busy)return;
 const text=form.querySelector('[data-form-input]').value.trim();
 const failure=form.querySelector('[data-form-error]');
 const suggesting=form.dataset.kind==='suggest';
 if(!text){
  const missing=suggesting?'Say what should change.':'Give a reason so it can be remembered.';
  if(failure){failure.hidden=false;failure.textContent=missing;}else notice(missing,true);
  return;
 }
 const card=document.querySelector(`[data-proposal="${id}"]`);
 card?.classList.add('is-pending');
 /* Suggesting changes re-runs the research, so it is as slow as the first run. */
 const action=runAction({
  button:form.querySelector('[data-form-submit]'),
  label:suggesting?'Re-researching…':'Rejecting…',
  surface:failure,
  failTitle:suggesting?'The re-research did not finish.':'The rejection was not recorded.'
 });
 try{
  if(suggesting){
   const result=await post('/ceo/api/proposal/suggest',{proposal_id:Number(id),comment:text});
   toast(`Revised. Cost ${result.credits_used} credits.`);
  }else{
   await post('/ceo/api/proposal/reject',{proposal_id:Number(id),reason:text});
   toast('Rejected and remembered.');
  }
  await refresh();
 }catch(error){
  card?.classList.remove('is-pending');form.hidden=false;
  action.fail(error.message);
 }finally{action.done();}
}
async function approveProposal(id){
 if(busy)return;
 const card=document.querySelector(`[data-proposal="${id}"]`);
 card?.classList.add('is-pending');
 const action=runAction({
  button:document.querySelector(`[data-approve="${id}"]`),label:'Approving…',
  surface:card?.querySelector('[data-card-error]'),
  failTitle:'The approval was not recorded.'
 });
 try{
  const result=await post('/ceo/api/proposal/approve',{proposal_id:Number(id)});
  const swept=(result.archived||[]).length;
  /* Say what else moved. A card that vanishes from this screen without being
     named is indistinguishable from one that was lost. */
  toast(swept
   ?`Approved. Board card ${result.task_id} is queued for writing; ${swept} related topic${swept===1?'':'s'} moved to Archived.`
   :`Approved. Board card ${result.task_id} is queued for writing.`);
  await refresh();
 }catch(error){card?.classList.remove('is-pending');action.fail(error.message);}
 finally{action.done();}
}
async function archiveProposal(id){
 if(busy)return;
 const card=document.querySelector(`[data-proposal="${id}"]`);
 card?.classList.add('is-pending');
 const action=runAction({
  button:document.querySelector(`[data-archive="${id}"]`),label:'Archiving…',
  surface:card?.querySelector('[data-card-error]'),
  failTitle:'The topic was not archived.'
 });
 try{
  await post('/ceo/api/proposal/archive',{proposal_id:Number(id)});
  toast('Moved to Archived. It is not rejected — Restore brings it back.');
  await refresh();
 }catch(error){card?.classList.remove('is-pending');action.fail(error.message);}
 finally{action.done();}
}
async function restoreProposal(id){
 if(busy)return;
 const card=document.querySelector(`[data-proposal="${id}"]`);
 card?.classList.add('is-pending');
 const action=runAction({
  button:document.querySelector(`[data-restore="${id}"]`),label:'Restoring…',
  surface:card?.querySelector('[data-card-error]'),
  failTitle:'The topic was not restored.'
 });
 try{
  await post('/ceo/api/proposal/restore',{proposal_id:Number(id)});
  toast('Back in Topics & Research, awaiting your decision.');
  await refresh();
 }catch(error){card?.classList.remove('is-pending');action.fail(error.message);}
 finally{action.done();}
}
async function undoRejection(id){
 if(busy)return;
 const action=runAction({
  button:document.querySelector(`[data-undo="${id}"]`),label:'Returning…',
  failTitle:'The undo did not go through.'
 });
 try{await post('/ceo/api/proposal/undo-rejection',{proposal_id:Number(id)});toast('Rejection undone.');await refresh();}
 catch(error){action.fail(error.message);}
 finally{action.done();}
}
async function queueSubject(subject,reason,action){
 if(busy)return;
 const card=document.querySelector(`[data-opportunity="${CSS.escape(subject)}"]`);
 const run=runAction({
  button:document.querySelector(`[data-queue="${CSS.escape(subject)}"]`),
  label:action==='add'?'Queuing…':'Removing…',
  surface:card?.querySelector('[data-card-error]'),
  failTitle:'The queue was not changed.'
 });
 try{
  const result=await post('/ceo/api/research-queue',{subject,reason,action});
  if(state)state.research_queue=result.research_queue;
  toast(action==='add'?'Queued in Topics & Research.':'Removed from the queue.');
  renderProposals();renderOpportunities();
 }catch(error){run.fail(error.message);}
 finally{run.done();}
}

/* ------------------------------------------------------------------- trends */
function renderTrends(){
 const keyword=$('#trend-keyword').value.trim().toLocaleLowerCase();
 const all=(state.trending||[]).filter(row=>!keyword||String(row.title||'').toLocaleLowerCase().includes(keyword));
 const view=page(all,'trends');
 setHtml($('#trend-list'),view.items.map(row=>`<div class="list-row"><div class="card-main"><strong>${esc(row.title)}</strong><p class="meta"><span class="source">${esc(row.source)}</span> · ${esc(row.metric||'metric unavailable')}</p></div><div class="card-figures"><span><span class="stat">${cell(row.current??row.summary)}</span>${deltaHtml(row.delta)}</span></div></div>`).join('')
  ||'<p class="empty">No connected source returned matching trends.</p>');
 renderPager('#trends-pager','trends',view,'trends');
 setHtml($('#trend-messages'),(state.trending_messages||[]).map(message=>`<p class="meta">${esc(message)}</p>`).join(''));
 setHtml($('#watchlist'),(state.watchlist||[]).map(keyword=>`<div class="list-row"><span>${esc(keyword)}</span><button class="ghost small" data-unwatch="${esc(keyword)}" type="button">Remove</button></div>`).join('')||'<p class="empty">Nothing is being watched. Watchlist entries never create board cards.</p>');
}

/* -------------------------------------------------------------------- blogs */
/* Every content card is here now, not only the ones with a finished article. The
   server decides which state a card is in — one function, `console_board.blog_state`
   — and this side only decides how to say it. Two views of the same fact drifting
   apart is exactly how a card being written came to look identical to a card
   nobody had started. */
function blogStatus(task){return task.blog?.state||'awaiting_you';}
function blogLabel(task){return task.blog?.label||'Awaiting you';}
/* A run takes minutes. A label that does not move for four of them reads as a
   hang, so the two running states carry a clock. It is ticked in place by
   `tickElapsed` rather than re-rendered: patchRows compares the markup it last
   produced, so a node whose text we changed underneath it is left alone. */
function elapsedText(iso){
 const started=Date.parse(String(iso||''));
 if(!Number.isFinite(started))return '';
 const seconds=Math.max(0,Math.floor((Date.now()-started)/1000));
 if(seconds<60)return `${seconds}s`;
 const minutes=Math.floor(seconds/60);
 return minutes<60?`${minutes}m ${seconds%60}s`:`${Math.floor(minutes/60)}h ${minutes%60}m`;
}
function tickElapsed(){
 $$('[data-elapsed]').forEach(node=>{
  const text=elapsedText(node.dataset.elapsed);
  if(text&&node.textContent!==text)node.textContent=text;
 });
}
setInterval(tickElapsed,1000);
function blogCard(task){
 const blog=task.blog||{};
 const words=task.article?.word_count??0;
 const minutes=task.article?.read_minutes??0;
 const running=blog.state==='researching'||blog.state==='writing';
 const clock=running&&blog.started_at
  ?` · <span class="num" data-elapsed="${esc(blog.started_at)}">${esc(elapsedText(blog.started_at))}</span>`:'';
 /* An article that does not exist yet has no word count, and a zero would read
    as an empty article rather than an unwritten one. */
 const figures=task.article
  ?`<div class="card-figures"><span><span class="stat">${grouped.format(words)}</span><span class="label">words</span></span></div>`
  :'';
 const measures=task.article
  ?` · <span class="num">${grouped.format(words)}</span> words · <span class="num">${minutes}</span> min read`:'';
 /* The failure line is the whole reason this state exists. Nine writer attempts
    on one card failed in a row and the board said nothing at all. */
 const reason=blog.reason
  ?`<p class="meta blog-reason${blog.state==='failed'?' is-failure':''}">${esc(blog.reason)}</p>`:'';
 const actions=[];
 if(blog.retryable)actions.push(`<button class="ghost small" data-retry="${esc(task.id)}" type="button">Retry</button>`);
 if((blog.state==='in_preview'||blog.state==='published')&&blog.url)
  actions.push(`<a class="ghost small" href="${esc(blog.url)}" target="_blank" rel="noopener">Open preview</a>`);
 const aside=actions.length?`<div class="blog-actions">${actions.join('')}</div>`:'';
 return `<article class="card" role="listitem" data-key="${esc(task.id)}" data-row="${esc(task.id)}"><div class="card-row">
<div class="card-main"><button class="open" data-open="${esc(task.id)}" type="button">${pill(blogStatus(task),blogLabel(task))}
<h3>${esc(task.title||task.id)}</h3>
<p class="meta"><span class="num">${esc(task.id)}</span>${measures}${clock}</p></button>${reason}${aside}</div>
${figures}
</div></article>`;
}
/* Grouped for the chips, because "is it moving" and "is it stuck" are the two
   questions actually being asked of this tab. */
const BLOG_GROUPS={
 draft:new Set(['queued','researching','writing']),
 'being edited':new Set(['rewriting']),
 'waiting for review':new Set(['checking','awaiting_you']),
 approved:new Set(['approved']),
 scheduled:new Set(['scheduled']),
 'in preview':new Set(['in_preview']),
 published:new Set(['published']),
 failed:new Set(['failed'])
};
function blogGroup(task){
 const state=blogStatus(task);
 return Object.keys(BLOG_GROUPS).find(name=>BLOG_GROUPS[name].has(state))||'held';
}
function renderBlogs(){
 const all=state.blogs||[];
 const term=ui.blogs.search.trim().toLocaleLowerCase();
 const counts=all.reduce((total,item)=>{const key=blogGroup(item);total[key]=(total[key]||0)+1;return total;},{});
 chipRow('#blogs-filter',[
  {value:'all',label:'All',count:all.length},
  {value:'draft',label:'Draft',count:counts.draft||0},
  {value:'being edited',label:'Being edited',count:counts['being edited']||0},
  {value:'waiting for review',label:'Waiting for review',count:counts['waiting for review']||0},
  {value:'approved',label:'Approved',count:counts.approved||0},
  {value:'scheduled',label:'Scheduled',count:counts.scheduled||0},
  {value:'in preview',label:'In preview',count:counts['in preview']||0},
  {value:'published',label:'Published',count:counts.published||0},
  {value:'failed',label:'Could not be written',count:counts.failed||0}
 ],ui.blogs.filter,'blogs-filter');
 const filtered=all.filter(task=>{
  if(ui.blogs.filter!=='all'&&blogGroup(task)!==ui.blogs.filter)return false;
  if(!term)return true;
  return `${task.title||''} ${task.id} ${task.article?.text||''}`.toLocaleLowerCase().includes(term);
 });
 const view=page(filtered,'blogs');
 $('#blogs-count').textContent=filtered.length===all.length
  ?`${grouped.format(all.length)} article${all.length===1?'':'s'}`
  :`${grouped.format(filtered.length)} of ${grouped.format(all.length)}`;
 patchRows($('#blog-list'),view.items.map(task=>({key:String(task.id),html:blogCard(task)})),all.length
  ?emptyState('Nothing matches','No article matches this search and filter.','Clear the filters','data-clear="blogs"')
  :emptyState('No article yet','A topic has to be approved in Topics & Research before the writer can produce one.','Go to Topics & Research','data-view="topics"'));
 settleArrivals('blogs',view.items.map(task=>task.id));
 paintArrivals();
 renderPager('#blogs-pager','blogs',view,'articles');
 tickElapsed();
}
/* A retry is his click and only his. The worker skips a failed card precisely so
   it cannot sit in a loop retrying something that keeps failing. */
function retryBlog(id){
 const button=document.querySelector(`[data-retry="${id}"]`);
 const action=runAction({button,label:'Queueing…',count:0,failTitle:'That could not be queued.'});
 post('/ceo/api/blog-retry',{task_id:id})
  .then(()=>{toast('Queued to be written again.');return refresh(true);})
  .catch(error=>action.fail(error.message))
  .finally(()=>action.done());
}

/* ---------------------------------------------------------------- analytics */
const TILES=[
 {key:'impressions',label:'Impressions'},
 {key:'clicks',label:'Clicks'},
 {key:'ctr',label:'CTR',kind:'ctr'},
 {key:'position',label:'Average position',kind:'position'},
 {key:'indexed_pages',label:'Indexed pages'}
];
const CHART_METRICS=[
 {value:'traffic',label:'Impressions & clicks'},
 {value:'ctr',label:'CTR'},
 {value:'position',label:'Average position'}
];
function searchReport(){return state?.analytics?.search||{};}
function renderRangeChips(){
 const report=searchReport();
 chipRow('#range-chips',[
  {value:'7',label:'7 days'},{value:'28',label:'28 days'},{value:'90',label:'90 days'},
  {value:'all',label:'All'},{value:'custom',label:'Custom'}
 ],ui.analytics.range,'range');
 chipRow('#device-chips',[
  {value:'all',label:'All devices'},{value:'desktop',label:'Desktop'},
  {value:'mobile',label:'Mobile'},{value:'tablet',label:'Tablet'}
 ],ui.analytics.device,'device');
 $('#custom-range').hidden=ui.analytics.range!=='custom';
 if(report.range&&ui.analytics.range==='custom'){
  if(!$('#range-start').value)$('#range-start').value=report.range.start||'';
  if(!$('#range-end').value)$('#range-end').value=report.range.end||'';
 }
}
function renderSearchConsole(){
 const report=searchReport();
 renderRangeChips();
 const connected=report.status==='ready'||report.status==='collecting';
 if(!connected){
  const vars=(report.required_variables||[]).join(', ');
  setHtml($('#search-status'),emptyState(
   report.status==='error'?'Search Console could not be read':'Search Console is not connected',
   (report.message||'No Search Console credentials are configured.')+(vars?` Required environment variables: ${vars}.`:'')));
 }else if(report.message){
  setHtml($('#search-status'),emptyState('Nothing measured yet',report.message));
 }else setHtml($('#search-status'),'');

 const totals=report.totals||{};
 const deltas=report.deltas||null;
 setHtml($('#stat-tiles'),TILES.map(tile=>{
  const shown=figure(totals[tile.key],tile.kind);
  return `<article class="tile"><span class="tile-label">${esc(tile.label)}</span>
<span class="tile-figure${shown===null?' absent':''}">${shown===null?'not yet':esc(shown)}</span>
${deltas&&tile.key!=='indexed_pages'?deltaHtml(deltas[tile.key],tile.kind):''}</article>`;
 }).join(''));

 chipRow('#chart-metrics',CHART_METRICS,ui.analytics.metric,'metric');
 setHtml($('#chart-legend'),ui.analytics.metric==='traffic'
  ?'<span><i></i>Impressions</span><span><i class="clicks"></i>Clicks</span>'
  :`<span><i></i>${esc(CHART_METRICS.find(item=>item.value===ui.analytics.metric).label)}</span>`);
 drawChart();
 renderOpportunities();
 renderDataTable('#queries-table','#queries-pager','queries',report.queries||[],'query','queries');
 renderDataTable('#pages-table','#pages-pager','pages',report.pages||[],'page','pages');
 const range=report.range||{};
 $('#analytics-footnote').textContent=
  `Collection started ${report.collection_start||'—'}. Search Console finalises a day about ${report.reporting_delay_days??2} days later, so this window ends ${range.end||'—'}.`
  +(range.start?` Showing ${range.start} to ${range.end}, ${range.days} day${range.days===1?'':'s'}, ${report.device==='all'?'all devices':report.device}.`:'');
}
function renderOpportunities(){
 const report=searchReport();
 const all=report.opportunities||[];
 const queued=new Set((state.research_queue||[]).map(item=>item.subject.toLocaleLowerCase()));
 const view=page(all,'opportunities');
 setHtml($('#opportunity-list'),view.items.map(item=>{
  const isQueued=queued.has(item.subject.toLocaleLowerCase());
  return `<article class="opportunity card kind-${esc(item.kind)}${isQueued?' is-queued':''}" role="listitem" data-row="op-${esc(item.subject)}" data-opportunity="${esc(item.subject)}">
<div class="card-main">${pill(item.kind)} <span class="meta">${item.source==='page'?'page':'search query'}</span>
<strong>${esc(item.subject)}</strong>
<p class="why">${esc(item.reason)}</p></div>
<div class="card-figures">
<span><span class="stat">${cell(item.impressions)}</span><span class="label">impressions</span></span>
<span><span class="stat">${cell(item.position,'position')}</span><span class="label">position</span></span></div>
<button class="${isQueued?'ghost':''}" data-queue="${esc(item.subject)}" data-queue-action="${isQueued?'remove':'add'}" data-queue-reason="${esc(item.reason)}" type="button">${isQueued?'Queued ✓':'Research this'}</button>
<p class="row-error" data-card-error hidden></p>
</article>`;
 }).join('')||emptyState(
  report.status==='ready'?'Nothing qualifies yet':'Nothing to suggest yet',
  report.status==='ready'
   ?'No query or page in this window met the thresholds for an opportunity. Widen the range to look further back.'
   :'Once Search Console has recorded impressions, the queries worth writing about will be listed here.',
  report.status==='ready'?'Show all time':'',
  'data-range="all"'));
 renderPager('#opportunities-pager','opportunities',view,'opportunities');
}
function renderDataTable(tableId,pagerId,key,allRows,subjectField,noun){
 const table=$(tableId);if(!table)return;
 const config=ui[key];
 const sorted=[...allRows].sort((left,right)=>{
  const a=left[config.sort],b=right[config.sort];
  if(a===b)return 0;
  if(a===null||a===undefined)return 1;
  if(b===null||b===undefined)return -1;
  const result=typeof a==='string'?a.localeCompare(b):a-b;
  return config.dir==='asc'?result:-result;
 });
 const view=page(sorted,key);
 [...table.querySelectorAll('th[data-sort]')].forEach(header=>{
  header.setAttribute('aria-sort',header.dataset.sort===config.sort?(config.dir==='asc'?'ascending':'descending'):'none');
 });
 setHtml(table.querySelector('tbody'),view.items.map(row=>`<tr>
<td class="subject">${esc(row[subjectField])}</td>
<td class="n">${cell(row.impressions)}</td>
<td class="n">${cell(row.clicks)}</td>
<td class="n">${cell(row.ctr,'ctr')}</td>
<td class="n">${cell(row.position,'position')}</td></tr>`).join('')
  ||`<tr><td colspan="5" class="meta">No ${esc(noun)} have been recorded in this window yet.</td></tr>`);
 renderPager(pagerId,key,view,noun);
}

/* A chart drawn as SVG, by hand. Bars while a day still has room to be its own
   mark; a line once it does not. */
function drawChart(){
 const host=$('#chart');if(!host)return;
 const report=searchReport();
 const series=report.series||[];
 const metric=ui.analytics.metric;
 if(!series.length){
  setHtml(host,emptyState('No day measured yet',
   report.status==='ready'||report.status==='collecting'
    ?`Search Console has returned no daily rows for this window. Collection started ${report.collection_start||'recently'}.`
    :'Connect Search Console and the daily shape of impressions and clicks appears here.'));
  return;
 }
 const width=Math.max(320,host.clientWidth||760);
 const height=210,left=46,right=14,top=14,bottom=28;
 const plotW=width-left-right,plotH=height-top-bottom;
 const slot=plotW/series.length;
 const asBars=slot>=5;
 const primary=metric==='traffic'?'impressions':metric;
 const values=series.map(day=>day[primary]).filter(value=>value!==null&&value!==undefined);
 if(!values.length){setHtml(host,emptyState('Not measured yet',`No ${primary} were recorded on any day in this window.`));return;}
 const inverted=metric==='position';
 let low=Math.min(...values),high=Math.max(...values);
 if(inverted){low=Math.max(1,Math.floor(low)-1);high=Math.ceil(high)+1;}
 else{low=0;high=Math.max(high,1);}
 const span=high-low||1;
 const y=value=>top+(inverted?(value-low)/span:(1-(value-low)/span))*plotH;
 const x=index=>left+slot*index+slot/2;
 const parts=[];
 const ticks=4;
 for(let index=0;index<=ticks;index+=1){
  const value=low+span*index/ticks;
  const py=y(value);
  parts.push(`<line class="grid" x1="${left}" y1="${py.toFixed(1)}" x2="${(width-right).toFixed(1)}" y2="${py.toFixed(1)}"></line>`);
  parts.push(`<text x="${left-8}" y="${(py+3.5).toFixed(1)}" text-anchor="end">${esc(figure(metric==='ctr'?Number(value.toFixed(1)):Math.round(value*10)/10,metric==='ctr'?'ctr':metric==='position'?'position':''))}</text>`);
 }
 if(asBars){
  const barW=Math.max(2,Math.min(22,slot-2));
  series.forEach((day,index)=>{
   const value=day[primary];
   if(value===null||value===undefined)return;
   const py=y(value),base=inverted?y(low):y(0);
   parts.push(`<rect class="bar" x="${(x(index)-barW/2).toFixed(1)}" y="${Math.min(py,base).toFixed(1)}" width="${barW.toFixed(1)}" height="${Math.max(1,Math.abs(base-py)).toFixed(1)}" rx="1.5"></rect>`);
  });
 }else{
  const path=series.map((day,index)=>{
   const value=day[primary];
   if(value===null||value===undefined)return '';
   return `${index===0?'M':'L'}${x(index).toFixed(1)},${y(value).toFixed(1)}`;
  }).filter(Boolean).join(' ');
  parts.push(`<path class="line" style="stroke:var(--green)" d="${path}"></path>`);
 }
 if(metric==='traffic'){
  const clicks=series.map(day=>day.clicks).filter(value=>value!==null&&value!==undefined);
  const clickHigh=Math.max(1,...clicks);
  const cy=value=>top+(1-value/clickHigh)*plotH;
  const path=series.map((day,index)=>day.clicks===null||day.clicks===undefined?'':`${index===0?'M':'L'}${x(index).toFixed(1)},${cy(day.clicks).toFixed(1)}`).filter(Boolean).join(' ');
  if(path)parts.push(`<path class="line" d="${path}"></path>`);
  series.forEach((day,index)=>{if(day.clicks)parts.push(`<circle class="dot" cx="${x(index).toFixed(1)}" cy="${cy(day.clicks).toFixed(1)}" r="2.5"></circle>`);});
  parts.push(`<text x="${width-right}" y="${top-3}" text-anchor="end" style="fill:var(--clay)">clicks peak ${esc(figure(clickHigh))}</text>`);
 }
 const step=Math.max(1,Math.ceil(series.length/6));
 series.forEach((day,index)=>{
  if(index%step===0||index===series.length-1)
   parts.push(`<text x="${x(index).toFixed(1)}" y="${height-8}" text-anchor="middle">${esc(String(day.date).slice(5))}</text>`);
 });
 series.forEach((day,index)=>{
  parts.push(`<rect class="hit" tabindex="0" role="img" data-day="${index}" x="${(left+slot*index).toFixed(1)}" y="${top}" width="${slot.toFixed(1)}" height="${plotH}" aria-label="${esc(tipText(day))}"></rect>`);
 });
 setHtml(host,`<svg class="chart" viewBox="0 0 ${width} ${height}" role="group" aria-label="Daily Search Console performance">${parts.join('')}</svg>`);
}
function tipText(day){
 return `${day.date}: ${figure(day.impressions)??'not measured'} impressions, ${figure(day.clicks)??'not measured'} clicks, CTR ${figure(day.ctr,'ctr')??'not measured'}, position ${figure(day.position,'position')??'not measured'}`;
}
function showTip(index,target){
 const day=(searchReport().series||[])[index];
 const tip=$('#chart-tip');if(!day||!tip)return;
 tip.innerHTML=`<b>${esc(day.date)}</b><dl>
<dt>Impressions</dt><dd>${cell(day.impressions)}</dd>
<dt>Clicks</dt><dd>${cell(day.clicks)}</dd>
<dt>CTR</dt><dd>${cell(day.ctr,'ctr')}</dd>
<dt>Position</dt><dd>${cell(day.position,'position')}</dd></dl>`;
 tip.hidden=false;
 const wrap=$('.chart-wrap').getBoundingClientRect();
 const box=target.getBoundingClientRect();
 tip.style.left=(box.left-wrap.left+box.width/2)+'px';
 tip.style.top=(box.top-wrap.top-8)+'px';
}
function hideTip(){const tip=$('#chart-tip');if(tip)tip.hidden=true;}

function renderGa4(){
 const data=state.analytics?.ga4||{};
 if(data.status!=='ready'){
  const vars=(data.required_variables||[]).join(', ');
  setHtml($('#ga4-panel'),emptyState('Google Analytics is not connected',
   (data.message||'Google Analytics is not connected yet.')+(vars?` Required environment variables: ${vars}.`:'')));
  return;
 }
 const labels={active_users:'Active users',sessions:'Sessions',screen_page_views:'Page views',engagement_rate:'Engagement rate'};
 setHtml($('#ga4-panel'),`<div class="tiles">${Object.keys(labels).map(key=>{
  const shown=figure(data.metrics?.[key]);
  return `<article class="tile"><span class="tile-label">${esc(labels[key])}</span><span class="tile-figure${shown===null?' absent':''}">${shown===null?'not yet':esc(shown)}</span>${deltaHtml(data.deltas?.[key])}</article>`;
 }).join('')}</div>`);
}
/* ---------------------------------------------------------- blog performance */
/* One row per published article, joined server-side from Search Console and
   Google Analytics. Six columns rather than the five the query and page tables
   carry, so this does not reuse `renderDataTable` -- and `views` sorts on its
   own key, which a shared function would have had to branch on anyway. */
function renderPosts(){
 const table=$('#posts-table');if(!table)return;
 const data=state.analytics?.posts||{};
 const all=data.posts||[];
 const config=ui.posts;
 const sorted=[...all].sort((left,right)=>{
  const a=left[config.sort],b=right[config.sort];
  if(a===b)return 0;
  if(a===null||a===undefined)return 1;
  if(b===null||b===undefined)return -1;
  const result=typeof a==='string'?a.localeCompare(b):a-b;
  return config.dir==='asc'?result:-result;
 });
 const view=page(sorted,'posts');
 [...table.querySelectorAll('th[data-sort]')].forEach(header=>{
  header.setAttribute('aria-sort',header.dataset.sort===config.sort?(config.dir==='asc'?'ascending':'descending'):'none');
 });
 setHtml(table.querySelector('tbody'),view.items.map(row=>{
  /* Which system saw it. A post with views and no impressions was shared, not
     found; one with impressions and no views was shown, not opened. Saying so
     on the row is the difference between a surprising number and a wrong one. */
  const seen=(row.sources||[]).length===2?''
   :(row.sources||[]).includes('ga4')?'<span class="meta"> · analytics only</span>'
   :'<span class="meta"> · search only</span>';
  const label=row.url
   ?`<a href="${esc(row.url)}" target="_blank" rel="noopener">${esc(row.title||row.slug)}</a>`
   :esc(row.title||row.slug);
  return `<tr>
<td class="subject">${label}${seen}</td>
<td class="n">${cell(row.views)}</td>
<td class="n">${cell(row.impressions)}</td>
<td class="n">${cell(row.clicks)}</td>
<td class="n">${cell(row.ctr,'ctr')}</td>
<td class="n">${cell(row.position,'position')}</td></tr>`;
 }).join('')
  ||`<tr><td colspan="6" class="meta">No published article has been measured in this window yet.</td></tr>`);
 renderPager('#posts-pager','posts',view,'articles');
}

/* --------------------------------------------------------- audience panels */
/* Four panels off one payload. Each renders its own "not connected" state from
   the same status, because four independent empty states saying four different
   things about one missing tag is how a console stops being believed. */
function audience(){return state.analytics?.ga4_audience||{};}
function audienceEmpty(host,title){
 const data=audience();
 const vars=(data.required_variables||[]).join(', ');
 setHtml($(host),emptyState(title,
  (data.message||'Google Analytics is not connected yet.')+(vars?` Required environment variables: ${vars}.`:'')));
}
function shareCell(value){
 const width=Math.max(0,Math.min(100,Number(value)||0));
 return `<div class="share-cell"><span class="share-bar"><i style="width:${width}%"></i></span><span class="num">${value===null||value===undefined?'—':esc(Number(value).toFixed(1))+'%'}</span></div>`;
}
function renderSources(){
 const data=audience();
 if(data.status!=='ready'&&data.status!=='collecting'){audienceEmpty('#sources-panel','Traffic sources need Google Analytics');return;}
 const rows=data.traffic_sources||[];
 if(!rows.length){
  setHtml($('#sources-panel'),emptyState('No session recorded yet',
   'Once Google Analytics has recorded sessions in this window, the channels that sent them will be listed here.'));
  return;
 }
 setHtml($('#sources-panel'),`<div class="table-scroll"><table class="data"><thead><tr>
<th>Source</th><th class="n">Sessions</th><th class="n">Visitors</th><th>Share</th><th>Seen as</th>
</tr></thead><tbody>${rows.map(row=>`<tr>
<td class="subject">${esc(row.source)}</td>
<td class="n">${cell(row.sessions)}</td>
<td class="n">${cell(row.active_users)}</td>
<td>${shareCell(row.share)}</td>
<td class="source-examples">${esc((row.examples||[]).join(', ')||'—')}</td></tr>`).join('')}</tbody></table></div>`);
}
function renderPlaces(){
 const data=audience();
 if(data.status!=='ready'&&data.status!=='collecting'){audienceEmpty('#places-panel','Visitor locations need Google Analytics');return;}
 const countries=data.countries||[],cities=data.cities||[];
 if(!countries.length&&!cities.length){
  setHtml($('#places-panel'),emptyState('No location recorded yet',
   'Google Analytics reports a country once it has sessions to report. Nothing has arrived in this window.'));
  return;
 }
 setHtml($('#places-panel'),`<div class="table-scroll"><table class="data"><thead><tr>
<th>Country</th><th class="n">Sessions</th><th class="n">Visitors</th>
</tr></thead><tbody>${countries.map(row=>`<tr>
<td class="subject">${esc(row.country)}</td><td class="n">${cell(row.sessions)}</td><td class="n">${cell(row.active_users)}</td></tr>`).join('')||'<tr><td colspan="3" class="meta">No country recorded yet.</td></tr>'}</tbody></table></div>
<h4>Cities</h4>
<div class="table-scroll"><table class="data"><thead><tr>
<th>City</th><th>Country</th><th class="n">Sessions</th>
</tr></thead><tbody>${cities.map(row=>`<tr>
<td class="subject">${esc(row.city)}</td><td>${esc(row.country)}</td><td class="n">${cell(row.sessions)}</td></tr>`).join('')||'<tr><td colspan="3" class="meta">No city recorded yet.</td></tr>'}</tbody></table></div>`);
}
function renderDevices(){
 const data=audience();
 if(data.status!=='ready'&&data.status!=='collecting'){audienceEmpty('#devices-panel','Device information needs Google Analytics');return;}
 const devices=data.devices||[],browsers=data.browsers||[];
 if(!devices.length&&!browsers.length){
  setHtml($('#devices-panel'),emptyState('No device recorded yet',
   'Device category arrives with the first session Google Analytics records in this window.'));
  return;
 }
 setHtml($('#devices-panel'),`<div class="table-scroll"><table class="data"><thead><tr>
<th>Device</th><th class="n">Sessions</th><th class="n">Engagement</th>
</tr></thead><tbody>${devices.map(row=>`<tr>
<td class="subject">${esc(row.device)}</td><td class="n">${cell(row.sessions)}</td>
<td class="n">${row.engagement_rate===null||row.engagement_rate===undefined?'—':esc((Number(row.engagement_rate)*100).toFixed(1)+'%')}</td></tr>`).join('')||'<tr><td colspan="3" class="meta">No device recorded yet.</td></tr>'}</tbody></table></div>
<h4>Browser and operating system</h4>
<div class="table-scroll"><table class="data"><thead><tr>
<th>Browser</th><th>Operating system</th><th class="n">Sessions</th>
</tr></thead><tbody>${browsers.map(row=>`<tr>
<td class="subject">${esc(row.browser)}</td><td>${esc(row.operating_system)}</td><td class="n">${cell(row.sessions)}</td></tr>`).join('')||'<tr><td colspan="3" class="meta">No browser recorded yet.</td></tr>'}</tbody></table></div>`);
}
function renderJourney(){
 const data=audience();
 if(data.status!=='ready'&&data.status!=='collecting'){audienceEmpty('#journey-panel','Landing pages need Google Analytics');return;}
 const rows=data.landing_pages||[];
 if(!rows.length){
  setHtml($('#journey-panel'),emptyState('No landing page recorded yet',
   'The page a session starts on is recorded with that session. None has arrived in this window.'));
  return;
 }
 setHtml($('#journey-panel'),`<div class="table-scroll"><table class="data"><thead><tr>
<th>Landing page</th><th class="n">Sessions</th><th class="n">Engagement</th><th class="n">Bounce</th>
</tr></thead><tbody>${rows.map(row=>`<tr>
<td class="subject">${esc(row.page)}</td>
<td class="n">${cell(row.sessions)}</td>
<td class="n">${row.engagement_rate===null||row.engagement_rate===undefined?'—':esc((Number(row.engagement_rate)*100).toFixed(1)+'%')}</td>
<td class="n">${row.bounces===null||row.bounces===undefined?'—':esc((Number(row.bounces)*100).toFixed(1)+'%')}</td></tr>`).join('')}</tbody></table></div>
<p class="footnote">This is the entry point, not a full path. Google Analytics reports the page a session began on; a step-by-step journey needs an exploration in GA itself.</p>`);
}
/* --------------------------------------------------------------- social */
/* Published articles and the copy that promotes them. Everything here is a read
   of state except the three actions, and each of those goes through runAction
   like every other slow thing on this console. */
const PLATFORMS=[
 {key:'linkedin',label:'LinkedIn',mark:'in',limit:3000},
 {key:'x',label:'X',mark:'X',limit:280},
 {key:'instagram',label:'Instagram',mark:'IG',limit:2200}
];
/* An X thread is edited as one textarea, with items separated by a line
   containing only three dashes. One box per item would be a nicer form and a
   worse edit: reordering a thread is the commonest change and dragging boxes is
   harder than moving a line. */
const THREAD_SEPARATOR='---';
function splitThread(text){
 return String(text||'').split(/\n\s*---\s*\n/).map(part=>part.trim()).filter(Boolean);
}
function joinThread(items){return (items||[]).join('\n'+THREAD_SEPARATOR+'\n');}
function socialArticles(){return state.social?.articles||[];}
function draftText(draft){
 return draft.platform==='x'&&(draft.thread||[]).length
  ?joinThread(draft.thread)
  :String(draft.body||'');
}
function draftLength(draft,text){
 if(draft.platform!=='x')return {count:text.length,note:''};
 const items=splitThread(text);
 const longest=items.reduce((most,item)=>Math.max(most,item.length),0);
 return {count:longest,note:`${items.length} post${items.length===1?'':'s'} · longest `};
}
function draftBlock(article,platform,draft){
 const meta=PLATFORMS.find(item=>item.key===platform);
 const head=`<div class="draft-head"><span class="draft-name">
<span class="draft-mark ${esc(platform)}" aria-hidden="true">${esc(meta.mark)}</span>${esc(meta.label)}</span>`;
 if(!draft){
  return `<div class="draft" data-draft="${esc(article.task_id)}:${esc(platform)}">${head}
${pill('draft','no copy written yet')}</div>
<p class="draft-note">Write the copy below and this becomes editable.</p></div>`;
 }
 const status=draft.status==='queued'?'queued':draft.status==='failed'?'failed_send':'draft';
 const text=draftText(draft);
 const measured=draftLength(draft,text);
 const over=measured.count>meta.limit;
 const producer=draft.producer==='writer'
  ?'written by the writer'
  :'assembled from the article — read it before sending';
 const tail=draft.status==='queued'
  ? `<p class="draft-note">Queued in Buffer${draft.scheduled_at?` for ${esc(draft.scheduled_at)}`:''}, sent by ${esc(draft.sent_by||'someone')}. Edit it in Buffer, not here.</p>
<div class="thread-text">${esc(text)}</div>`
  : `<textarea data-draft-body="${esc(article.task_id)}:${esc(platform)}" spellcheck="true"
aria-label="${esc(meta.label)} copy">${esc(text)}</textarea>
${platform==='x'?`<p class="draft-note">Separate thread posts with a line containing only ${THREAD_SEPARATOR}.</p>`:''}
${platform==='instagram'?'<p class="draft-note">Instagram needs the cover image, and captions carry no live link — say the article is linked in bio.</p>':''}
<div class="draft-foot"><span class="counter${over?' over':''}">${esc(measured.note)}${grouped.format(measured.count)} / ${grouped.format(meta.limit)}</span>
<button class="ghost small" data-draft-save="${esc(article.task_id)}:${esc(platform)}" type="button">Save copy</button></div>`;
 return `<div class="draft ${draft.status==='queued'?'is-queued':draft.status==='failed'?'is-failed':''}"
data-draft="${esc(article.task_id)}:${esc(platform)}">${head}
<span class="meta">${pill(status)} ${esc(producer)}</span></div>
${draft.error?`<p class="draft-note">${esc(draft.error)}</p>`:''}
${tail}</div>`;
}
function socialCard(article){
 const drafts={};
 for(const draft of article.drafts||[])drafts[draft.platform]=draft;
 const written=Object.keys(drafts).length;
 const queued=(article.drafts||[]).filter(draft=>draft.status==='queued').length;
 /* What is left to send. A card whose three posts are all in Buffer has nothing
    to prepare, and offering it anyway is a button that can only ever fail. A
    refused draft still counts: retrying it is exactly what the button is for. */
 const pending=(article.drafts||[]).filter(draft=>draft.status!=='queued').length;
 const plan=socialPlans[article.task_id];
 const planned=plan?`<div class="inline-form" data-social-plan="${esc(article.task_id)}">
<p class="meta">This will queue ${grouped.format(plan.platforms.length)} post${plan.platforms.length===1?'':'s'} in Buffer — ${esc(plan.platforms.map(key=>(PLATFORMS.find(item=>item.key===key)||{}).label||key).join(', '))} — to publish in your own posting slots.</p>
${(plan.notes||[]).map(note=>`<p class="meta">${esc(note)}</p>`).join('')}
<div class="actions"><button data-social-send="${esc(article.task_id)}" type="button">Approve &amp; schedule</button>
<button class="ghost" data-social-cancel="${esc(article.task_id)}" type="button">Not now</button></div></div>`:'';
 /* The key is the article and nothing else. `patchRows` matches a rendered row
    to its entry by this exact attribute and removes any child whose key is not
    in the incoming set -- so a key carrying the card's own state matches nothing
    and the whole list disappears on the first background repaint. State does not
    belong here: patchRows already compares the markup byte for byte, which is
    what decides whether the row is rebuilt. */
 return `<article class="card" role="listitem" data-key="social-${esc(article.task_id)}" data-row="social-${esc(article.task_id)}">
<div class="card-row"><div class="card-main">
<h3>${esc(article.title||article.task_id)}</h3>
<p class="meta">${esc(article.task_id)}${article.url?` · <a href="${esc(article.url)}" target="_blank" rel="noopener">${esc(String(article.url).replace(/^https?:\/\//,''))}</a>`:''}</p>
</div><div class="card-figures">
<span><span class="stat">${grouped.format(queued)}</span><span class="label">queued</span></span>
<span><span class="stat">${grouped.format(written)}</span><span class="label">drafts</span></span>
</div></div>
<div class="drafts">${PLATFORMS.map(meta=>draftBlock(article,meta.key,drafts[meta.key])).join('')}</div>
${planned}
<div class="send-bar">
<button class="ghost" data-social-generate="${esc(article.task_id)}" type="button">${written?'Rewrite the copy':'Write the copy'}</button>
${pending&&!plan?`<button data-social-prepare="${esc(article.task_id)}" type="button">Prepare send</button>`:''}
<span class="meta">${queued===3?'Every platform has been queued.':'Nothing is sent until you approve it.'}</span>
</div>
<p class="row-error" data-card-error hidden></p></article>`;
}
function renderSocial(){
 const social=state.social||{};
 const all=socialArticles();
 const search=(ui.social.search||'').trim().toLowerCase();
 const filter=ui.social.filter||'all';
 const status=article=>{
  const drafts=article.drafts||[];
  if(!drafts.length)return 'none';
  if(drafts.some(draft=>draft.status==='failed'))return 'failed';
  if(drafts.every(draft=>draft.status==='queued'))return 'queued';
  return 'ready';
 };
 const counts={all:all.length,none:0,ready:0,queued:0,failed:0};
 for(const article of all)counts[status(article)]+=1;
 chipRow('#social-filter',[
  {value:'all',label:'All',count:counts.all},
  {value:'none',label:'No copy yet',count:counts.none},
  {value:'ready',label:'Ready to send',count:counts.ready},
  {value:'queued',label:'Queued',count:counts.queued},
  {value:'failed',label:'Refused',count:counts.failed}
 ],filter,'social-filter');
 const matched=all.filter(article=>{
  if(filter!=='all'&&status(article)!==filter)return false;
  if(!search)return true;
  return `${article.title} ${article.task_id} ${article.slug}`.toLowerCase().includes(search);
 });
 const view=page(matched,'social');
 $('#social-count').textContent=`${grouped.format(matched.length)} of ${grouped.format(all.length)}`;
 $('#buffer-state').textContent=social.connected
  ?'Buffer is connected.'
  :'Buffer is not connected — set BUFFER_ACCESS_TOKEN and BUFFER_ORGANIZATION_ID.';
 /* The badge counts work waiting on him, not arrivals: articles that are live
    and have something still to send. An article with nothing written is one of
    them, because writing the copy is the outstanding thing. */
 const badge=document.querySelector('[data-badge="social"]');
 if(badge){
  const waiting=counts.none+counts.ready+counts.failed;
  badge.hidden=!waiting||currentView==='social';
  badge.textContent=waiting?String(waiting):'';
 }
 patchRows($('#social-list'),view.items.map(article=>({key:`social-${article.task_id}`,html:socialCard(article)})),
  emptyState(all.length?'Nothing matches that':'No article is live yet',
   all.length
    ?'Clear the search or choose a different filter.'
    :'An article appears here once Gate 2 merges it and a reader can open it. Until then a social post would link to a page that is not there.'));
 renderPager('#social-pager','social',view,'articles');
}
/* The live character count, updated as he types. It reads the same limits the
   server checks against, so a draft that looks acceptable here is one the send
   will accept -- and one that does not is refused before Buffer is asked. */
function updateCounter(box){
 const [,platform]=String(box.dataset.draftBody||'').split(':');
 const meta=PLATFORMS.find(item=>item.key===platform);
 const node=box.closest('.draft')?.querySelector('.counter');
 if(!meta||!node)return;
 const measured=draftLength({platform},box.value);
 node.textContent=`${measured.note}${grouped.format(measured.count)} / ${grouped.format(meta.limit)}`;
 node.classList.toggle('over',measured.count>meta.limit);
}
async function generateSocial(taskId){
 if(busy)return;
 const card=document.querySelector(`[data-row="social-${taskId}"]`);
 const action=runAction({
  button:document.querySelector(`[data-social-generate="${taskId}"]`),
  label:'Writing…',
  surface:card?.querySelector('[data-card-error]'),
  failTitle:'The copy was not written.'
 });
 try{
  await post('/ceo/api/social/generate',{task:taskId});
  delete socialPlans[taskId];
  toast('Three drafts written. Read them before sending.');
  await refresh();
 }catch(error){action.fail(error.message);}
 finally{action.done();}
}
async function saveSocialDraft(key){
 if(busy)return;
 const [taskId,platform]=key.split(':');
 const box=document.querySelector(`[data-draft-body="${key}"]`);
 if(!box)return;
 const card=document.querySelector(`[data-row="social-${taskId}"]`);
 const text=box.value;
 const action=runAction({
  button:document.querySelector(`[data-draft-save="${key}"]`),
  label:'Saving…',
  surface:card?.querySelector('[data-card-error]'),
  shape:'row-h',
  failTitle:'That edit was not saved.'
 });
 try{
  const thread=platform==='x'?splitThread(text):[];
  await post('/ceo/api/social/draft',{
   task:taskId,platform,
   body:platform==='x'?(thread[0]||''):text,
   thread
  });
  /* Editing copy invalidates a prepared send: the instruction was minted
     against the article as it stood, and the server checks that. */
  delete socialPlans[taskId];
  toast('Saved.');
  await refresh();
 }catch(error){action.fail(error.message);}
 finally{action.done();}
}
async function prepareSocial(taskId){
 if(busy)return;
 const card=document.querySelector(`[data-row="social-${taskId}"]`);
 const action=runAction({
  button:document.querySelector(`[data-social-prepare="${taskId}"]`),
  label:'Checking…',
  surface:card?.querySelector('[data-card-error]'),
  shape:'row-h',
  failTitle:'Buffer could not be asked.'
 });
 try{
  const check=await api(`/ceo/social-check?task=${encodeURIComponent(taskId)}`);
  if(!check.eligible||!check.request_id){
   action.fail((check.blockers||[]).concat(check.notes||[]).join(' · ')||'Nothing can be sent for this article right now.');
   return;
  }
  socialPlans[taskId]={request_id:check.request_id,platforms:check.sendable||[],notes:check.notes||[]};
  renderSocial();
 }catch(error){action.fail(error.message);}
 finally{action.done();}
}
async function sendSocial(taskId){
 if(busy)return;
 const plan=socialPlans[taskId];
 const card=document.querySelector(`[data-row="social-${taskId}"]`);
 if(!plan){notice('Prepare the send again — that instruction is gone.',true);return;}
 const action=runAction({
  button:document.querySelector(`[data-social-send="${taskId}"]`),
  label:'Scheduling…',
  surface:card?.querySelector('[data-card-error]'),
  failTitle:'Buffer did not take the posts.'
 });
 try{
  const result=await post('/ceo/api/social/send',
   {task:taskId,request_id:plan.request_id,platforms:plan.platforms});
  /* An instruction is single use whatever happened to it, so it goes either way. */
  delete socialPlans[taskId];
  const queued=(result.queued||[]).length;
  if((result.failed||[]).length){
   /* A partial send is reported as one, on screen, naming both halves. A toast
      saying "done" over two posts that went and one that did not is a lie. */
   action.fail(`Queued ${queued}. Refused: ${(result.failed||[]).map(item=>`${item.platform} — ${item.error}`).join(' · ')}`);
  }else{
   toast(`Queued ${queued} post${queued===1?'':'s'} in Buffer.`);
  }
  await refresh();
 }catch(error){delete socialPlans[taskId];action.fail(error.message);}
 finally{action.done();}
}
function gapRow(finding){
 const position=finding.our_position==null?'no Search Console data for this topic'
  :`we average position ${Number(finding.our_position).toFixed(1)}${finding.our_impressions!=null?` on ${finding.our_impressions} impressions`:''}`;
 return `<article class="card" role="listitem" data-row="gap-${esc(finding.topic)}">
<div class="card-row"><div class="card-main">${pill(finding.kind)}
<h3>${esc(finding.topic)}</h3>
<p class="meta">Them: <a href="${esc(finding.their_url)}" target="_blank" rel="noopener">${esc(String(finding.their_url).replace(/^https?:\/\//,'').slice(0,70))}</a></p>
<p class="meta">Us: ${esc(position)}</p>
<p class="outline">${esc(finding.recommendation)}</p></div>
<button class="ghost small" data-queue="${esc(finding.topic)}" data-queue-action="add" data-queue-reason="${esc(finding.recommendation)}" type="button">Research this</button></div>
<p class="row-error" data-card-error hidden></p></article>`;
}
function renderCompetitor(){
 const data=state.analytics?.competitor||{};
 const node=$('#competitor-panel');
 if(data.status==='none'){
  setHtml(node,emptyState('No competitor analysed yet','Enter a website above to see which of their topics we do not cover.','Enter a website','data-focus="competitor"'));
  setHtml($('#competitor-pager'),'');
  return;
 }
 const counts=(data.findings||[]).reduce((total,item)=>{total[item.kind]=(total[item.kind]||0)+1;return total;},{});
 const chips=['uncontested','weak_position','covered'].filter(kind=>counts[kind])
  .map(kind=>pill(kind,`${counts[kind]} ${STATUS[kind].label}`)).join(' ');
 const cost=data.credits_used?`${data.credits_used} credits`:'no credits';
 const view=page(data.findings||[],'competitor');
 setHtml(node,`<p class="meta">${esc(data.domain)} · <span class="num">${esc(data.sitemap_url_count??0)}</span> pages in their sitemap (free) · <span class="num">${esc(data.pages_fetched??0)}</span> read for ${esc(cost)} · measured ${esc(data.measured_at||'—')}</p>
${data.message?`<p class="meta">${esc(data.message)}</p>`:''}
<p class="meta">${esc(data.volume_message||'')}</p>
<div class="keywords">${chips}</div>
<div class="rows" role="list">${view.items.map(gapRow).join('')||emptyState('No comparable topic','Their pages produced no topic we could score against ours.')}</div>`);
 renderPager('#competitor-pager','competitor',view,'findings');
}
async function analyseCompetitor(){
 const target=$('#competitor').value.trim();
 const line=$('#competitor-result');
 if(!target){line.hidden=false;line.classList.add('error');line.textContent='Enter a competitor website first.';$('#competitor').focus();return;}
 if(busy)return;
 line.classList.remove('error');
 line.hidden=false;
 line.textContent='Reading their sitemap, then up to 10 of their pages.';
 const action=runAction({
  button:'#analyse-competitor',label:'Analysing…',
  slot:'#competitor-panel',shape:'card-h',count:4,surface:line,
  failTitle:'The competitor read did not finish.'
 });
 try{
  const result=await post('/ceo/api/competitor',{target});
  setUi('competitor',{page:1});
  await refresh();
  line.classList.remove('error');
  line.textContent=`${result.domain}: ${(result.findings||[]).length} topics scored for ${result.credits_used} credits.`;
 }catch(error){action.fail(error.message);}
 finally{action.done();}
}

function renderSkeletons(){
 setHtml($('#proposal-list'),skeleton(3,'card-h'));
 setHtml($('#blog-list'),skeleton(3,'card-h'));
 setHtml($('#opportunity-list'),skeleton(3,'card-h'));
 setHtml($('#stat-tiles'),skeleton(5,'tile-h'));
 setHtml($('#chart'),skeleton(1,'chart-h'));
 setHtml($('#trend-list'),skeleton(3,'row-h'));
 setHtml($('#competitor-panel'),skeleton(2,'card-h'));
 setHtml($('#archived-list'),skeleton(2,'card-h'));
 setHtml($('#social-list'),skeleton(2,'card-h'));
 setHtml($('#sources-panel'),skeleton(1,'card-h'));
 setHtml($('#places-panel'),skeleton(1,'card-h'));
 setHtml($('#devices-panel'),skeleton(1,'card-h'));
 setHtml($('#journey-panel'),skeleton(1,'card-h'));
}
function renderAll(){
 renderProposals();renderArchived();renderTrends();renderBlogs();renderSearchConsole();renderPosts();
 renderGa4();renderSources();renderPlaces();renderDevices();renderJourney();renderSocial();
 renderCompetitor();applyFocus();
}

/* ------------------------------------------------------------- blog reading */
async function hydrateImages(){
 for(const frame of $$('#detail-body [data-image-url]')){
  try{
   const response=await api(frame.dataset.imageUrl,{raw:true});
   const blob=await response.blob();
   const image=document.createElement('img');
   image.alt='';
   image.src=URL.createObjectURL(blob);
   frame.replaceChildren(image);
  }catch(error){frame.textContent='This image could not be loaded.';}
 }
}
function reviewNotesHtml(task){
 const notes=task.article?.review_notes_html;
 if(!notes)return '';
 const titles=(task.article?.review_note_titles||[]).join(' · ');
 return `<details class="review-notes"><summary>Review notes — not part of the article</summary>
<div class="body"><p class="meta">The writer leaves these for whoever reviews the piece: ${esc(titles||'working notes')}. They are not published.</p>${notes}</div></details>`;
}
function detailRead(task){
 if(editing)return editorHtml(task);
 const article=task.article;
 if(!article)return emptyState('No article on this card','This card has no attached article yet.');
 return `<div class="reader-bar">
<button class="ghost small" data-reader="edit" type="button">Edit</button>
<button class="ghost small" data-reader="download" type="button">Download Markdown</button>
<button class="ghost small" data-reader="print" type="button">Print or save as PDF</button>
<span class="meta"><span class="num">${grouped.format(article.word_count||0)}</span> words · <span class="num">${article.read_minutes||0}</span> min read${(article.revisions||[]).length?` · <span class="num">${article.revisions.length}</span> earlier version${article.revisions.length===1?'':'s'} kept`:''}</span>
</div>
<article class="article-sheet">${article.html||'<p>This article is empty.</p>'}</article>
${reviewNotesHtml(task)}
${decisionHtml(task)}
${blogPublishHtml(task)}`;
}
function editorHtml(task){
 return `<div class="editor">
<p class="editor-conflict" id="editor-conflict" role="status" hidden></p>
<p class="meta">Saving writes a new revision. The version on screen now is kept as a numbered file, and the change is recorded in the thread as your edit — it does not approve anything.</p>
<div class="editor-grid">
<div class="editor-pane"><span class="label">Markdown source</span>
<label class="field"><span class="visually-hidden">Article Markdown</span><textarea id="editor-input" spellcheck="true">${esc(editorText)}</textarea></label></div>
<div class="editor-pane"><span class="label">Preview</span>
<div class="preview" id="editor-preview">${task.article?.html||''}</div></div>
</div>
<div class="editor-bar">
<button data-editor="save" type="button">Save revision</button>
<button class="ghost" data-editor="cancel" type="button">Cancel</button>
<span class="meta" id="editor-state"></span>
</div></div>`;
}
function schedulePreview(){
 clearTimeout(previewTimer);
 previewTimer=setTimeout(async()=>{
  const target=$('#editor-preview');if(!target)return;
  try{
   const result=await post('/ceo/api/article/preview',{text:editorText});
   target.innerHTML=result.html||'<p class="meta">Nothing to preview yet.</p>';
   const line=$('#editor-state');if(line)line.textContent='Preview updated.';
  }catch(error){const line=$('#editor-state');if(line)line.textContent='Preview unavailable: '+error.message;}
 },350);
}
async function saveEdit(task){
 if(busy)return;
 const action=runAction({
  button:document.querySelector('[data-editor="save"]'),label:'Saving…',
  surface:'#editor-state',failTitle:'The revision was not saved.'
 });
 try{
  const result=await post('/ceo/api/article/edit',{task_id:task.id,text:editorText});
  toast(`Saved as revision ${result.revision_round}. The previous version is kept as ${result.archived_as}.`);
  editing=false;editorText='';editorBase='';
  await refresh();
  await renderDetail(true);
 }catch(error){action.fail(error.message);}
 finally{action.done();}
}
function cancelEdit(task){
 if(editorText!==editorBase&&!confirm('Discard your edit?'))return;
 editing=false;editorText='';editorBase='';renderDetail(true);
}
/* Someone else saved this article while he has it open with unsaved text. His
   textarea is not touched: the only correct move is to tell him and stop. */
function showEditorConflict(){
 const line=$('#editor-conflict');if(!line)return;
 line.hidden=false;
 line.textContent='This article changed elsewhere. Save yours, or reload to see theirs.';
}
/* Everything needed to ship this article, on the tab that holds the article.
   Publishing stops at the preview: cmo-changes, then a human merges the pull
   request on GitHub. There is no merge-to-main control on this console at all —
   the one that used to live here is gone, not moved. */
function blogPublishHtml(task){
 const item=task.publishing_pipeline||{};
 const commit=item.commit||'';
 const preview=task.blog?.url||item.preview_url||'';
 const impact=`<p class="meta">Expected impact: ${cell(task.metric||task.declared_metric)}</p>`;
 /* Already pushed. The control that performed the push has nothing left to do,
    so what belongs here is where it landed — not a second button. */
 if(commit||preview){
  const open=preview
   ?`<div class="actions"><a class="ghost small" href="${esc(preview)}" target="_blank" rel="noopener">Open preview</a></div>`:'';
  return `<div class="publish" id="blog-publish-block" data-checked="1"><h4>Published</h4>
${impact}
<p class="meta" id="blog-publish-state">Pushed to <span class="num">cmo-changes</span>${commit?` at <span class="num">${esc(String(commit).slice(0,7))}</span>`:''}.</p>
${open}
<p class="meta">A human merges the pull request on GitHub. This console never touches <span class="num">main</span>.</p></div>`;
 }
 /* Publish is refused outside Human Approval server-side, twice. Drawing a
    button here whose only possible outcome is a refusal would be the same lie
    the decision controls used to tell on the Discussion tab. */
 if(String(task.board_section||task.status||'').trim()!=='Human Approval')return '';
 return `<div class="publish" id="blog-publish-block"><h4>Publish to website</h4>
${impact}
<p class="meta" id="blog-publish-state">Checking whether this article can be published…</p>
<div id="blog-publish-files"></div>
${publishDateHtml(task)}
<div class="actions"><button data-blog-publish="1" type="button" disabled>Publish to website</button></div>
<p class="meta">This records your approval in <span class="num">approvals.log</span>, then writes the blog page, its index entry and its diagram and pushes them to <span class="num">cmo-changes</span>. It does not touch <span class="num">main</span> — a human merges the pull request on GitHub after seeing the preview. Your name is recorded in the commit trailer.</p></div>`;
}
/* A day, written down. Nothing on this box fires on it — there is no cron here
   and no scheduler — so this says "planned", never "will publish". Saying the
   second would be promising an unattended publish that no code performs, and
   that publish is a human press by design. */
function publishDateHtml(task){
 const planned=(task.publish_at||'').trim();
 return `<div class="publish-date"><label class="field"><span>Planned publish date</span>
<input type="date" data-publish-date="${esc(task.id)}" value="${esc(planned)}"></label>
<p class="meta">A note to yourself, shown on the Blogs list as <em>Scheduled</em>. Nothing publishes on its own — the button below is still the press that ships it.</p></div>`;
}
function blogPublishFilesHtml(check){
 if(!check.files||!check.files.length)return '';
 return `<ul class="files">${check.files.map(name=>`<li><span class="num">${esc(name)}</span></li>`).join('')}</ul>`;
}
/* The eligibility check reads the board, converts the article and asks the git
   remote where cmo-changes is. Any of those can be slow, and one of them can hang.
   A hung check used to leave "Checking whether this article can be published…" on
   screen with no end and no reason, which is indistinguishable from a broken
   console. It now gives up out loud and offers to try again. */
let CHECK_TIMEOUT_MS=15000;
function withDeadline(promise,ms,message){
 return new Promise((resolve,reject)=>{
  const timer=setTimeout(()=>reject(new Error(message)),ms);
  promise.then(value=>{clearTimeout(timer);resolve(value);},
               error=>{clearTimeout(timer);reject(error);});
 });
}
/* A block still sitting on its placeholder has not been answered. renderDetail
   skips a repaint whose markup is unchanged, and skipping the repaint used to skip
   the check with it, so a check that never landed was never retried either. */
function publishCheckPending(){
 const block=$('#blog-publish-block');
 return Boolean(block)&&block.dataset.checked!=='1';
}
async function refreshBlogPublish(task){
 const block=$('#blog-publish-block');if(!block)return;
 const line=$('#blog-publish-state'),button=block.querySelector('[data-blog-publish]');
 /* The published block wears the same id and carries no button. There is
    nothing left to ask the remote about it. */
 if(!button)return;
 try{
  const check=await withDeadline(
   api('/ceo/blog-publish-check?task='+encodeURIComponent(task.id)),
   CHECK_TIMEOUT_MS,
   'the check did not answer in time'
  );
  blogPublishRequest=check.request_id||'';
  setHtml($('#blog-publish-files'),blogPublishFilesHtml(check));
  if(check.eligible){
   line.textContent=`Ready to publish as /blog/${check.slug} in ${check.category}.`;
   button.disabled=false;
  }else{
   line.innerHTML='Cannot publish yet:<ul>'+check.blockers.map(reason=>`<li>${esc(reason)}</li>`).join('')+'</ul>';
   button.disabled=true;
  }
 }catch(error){
  line.innerHTML=`<span class="error">Could not check whether this can be published: ${esc(error.message)}.</span> `
   +'<button class="ghost small" data-recheck="1" type="button">Check again</button>';
  button.disabled=true;
 }finally{
  /* Answered either way. Never left implying a check is still running. */
  block.dataset.checked='1';
 }
}
async function publishBlog(task){
 const line=$('#blog-publish-state');
 if(!blogPublishRequest){
  if(line)line.textContent='This card has no current publish instruction. Close this article and open it again.';
  return;
 }
 if(!confirm('Publish '+task.id+' to cmo-changes? This does not merge to main.'))return;
 const action=runAction({
  button:document.querySelector('#blog-publish-block [data-blog-publish]'),label:'Publishing…',
  surface:line,failTitle:'The publish did not go through.'
 });
 try{
  const outcome=await post('/ceo/blog-publish',{task:task.id,request_id:blogPublishRequest});
  blogPublishRequest='';
  toast('Pushed to cmo-changes at '+(outcome.commit||'').slice(0,7)+'.');
  await refresh();await renderDetail(true);
 }catch(error){
  action.fail(error.message);blogPublishRequest='';
 }finally{action.done();}
}
/* Why a card cannot be decided yet, in the words its own state warrants. Every
   one of these ends by saying when it *will* come to him, because "you cannot act
   on this" without "here is when you can" is just a dead end. */
const NOT_YET_DECIDABLE={
 queued:'Queued to be written. It will come to you once the article exists.',
 researching:'Being written now. It will come to you when it is finished.',
 writing:'Being written now. It will come to you when it is finished.',
 rewriting:'Being edited. The new version will come to you when it is done.',
 checking:'Waiting for review. It will come to you when review finishes.',
 failed:'This could not be written, so there is nothing to decide yet. Retry it from the Blogs list.',
 held:'On hold. It will come to you once it is released.',
 in_preview:'Published to cmo-changes and waiting on a merge to main. The decision on it is already recorded.',
 published:'Published. The decision on it is already recorded.'
};
/* The change request, on the tab that holds the article.

   `request_revision` refuses any card that is not in Human Approval, and it does
   not fail quietly on the ones it accepts: it sets `revision requested` on a card
   that may never have reached him, which the content worker then picks up and
   rewrites. So the field appears only where a change can actually be asked for.
   This is the courtesy; the guard is server-side and proved separately. */
function decisionHtml(task){
 const thread=(task.approval_thread||[]).map(event=>`<div class="history-row"><span class="meta">Round ${esc(event.round)} · ${esc(event.type)}</span><p>${esc(event.text)}</p></div>`).join('');
 const surfaces=`<div id="detail-pending" class="rows" aria-live="polite" hidden></div>
<p class="row-error" id="detail-error" role="alert" hidden></p>`;
 const history=thread?`<h3>Thread</h3>${thread}`:'';
 const round=`<p class="meta">Revision round: <span class="num">${esc(task.revision_round||'0')}</span>.</p>`;
 const section=String(task.board_section||task.status||'').trim();
 /* Why it cannot be acted on yet, in the words its own state warrants — and
    always ending with when it *will* come to him. "You cannot act on this"
    without "here is when you can" is just a dead end. */
 if(section!=='Human Approval'){
  const state=task.blog?.state||'';
  const line=NOT_YET_DECIDABLE[state]
   ||`In ${section||'another lane'}. It will come to you when it reaches your approval.`;
  const reason=task.blog?.reason?`<p class="meta">${esc(task.blog.reason)}</p>`:'';
  return `<h3>Decision</h3><p>${esc(line)}</p>${reason}${surfaces}${round}${history}`;
 }
 /* A decision that still describes this article closes the door on a revision —
    the server refuses one, so the field would be a control that cannot work. A
    decision the article has outgrown does not: publishing records a fresh one. */
 if(task.decision_approved&&!task.decision_stale){
  const record=task.decision_summary||{};
  const decided=record.approver_id?` by ${esc(record.approver_id)}`:'';
  const when=record.timestamp?` on ${esc(record.timestamp)}`:'';
  return `<h3>Decision</h3><p>Approved${decided}${when}.</p>
<p class="meta">A change request is refused once a decision exists, so this article can no longer be sent back from here.</p>${surfaces}${history}`;
 }
 /* Approved once, and then the article moved. Publishing records a fresh
    decision over what is on screen now, so this is no longer the deadlock it
    used to be — but he still has to be told that the old approval does not
    describe the article he is reading. */
 let stale='';
 if(task.decision_stale){
  const record=task.decision_summary||{};
  const decided=record.approver_id?` by ${esc(record.approver_id)}`:'';
  const when=record.timestamp?` on ${esc(record.timestamp)}`:'';
  const changes=(task.decision_change||[]).map(line=>`<li>${esc(line)}</li>`).join('');
  stale=`<h3>Decision</h3><p>Approved${decided}${when}, <strong>but the article has changed since</strong>, so that approval no longer covers it.</p>
${changes?`<p class="meta">What changed:</p><ul class="meta">${changes}</ul>`:''}
<p class="meta">Publishing records a new decision over the article as it stands now and keeps the old one; nothing is overwritten.</p>`;
 }
 return `${stale}<h3>Ask for changes</h3>
<label class="field"><span class="visually-hidden">What needs to change</span><textarea id="revision-comment" rows="3" placeholder="State the exact change needed"></textarea></label>
<div class="actions"><button class="ghost" data-revision="1" type="button">Ask for changes</button></div>
${surfaces}
<p class="meta">This sends the article back to the agent to rewrite and keeps the card in this lane.</p>${round}${history}`;
}
function detailFiles(task){
 const files=(task.article?.files||[]).map(file=>`<div class="list-row"><span>${esc(file.name)} · <span class="meta">${esc(file.kind)}</span></span><span class="meta num">${grouped.format(file.bytes)} bytes</span></div>`).join('');
 const revisions=(task.article?.revisions||[]).map(item=>`<div class="list-row"><span>${esc(item.name)} · <span class="meta">revision ${esc(item.round)}</span></span><span class="meta num">${grouped.format(item.bytes)} bytes</span></div>`).join('');
 const slots=(task.article?.image_slots||[]).map(imageSlotRow).join('');
 const cover=task.article?.cover?imageSlotRow(task.article.cover):'';
 return `<h3>Files</h3><div class="rows">${files||'<p class="empty">No files.</p>'}</div>
<h3>Earlier versions</h3><div class="rows">${revisions||'<p class="empty">No revision has been written yet.</p>'}</div>
<h3>Cover image</h3><div class="rows">${cover||'<p class="empty">This card has no article yet.</p>'}</div>
<h3>Image slots</h3><div class="rows">${slots||'<p class="empty">The article declares no image slots.</p>'}</div>
<p class="meta">Uploads: PNG, JPG, JPEG, WEBP or GIF, maximum 5 MB. SVG is not accepted for upload.</p>
<p class="meta">Generating asks the image model for a new picture from the description and binds it here. It costs a fraction of a dollar per image and is recorded in the spend ledger. A diagram slot is drawn by the writer, not generated.</p>`;
}
/* One row per image the card can carry: what is bound, the description it was
   drawn from, and the two ways to change it. The description is editable because
   the first thing anyone wants after seeing a generated picture is to say what was
   wrong with it. */
function imageSlotRow(slot){
 const bound=slot.bound?esc(slot.filename):'no image bound';
 const preview=slot.bound?`<img class="slot-thumb" src="${esc(slot.url)}" alt="" loading="lazy">`:'';
 const diagram=slot.kind==='diagram';
 const altField=slot.kind==='illustration'
  ?`<label class="field"><span class="visually-hidden">Alt text for ${esc(slot.id)}</span><input data-alt="${esc(slot.id)}" type="text" placeholder="Alt text: what the picture shows" value="${esc(slot.alt||'')}"></label>`
  :'';
 const generate=diagram
  ?'<span class="meta">Drawn by the writer as SVG; not generated.</span>'
  :`<button class="ghost small" data-generate="${esc(slot.id)}" type="button">${slot.bound?'Regenerate':'Generate'}</button>`;
 const describe=diagram
  ?''
  :`<label class="field"><span class="visually-hidden">Describe the image for ${esc(slot.id)}</span><textarea data-scene="${esc(slot.id)}" rows="2" placeholder="Describe the scene: what is visible, no text or logos">${esc(slot.prompt||'')}</textarea></label>${altField}`;
 return `<div class="list-row slot-row"><div class="slot-main">${preview}<span>${esc(slot.caption)} · <span class="meta">${bound}</span></span></div>
${describe}
<div class="actions">${generate}<label class="ghost small" style="cursor:pointer">Bind image<input data-upload="${esc(slot.id)}" type="file" accept=".png,.jpg,.jpeg,.webp,.gif" hidden></label></div></div>`;
}
/* `force` is for a tab or mode change, where the body must be rebuilt. Left alone,
   this paints only when the markup actually differs, and puts the reading position
   back where it was — a background update must not scroll the open article. */
async function renderDetail(force=false){
 const task=findTask(openTask);if(!task)return;
 $('#detail-id').textContent=task.id;$('#detail-title').textContent=task.title||task.id;
 paintTitleControl(task);
 $$('.nested button').forEach(node=>node.classList.toggle('active',node.dataset.detail===detailTab));
 const body=$('#detail-body');
 /* Two tabs. Anything else — a stale value, an old link — is Read. */
 if(detailTab!=='files')detailTab='read';
 const render={read:detailRead,files:detailFiles}[detailTab];
 if(force)painted.delete(body);
 const where=body?body.scrollTop||0:0;
 const repainted=setHtml(body,render(task));
 if(repainted){
  if(body&&where)body.scrollTop=where;
  if(detailTab==='read'&&!editing)await hydrateImages();
  if(detailTab==='read'&&editing)$('#editor-input')?.focus();
 }
 /* Publish eligibility asks the git remote, so it runs on a repaint — and on any
    render where the block is still unanswered, so a check that never landed gets
    another chance instead of leaving the placeholder up for good. */
 if(detailTab==='read'&&!editing&&(repainted||publishCheckPending())){
  await refreshBlogPublish(task);
 }
}
/* ------------------------------------------------------- renaming an article */
/* A blog title is written down four times — the card heading, the card's Title
   field, the article's front-matter `title:` that the published page uses, and the
   article's own H1 — and nothing kept them in step. The pencil moves all four in one
   press, through the same revision and the same refusals as any other article edit.

   It is offered only where the rename will be accepted. An approved article is
   closed to it, because the headline is part of what was approved; saying so on the
   disabled button beats a control that fails when pressed. */
let renamingTitle=false;
function titleRefusal(task){
 if(!task)return 'No card is open.';
 if(!task.article)return 'This card has no article to retitle yet.';
 if(task.decision_approved&&!task.decision_stale)
  return 'This article carries a human decision. Ask for a revision to reopen it.';
 return '';
}
function paintTitleControl(task){
 const button=$('#edit-title');if(!button)return;
 const reason=titleRefusal(task);
 button.hidden=!task||!task.article;
 button.disabled=Boolean(reason);
 button.title=reason||'Edit title';
 button.setAttribute('aria-label',reason||'Edit title');
 if(!renamingTitle)closeTitleForm();
}
function closeTitleForm(){
 renamingTitle=false;
 const form=$('#title-form');if(form)form.hidden=true;
 const error=$('#title-error');if(error){error.hidden=true;error.textContent='';}
 const line=$('#title-state');if(line)line.textContent='';
}
function openTitleForm(){
 const task=findTask(openTask);
 if(!task||titleRefusal(task))return;
 renamingTitle=true;
 const form=$('#title-form');if(form)form.hidden=false;
 const input=$('#title-input');
 if(input){input.value=task.title||'';input.focus();input.select();}
 const error=$('#title-error');if(error){error.hidden=true;error.textContent='';}
}
async function saveTitle(){
 if(busy)return;
 const task=findTask(openTask);if(!task)return;
 const input=$('#title-input');
 const title=input?input.value.trim():'';
 const error=$('#title-error');
 const fail=message=>{if(error){error.hidden=false;error.textContent=message;}};
 if(!title){fail('Type a title.');input?.focus();return;}
 if(title===(task.title||'')){fail('That is already the title.');return;}
 if(error){error.hidden=true;error.textContent='';}
 const action=runAction({
  button:$('#title-save'),label:'Saving…',
  surface:'#title-state',failTitle:'The title was not changed.'
 });
 try{
  await post('/ceo/api/article/title',{task_id:task.id,title});
  toast('Renamed. The previous version of the article is kept.');
  closeTitleForm();
  await refresh();
  await renderDetail(true);
 }catch(err){fail(err.message);action.fail(err.message);}
 finally{action.done();}
}
/* The article exactly as it sits on disk, header included.
   `article.text` is the prose — what the reader renders and the search box reads —
   and posting that back to /ceo/api/article/edit is refused for having lost the
   front matter, which is what made Save revision fail on every article. Anything
   that means "the source file" goes through here. */
function articleSource(task){
 const article=task&&task.article;
 return article?(article.front_matter||'')+(article.text||''):'';
}
/* What a background update is allowed to do to an open card. */
async function syncDetail(){
 const task=findTask(openTask);
 if(!task)return;
 if(renamingTitle)return;
 if(!editing){await renderDetail();return;}
 const theirs=articleSource(task);
 if(theirs===editorBase)return;
 if(editorText!==editorBase){
  /* He has typed. Losing that once would end his trust in the console. */
  showEditorConflict();
  return;
 }
 /* Nothing of his to lose, so take theirs and say so. */
 editorBase=theirs;editorText=theirs;
 const input=$('#editor-input');if(input)input.value=theirs;
 const line=$('#editor-state');if(line)line.textContent='Updated to the version saved elsewhere.';
}
async function openDetail(id){
 openTask=id;detailTab='read';editing=false;editorText='';editorBase='';closeTitleForm();
 await renderDetail(true);$('#detail').showModal();
}
function closeDetail(){
 if(editing&&editorText!==editorBase&&!confirm('Discard your edit?'))return;
 openTask=null;editing=false;editorText='';editorBase='';closeTitleForm();$('#detail').close();
}
function downloadArticle(task){
 const blob=new Blob([articleSource(task)],{type:'text/markdown;charset=utf-8'});
 const link=document.createElement('a');
 link.href=URL.createObjectURL(blob);
 link.download=(task.article?.metadata?.slug||task.id)+'.md';
 link.click();setTimeout(()=>URL.revokeObjectURL(link.href),1000);
}

/* ------------------------------------------------------------------ loading */
function stateQuery(){
 const analytics=ui.analytics;
 const params=new URLSearchParams({range:analytics.range,device:analytics.device});
 if(analytics.range==='custom'){params.set('start',analytics.start||'');params.set('end',analytics.end||'');}
 return params.toString();
}
/* One refresh, two callers. `quiet` means nobody asked for this — it came from the
   version poller — so it must survive being unwelcome: no scroll moved, no open
   editor touched, no in-flight action interrupted, and the rows patched rather
   than repainted. Pagination, sort, filter and search all live in `ui`, which
   this never writes. */
async function refresh(quiet=false){
 if(quiet&&busy&&!liveWhileBusy)return;
 let next;
 try{next=await api('/ceo/api/state?'+stateQuery());}
 catch(error){if(!quiet)notice(error.message,true);return;}
 /* Read the scroll after the fetch, not before: if he scrolled while it was in
    the air that is where he wants to be, and only our own render may move him. */
 const scrolled=quiet?(window.scrollY||window.pageYOffset||0):0;
 const previous=state;
 state=next;
 if(quiet&&previous)markArrivals(previous,next);
 renderAll();
 if(openTask)await syncDetail();
 if(quiet&&window.scrollTo)window.scrollTo(0,scrolled);
 if(!quiet)notice('');
}

/* ------------------------------------------------------------ the one poller */
function schedulePoll(delay){
 clearTimeout(pollTimer);pollTimer=0;
 /* No point polling a phone in his pocket. visibilitychange starts it again. */
 if(document.hidden)return;
 pollTimer=setTimeout(pollVersion,delay===undefined?POLL_LADDER[pollStep]:delay);
}
async function pollVersion(){
 pollTimer=0;
 if(document.hidden)return;
 /* An action he started owns the screen until it finishes, unless it asked to
    be watched instead of waited on. */
 if(busy&&!liveWhileBusy){schedulePoll(POLL_LADDER[0]);return;}
 try{
  const result=await api('/ceo/api/version');
  pollStep=0;
  if(result.version&&result.version!==versionToken){
   versionToken=result.version;
   await refresh(true);
  }
 }catch(error){
  /* 3s → 6s → 12s → 30s, and back to 3s on the first success. A server that is
     restarting comes back; hammering it while it does helps nobody. */
  pollStep=Math.min(POLL_LADDER.length-1,pollStep+1);
 }
 schedulePoll();
}
function resumePolling(){
 if(document.hidden)return;
 pollStep=0;schedulePoll(0);
}
async function updateWatch(keyword,action){
 toast(action==='add'?'Added to the watchlist.':'Removed from the watchlist.');
 try{const result=await post('/ceo/api/watchlist',{keyword,action});state.watchlist=result.watchlist;renderTrends();}
 catch(error){toast(error.message,true);notice(error.message,true);}
}
async function revise(task){
 if(busy)return;
 const comment=$('#revision-comment').value;
 const action=runAction({
  button:document.querySelector('[data-revision]'),label:'Sending…',
  slot:'#detail-pending',shape:'row-h',count:1,surface:'#detail-error',
  failTitle:'The change request was not sent.'
 });
 try{await post('/ceo/api/revision',{task_id:task.id,comment});toast('Change requested.');closeDetail();await refresh();}
 catch(error){action.fail(error.message);}
 finally{action.done();}
}
async function generateImage(task,slot){
 if(busy)return;
 const scene=document.querySelector(`[data-scene="${slot}"]`)?.value||'';
 const alt=document.querySelector(`[data-alt="${slot}"]`)?.value||'';
 const action=runAction({
  button:document.querySelector(`[data-generate="${slot}"]`),label:'Generating…',
  failTitle:'The image was not generated.'
 });
 try{
  const result=await post('/ceo/api/generate-image',{task_id:task.id,slot,scene,alt});
  toast(`Image generated${result.cost_usd?` · $${result.cost_usd.toFixed(3)}`:''}.`);
  await refresh();openTask=task.id;detailTab='files';await renderDetail(true);
 }catch(error){action.fail(error.message);}
 finally{action.done();}
}
/* Writes the planned day, or clears it when the field is emptied. Not an action
   that ships anything, so it does not take over the screen the way runAction does
   -- a toast is the whole feedback a note deserves. */
async function savePublishDate(taskId,value){
 try{
  const result=await post('/ceo/api/publish-date',{task_id:taskId,publish_at:value});
  toast(result.publish_at?`Publish planned for ${result.publish_at}.`:'Publish date cleared.');
  await refresh();
 }catch(error){
  toast(error.message);
 }
}
async function upload(task,slot,file){
 if(busy)return;
 const action=runAction({
  button:document.querySelector(`[data-upload="${slot}"]`),label:'Uploading…',
  failTitle:'The image was not bound.'
 });
 try{
  await api(`/ceo/api/upload?task=${encodeURIComponent(task.id)}&slot=${encodeURIComponent(slot)}`,{method:'POST',headers:{'X-Filename':file.name},body:file});
  toast('Image bound to the slot.');
  await refresh();openTask=task.id;detailTab='files';await renderDetail(true);
 }catch(error){action.fail(error.message);}
 finally{action.done();}
}

/* ------------------------------------------------------------------- events */
document.addEventListener('click',event=>{
 /* A sortable header is a click target in its own right, padding included. */
 const header=event.target.closest('th[data-sort]');
 if(header){
  /* Three sortable tables now, so the key comes from the table rather than from
     a two-way guess -- adding the third to that ternary is exactly how it would
     have started sorting the wrong list. */
  const key={'queries-table':'queries','pages-table':'pages','posts-table':'posts'}[header.closest('table').id];
  if(!key)return;
  const field=header.dataset.sort;
  const same=ui[key].sort===field;
  setUi(key,{sort:field,dir:same&&ui[key].dir==='desc'?'asc':'desc',page:1});
  if(key==='posts')renderPosts();else renderSearchConsole();
  return;
 }
 const button=event.target.closest('button');
 if(!button)return;
 const data=button.dataset;
 if(data.view)showView(data.view);
 if(data.focus){showView(data.focus==='competitor'?'analytics':'topics');$('#'+data.focus)?.focus();}
 if(data.open)openDetail(data.open);
 if(data.detail){detailTab=data.detail;renderDetail(true);}
 if(data.generate)generateImage(findTask(openTask),data.generate);
 if(data.arrivals)showArrivals(data.arrivals);
 if(data.clear){setUi(data.clear,{search:'',filter:'all',page:1});$(`#${data.clear}-search`).value='';renderAll();}
 if(data.page){const [key,value]=data.page.split(':');setUi(key,{page:Number(value)},false);renderAll();}
 if(data.topicsFilter!==undefined){setUi('topics',{filter:data.topicsFilter});renderProposals();}
 if(data.blogsFilter!==undefined){setUi('blogs',{filter:data.blogsFilter});renderBlogs();}
 if(data.range!==undefined){
  setUi('analytics',{range:data.range},false);
  if(data.range!=='custom')refresh();else{renderRangeChips();$('#range-start')?.focus();}
 }
 if(data.device!==undefined){setUi('analytics',{device:data.device},false);refresh();}
 if(data.metric!==undefined){setUi('analytics',{metric:data.metric},false);renderSearchConsole();}
 if(data.queue!==undefined)queueSubject(data.queue,data.queueReason||'',data.queueAction||'add');
 if(data.unqueue!==undefined)queueSubject(data.unqueue,'','remove');
 if(data.researchQueued!==undefined){showView('topics');researchSubject(data.researchQueued);}
 if(data.unwatch)updateWatch(data.unwatch,'remove');
 if(data.approve)approveProposal(data.approve);
 if(data.archive)archiveProposal(data.archive);
 if(data.restore)restoreProposal(data.restore);
 if(data.suggestOpen)openInlineForm(data.suggestOpen,'suggest');
 if(data.rejectOpen)openInlineForm(data.rejectOpen,'reject');
 if(data.formSubmit)submitInlineForm(data.formSubmit);
 if(data.formCancel){const form=document.querySelector(`[data-form="${data.formCancel}"]`);if(form)form.hidden=true;}
 if(data.undo)undoRejection(data.undo);
 if(data.reader){
  const task=findTask(openTask);
  if(data.reader==='edit'){editing=true;editorText=articleSource(task);editorBase=editorText;renderDetail(true);}
  if(data.reader==='download')downloadArticle(task);
  if(data.reader==='print')window.print();
 }
 if(data.editor){
  const task=findTask(openTask);
  if(data.editor==='save')saveEdit(task);
  if(data.editor==='cancel')cancelEdit(task);
 }
 if(data.retry)retryBlog(data.retry);
 if(data.revision)revise(findTask(openTask));
 if(data.blogPublish)publishBlog(findTask(openTask));
 if(data.recheck)refreshBlogPublish(findTask(openTask));
 if(data.socialFilter){setUi('social',{filter:data.socialFilter});renderSocial();}
 if(data.socialGenerate)generateSocial(data.socialGenerate);
 if(data.draftSave)saveSocialDraft(data.draftSave);
 if(data.socialPrepare)prepareSocial(data.socialPrepare);
 if(data.socialSend)sendSocial(data.socialSend);
 if(data.socialCancel){delete socialPlans[data.socialCancel];renderSocial();}
});
document.addEventListener('change',event=>{
 const target=event.target;
 if(target.matches('[data-upload]')&&target.files[0])upload(findTask(openTask),target.dataset.upload,target.files[0]);
 if(target.matches('[data-publish-date]'))savePublishDate(target.dataset.publishDate,target.value);
 if(target.matches('[data-size]')){setUi(target.dataset.size,{size:Number(target.value),page:1});renderAll();}
});
document.addEventListener('input',event=>{
 const target=event.target;
 if(target.id==='topics-search'){setUi('topics',{search:target.value});renderProposals();}
 if(target.id==='blogs-search'){setUi('blogs',{search:target.value});renderBlogs();}
 if(target.id==='archived-search'){setUi('archived',{search:target.value});renderArchived();}
 if(target.id==='social-search'){setUi('social',{search:target.value});renderSocial();}
 /* The counter is the one thing that must not wait for a save: a limit
    discovered on submit is a limit discovered too late. */
 if(target.matches('[data-draft-body]'))updateCounter(target);
 if(target.id==='trend-keyword'){setUi('trends',{page:1},false);renderTrends();}
 if(target.id==='editor-input'){editorText=target.value;schedulePreview();}
});
document.addEventListener('pointerover',event=>{
 const hit=event.target.closest?.('.hit');
 if(hit)showTip(Number(hit.dataset.day),hit);
});
document.addEventListener('pointerout',event=>{if(event.target.closest?.('.hit'))hideTip();});
document.addEventListener('focusin',event=>{
 const hit=event.target.closest?.('.hit');
 if(hit)showTip(Number(hit.dataset.day),hit);else hideTip();
});
document.addEventListener('keydown',event=>{
 const typing=/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName);
 if(event.key==='Escape'){
  hideTip();
  if(openTask)closeDetail();
  else if(typing)document.activeElement.blur();
  else if(focusIndex>=0){focusIndex=-1;applyFocus();}
  return;
 }
 if(typing||event.ctrlKey||event.metaKey||event.altKey)return;
 if(event.key==='/'){
  const box=$(`#${currentView}-search`);
  if(box){event.preventDefault();box.focus();box.select();}
  return;
 }
 if(/^[1-5]$/.test(event.key)){showView(VIEWS[Number(event.key)-1]);return;}
 if(openTask)return;
 if(event.key==='j'){event.preventDefault();moveFocus(1);}
 if(event.key==='k'){event.preventDefault();moveFocus(-1);}
 if(event.key==='Enter'&&focusIndex>=0){event.preventDefault();openFocused();}
});
/* Restraint: nothing is polled while the tab is hidden, and the moment it comes
   back the check happens immediately rather than waiting out the interval. */
document.addEventListener('visibilitychange',resumePolling);
window.addEventListener('focus',resumePolling);
let resizeTimer=0;
window.addEventListener('resize',()=>{
 moveIndicator();
 clearTimeout(resizeTimer);
 resizeTimer=setTimeout(()=>{if(currentView==='analytics')drawChart();},150);
});
$('#research-subject').addEventListener('click',()=>researchSubject());
$('#scan-news').addEventListener('click',scanNews);
$('#analyse-competitor').addEventListener('click',analyseCompetitor);
$('#competitor').addEventListener('keydown',event=>{if(event.key==='Enter')analyseCompetitor();});
$('#subject').addEventListener('keydown',event=>{if(event.key==='Enter')researchSubject();});
$('#watch-keyword').addEventListener('click',()=>{const keyword=$('#trend-keyword').value.trim();if(keyword)updateWatch(keyword,'add');});
$('#apply-range').addEventListener('click',()=>{
 setUi('analytics',{range:'custom',start:$('#range-start').value,end:$('#range-end').value},false);
 refresh();
});
$('#edit-title').addEventListener('click',openTitleForm);
$('#title-save').addEventListener('click',saveTitle);
$('#title-cancel').addEventListener('click',closeTitleForm);
$('#title-input').addEventListener('keydown',event=>{
 if(event.key==='Enter'){event.preventDefault();saveTitle();}
 if(event.key==='Escape'){event.preventDefault();closeTitleForm();}
});
$('#close-detail').addEventListener('click',closeDetail);
$('#detail').addEventListener('cancel',event=>{event.preventDefault();closeDetail();});
$('#signout').addEventListener('click',expire);

async function boot(){
 if(!token){expire();return;}
 /* The stored preference covers sort, filter, search and paging. It never
    covers the tab: a first visit and every visit after it opens on Topics. */
 localStorage.removeItem('cmo_console_view');
 $('#topics-search').value=ui.topics.search;
 $('#blogs-search').value=ui.blogs.search;
 $('#archived-search').value=ui.archived.search;
 $('#social-search').value=ui.social.search;
 showView(DEFAULT_VIEW);
 renderSkeletons();moveIndicator();
 try{
  const session=await api('/api/session');
  email=session.email;role=session.role;
  sessionStorage.setItem('cmo_email',email);sessionStorage.setItem('cmo_role',role);
  if(session.console!=='/ceo'){location.replace(session.console);return;}
  $('#account').textContent=email;
  /* Read the token before the state, never after: a change that lands between the
     two then shows up as a difference on the next poll instead of being adopted
     silently and never noticed again. */
  try{versionToken=(await api('/ceo/api/version')).version||'';}catch(error){versionToken='';}
  await refresh();
  schedulePoll();
 }catch(error){notice(error.message,true);}
}
boot();'''
