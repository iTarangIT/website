SCRIPT = r'''const $=selector=>document.querySelector(selector);
const $$=selector=>[...document.querySelectorAll(selector)];
const esc=value=>String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
/* Tab order is the order the work happens, and it is fixed. The stored UI state
   below deliberately does not include the tab: every load opens on Topics. */
const VIEWS=['topics','blogs','analytics'];
const DEFAULT_VIEW='topics';
let token=sessionStorage.getItem('cmo_token')||'';
let email=sessionStorage.getItem('cmo_email')||'';
let role=sessionStorage.getItem('cmo_role')||'';
let state=null;
let currentView=DEFAULT_VIEW;
let openTask=null;
let detailTab='read';
let publishRequest='';
let blogPublishRequest='';
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
 trends:{page:1,size:10},
 opportunities:{page:1,size:10},
 queries:{page:1,size:25,sort:'impressions',dir:'desc'},
 pages:{page:1,size:25,sort:'impressions',dir:'desc'},
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
 'awaiting decision':{glyph:'●',label:'awaiting you',tone:'tone-wait'},
 /* The blog chain, start to finish. Every content card carries one of these, so
    the minutes between approving a topic and reading the article are no longer
    a blank tab. */
 queued:{glyph:'○',label:'queued to be written',tone:'tone-mute'},
 researching:{glyph:'◐',label:'researching',tone:'tone-wait'},
 writing:{glyph:'◑',label:'writing',tone:'tone-wait'},
 failed:{glyph:'✗',label:'could not be written',tone:'tone-stop'},
 held:{glyph:'‖',label:'on hold',tone:'tone-mute'},
 checking:{glyph:'◇',label:'being checked',tone:'tone-wait'},
 awaiting_you:{glyph:'●',label:'awaiting you',tone:'tone-wait'},
 rewriting:{glyph:'↻',label:'being rewritten',tone:'tone-wait'},
 published:{glyph:'▲',label:'live on the site',tone:''},
 uncontested:{glyph:'◆',label:'uncontested',tone:''},
 weak_position:{glyph:'▲',label:'we rank weakly',tone:'tone-wait'},
 covered:{glyph:'✓',label:'we hold this',tone:'tone-mute'},
 unclicked:{glyph:'◆',label:'seen, never clicked',tone:'tone-wait'},
 page_two:{glyph:'▲',label:'page two',tone:'tone-wait'},
 weak_title:{glyph:'○',label:'ranks but loses the click',tone:'tone-mute'},
 rising:{glyph:'↑',label:'rising',tone:''}
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
function proposalCard(proposal){
 const keywords=(proposal.keywords||[]).map(word=>`<span class="pill">${esc(word)}</span>`).join(' ')||'<span class="meta">no keywords recorded</span>';
 const round=proposal.round>1?`<span class="meta">revised ${proposal.round-1}×</span>`:'';
 const busyNote=proposal.status==='revising'?'<p class="meta">Re-researching this candidate…</p>':'';
 const history=(proposal.history||[]).length>1?`<details><summary>Earlier rounds</summary>${proposal.history.slice(0,-1).map(item=>`<div class="history-row"><strong>Round ${esc(item.round)}: ${esc(item.title)}</strong><p class="meta">${esc(item.outline)}</p></div>`).join('')}</details>`:'';
 return `<article class="card" role="listitem" data-key="${esc(proposal.id)}" data-row="${esc(proposal.id)}" data-proposal="${esc(proposal.id)}">
<div class="card-row"><div class="card-main">${pill(proposal.status)} ${round}
<h3>${esc(proposal.title)}</h3>
<p class="meta">From your subject: ${esc(proposal.subject)}</p>
<div class="keywords">${keywords}</div>
<p class="outline">${esc(proposal.outline)}</p>
${sourceLine(proposal)}${busyNote}${history}</div></div>
<div class="actions">
<button data-approve="${esc(proposal.id)}" type="button">Approve</button>
<button class="ghost" data-suggest-open="${esc(proposal.id)}" type="button">Suggest changes</button>
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
  if(run.dropped.length)parts.push(`${run.dropped.length} dropped without a source.`);
  (run.messages||[]).forEach(message=>parts.push(message));
  $('#subject').value='';
  setUi('topics',{filter:'all',page:1});
  /* The skeleton comes down only once the real candidates are in the DOM. */
  await refresh();
  result.classList.remove('error');
  result.textContent=parts.join(' ');
 }catch(error){
  action.fail(error.message);
  result.classList.add('error');
  result.textContent=error.message;
 }finally{action.done();}
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
  toast(`Approved. Board card ${result.task_id} is queued for writing.`);
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
 if(blog.state==='published'&&blog.url)
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
 'awaiting you':new Set(['awaiting_you']),
 'in progress':new Set(['queued','researching','writing','rewriting','checking']),
 failed:new Set(['failed']),
 approved:new Set(['approved']),
 published:new Set(['published'])
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
  {value:'awaiting you',label:'Awaiting you',count:counts['awaiting you']||0},
  {value:'in progress',label:'Being written',count:counts['in progress']||0},
  {value:'failed',label:'Could not be written',count:counts.failed||0},
  {value:'approved',label:'Approved',count:counts.approved||0},
  {value:'published',label:'Published',count:counts.published||0}
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
}
function renderAll(){
 renderProposals();renderTrends();renderBlogs();renderSearchConsole();renderGa4();renderCompetitor();applyFocus();
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
${reviewNotesHtml(task)}`;
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
function pipelineHtml(task){
 const item=task.publishing_pipeline;
 /* A blog card is a website card, but at Gate 1 it has no commit and no preview
    yet — the article is approved first and pushed afterwards. So which block
    belongs here depends on whether the push has happened, not on the change type:
    before it, the control that performs the push; after it, the pipeline showing
    where that push landed. */
 const pushed=Boolean(item&&(item.commit||item.preview_url));
 if(task.article&&!pushed)return blogPublishHtml();
 if(!item)return emptyState('No website pipeline','This card publishes nothing to the website, so there is no preview or commit to check.');
 const link=(url,label)=>url?`<a href="${esc(url)}" target="_blank" rel="noopener">${label}</a>`:'—';
 return `<div class="pipeline"><strong>Approval is Gate 1, not publication.</strong><p class="meta">${esc(item.waiting_on)}</p><dl><dt>Change status</dt><dd>${cell(item.change_status)}</dd><dt>Branch</dt><dd>${cell(item.branch)}</dd><dt>Commit</dt><dd>${item.commit_url?link(item.commit_url,esc(item.commit||'Open commit')):cell(item.commit)}</dd><dt>Preview</dt><dd>${link(item.preview_url,'Open preview')}</dd><dt>Lighthouse evidence</dt><dd>${cell(item.lighthouse_evidence)}</dd></dl>${publishHtml()}</div>`;
}
function publishHtml(){
 return `<div class="publish" id="publish-block"><h4>Gate 2 — publish to website</h4><p class="meta" id="publish-state">Checking whether this commit can be published…</p><div id="publish-evidence"></div><div class="actions"><button data-publish="1" type="button" disabled>Publish to website</button></div><p class="meta">Publishing merges the approved commit to main. Your name is recorded in approvals.log and in the merge commit trailer.</p></div>`;
}
/* Publishing an article stops at the preview. There is no merge button here on
   purpose: cmo-changes → preview → a human merges on GitHub. The only other
   publish control on this console is Gate 2, and it lives on website-change
   cards, not on these. */
function blogPublishHtml(){
 return `<div class="publish" id="blog-publish-block"><h4>Publish to website</h4>
<p class="meta" id="blog-publish-state">Checking whether this article can be published…</p>
<div id="blog-publish-files"></div>
<div class="actions"><button data-blog-publish="1" type="button" disabled>Publish to website</button></div>
<p class="meta">This writes the blog page, its index entry and its diagram, then pushes them to <span class="num">cmo-changes</span>. It does not touch <span class="num">main</span> — a human merges on GitHub after seeing the preview. Your name is recorded in approvals.log and in the commit trailer.</p></div>`;
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
  if(line)line.textContent='This card has no current publish instruction. Reopen the Impact tab.';
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
function scoreCell(before,after){
 if(before==null&&after==null)return '—';
 const delta=(before!=null&&after!=null)?after-before:null;
 const arrow=delta==null?'':(delta>0?` (+${delta.toFixed(0)})`:delta<0?` (${delta.toFixed(0)})`:' (no change)');
 return `${before==null?'—':before} → ${after==null?'—':after}${arrow}`;
}
function publishEvidenceHtml(check){
 if(!check.comparison||!check.comparison.length)return '<p class="meta">No baseline-to-preview comparison is attached.</p>';
 const rows=check.comparison.map(row=>`<tr><td>${esc(row.path)}</td><td>${scoreCell(row.performance_before,row.performance_after)}</td><td>${scoreCell(row.weight_before==null?null:Math.round(row.weight_before/1024),row.weight_after==null?null:Math.round(row.weight_after/1024))}</td></tr>`).join('');
 return `<table class="evidence"><thead><tr><th>Route</th><th>Performance</th><th>Weight (KB)</th></tr></thead><tbody>${rows}</tbody></table>`;
}
async function refreshPublish(task){
 const block=$('#publish-block');if(!block)return;
 const line=$('#publish-state'),button=block.querySelector('[data-publish]');
 try{
  const check=await api('/ceo/publish-check?task='+encodeURIComponent(task.id));
  publishRequest=check.request_id||'';
  setHtml($('#publish-evidence'),publishEvidenceHtml(check));
  if(check.eligible){
   line.textContent=`Ready: commit ${(check.commit||'').slice(0,7)} is current, the preview is deployed and the evidence is attached.`;
   button.disabled=false;
  }else{
   line.innerHTML='Cannot publish yet:<ul>'+check.blockers.map(reason=>`<li>${esc(reason)}</li>`).join('')+'</ul>';
   button.disabled=true;
  }
 }catch(error){line.textContent='Could not check publish eligibility: '+error.message;button.disabled=true;}
}
function detailImpact(task){return `<h3>Expected impact</h3><p>${cell(task.metric||task.declared_metric)}</p>${pipelineHtml(task)}`;}
/* Why a card cannot be decided yet, in the words its own state warrants. Every
   one of these ends by saying when it *will* come to him, because "you cannot act
   on this" without "here is when you can" is just a dead end. */
const NOT_YET_DECIDABLE={
 queued:'Queued to be written. It will come to you once the article exists.',
 researching:'Being written now. It will come to you when it is finished.',
 writing:'Being written now. It will come to you when it is finished.',
 rewriting:'Being rewritten. The new version will come to you when it is done.',
 checking:'Being checked. It will come to you when review finishes.',
 failed:'This could not be written, so there is nothing to decide yet. Retry it from the Blogs list.',
 held:'On hold. It will come to you once it is released.',
 published:'Published to cmo-changes. The decision on it is already recorded.'
};
function detailDiscussion(task){
 const thread=(task.approval_thread||[]).map(event=>`<div class="history-row"><span class="meta">Round ${esc(event.round)} · ${esc(event.type)}</span><p>${esc(event.text)}</p></div>`).join('');
 /* The decision controls appear only where a decision can actually be recorded.
    `DecisionStore` refuses any card that is not in Human Approval, so offering
    Approve anywhere else is a button whose only possible outcome is "The decision
    was not recorded." Ask for changes is worse than that: it does not fail, it
    succeeds — setting `revision requested` on a card that never reached him, which
    the content worker then picks up and rewrites. Both are gone from every other
    lane, and both are refused server-side as well; this is the courtesy, not the
    guard. */
 const section=String(task.board_section||task.status||'').trim();
 const decidable=section==='Human Approval';
 const surfaces=`<div id="detail-pending" class="rows" aria-live="polite" hidden></div>
<p class="row-error" id="detail-error" role="alert" hidden></p>`;
 if(!decidable){
  const state=task.blog?.state||'';
  const line=NOT_YET_DECIDABLE[state]||`In ${esc(section||'another lane')}. It will come to you when it reaches your approval.`;
  const reason=task.blog?.reason?`<p class="meta">${esc(task.blog.reason)}</p>`:'';
  return `<h3>Decision</h3><p>${esc(line)}</p>${reason}${surfaces}
<p class="meta">Revision round: <span class="num">${esc(task.revision_round||'0')}</span>.</p>
${thread?`<h3>Thread</h3>${thread}`:''}`;
 }
 const record=task.decision_summary||{};
 const decided=record.approver_id?`by ${esc(record.approver_id)}`:'';
 const when=record.timestamp?` on ${esc(record.timestamp)}`:'';
 /* The approval no longer describes the article in front of him. Publish already
    refuses it and asks for a fresh Gate 1 — so this is where that becomes possible,
    or the card sits between "already decided" and "the approval does not match"
    with no control that resolves either. */
 if(task.decision_stale){
  const changes=(task.decision_change||[]).map(line=>`<li>${esc(line)}</li>`).join('');
  return `<h3>Decision</h3><p>Approved ${decided}${when}, <strong>but the article has changed since</strong>, so that approval no longer covers it.</p>
${changes?`<p class="meta">What changed:</p><ul class="meta">${changes}</ul>`:''}
<div class="actions"><button data-decision="approve" type="button">Approve again</button></div>
<label class="field">Ask for changes<textarea id="revision-comment" rows="3" placeholder="State the exact change needed"></textarea></label>
<div class="actions"><button class="ghost" data-revision="1" type="button">Ask for changes</button></div>
${surfaces}
<p class="meta">Approving again records a new decision and keeps the old one; nothing is overwritten. Revision round: <span class="num">${esc(task.revision_round||'0')}</span>.</p>
${thread?`<h3>Thread</h3>${thread}`:''}`;
 }
 if(task.decision_approved){
  return `<h3>Decision</h3><p>Approved ${decided}${when}.</p>
<p class="meta">A revision is refused once a decision exists, so this article can no longer be changed here. Publish it from the Impact tab.</p>${surfaces}
${thread?`<h3>Thread</h3>${thread}`:''}`;
 }
 return `<h3>Decision</h3><p>Status: ${esc(task.decision_status)}</p>
<div class="actions"><button data-decision="approve" type="button">Approve</button></div>
<label class="field">Ask for changes<textarea id="revision-comment" rows="3" placeholder="State the exact change needed"></textarea></label>
<div class="actions"><button class="ghost" data-revision="1" type="button">Ask for changes</button></div>
${surfaces}
<p class="meta">Revision round: <span class="num">${esc(task.revision_round||'0')}</span>. A revision keeps the card in its current lane and is refused after any human decision.</p>
${thread?`<h3>Thread</h3>${thread}`:''}`;
}
function detailFiles(task){
 const files=(task.article?.files||[]).map(file=>`<div class="list-row"><span>${esc(file.name)} · <span class="meta">${esc(file.kind)}</span></span><span class="meta num">${grouped.format(file.bytes)} bytes</span></div>`).join('');
 const revisions=(task.article?.revisions||[]).map(item=>`<div class="list-row"><span>${esc(item.name)} · <span class="meta">revision ${esc(item.round)}</span></span><span class="meta num">${grouped.format(item.bytes)} bytes</span></div>`).join('');
 const slots=(task.article?.image_slots||[]).map(slot=>`<div class="list-row"><span>${esc(slot.caption)} · <span class="meta">${slot.bound?esc(slot.filename):'no image bound'}</span></span><label class="ghost small" style="cursor:pointer">Bind image<input data-upload="${esc(slot.id)}" type="file" accept=".png,.jpg,.jpeg,.webp,.gif" hidden></label></div>`).join('');
 return `<h3>Files</h3><div class="rows">${files||'<p class="empty">No files.</p>'}</div>
<h3>Earlier versions</h3><div class="rows">${revisions||'<p class="empty">No revision has been written yet.</p>'}</div>
<h3>Image slots</h3><div class="rows">${slots||'<p class="empty">The article declares no image slots.</p>'}</div>
<p class="meta">Images: PNG, JPG, JPEG, WEBP or GIF, maximum 5 MB. SVG is not accepted for upload.</p>`;
}
/* `force` is for a tab or mode change, where the body must be rebuilt. Left alone,
   this paints only when the markup actually differs, and puts the reading position
   back where it was — a background update must not scroll the open article. */
async function renderDetail(force=false){
 const task=findTask(openTask);if(!task)return;
 $('#detail-id').textContent=task.id;$('#detail-title').textContent=task.title||task.id;
 $$('.nested button').forEach(node=>node.classList.toggle('active',node.dataset.detail===detailTab));
 const body=$('#detail-body');
 const render={read:detailRead,impact:detailImpact,discussion:detailDiscussion,files:detailFiles}[detailTab];
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
 if(detailTab==='impact'&&(repainted||publishCheckPending())){
  await refreshPublish(task);await refreshBlogPublish(task);
 }
}
/* What a background update is allowed to do to an open card. */
async function syncDetail(){
 const task=findTask(openTask);
 if(!task)return;
 if(!editing){await renderDetail();return;}
 const theirs=task.article?.text||'';
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
 openTask=id;detailTab='read';editing=false;editorText='';editorBase='';
 await renderDetail(true);$('#detail').showModal();
}
function closeDetail(){
 if(editing&&editorText!==editorBase&&!confirm('Discard your edit?'))return;
 openTask=null;editing=false;editorText='';editorBase='';$('#detail').close();
}
function downloadArticle(task){
 const blob=new Blob([task.article?.text||''],{type:'text/markdown;charset=utf-8'});
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
 if(quiet&&busy)return;
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
 /* An action he started owns the screen until it finishes. */
 if(busy){schedulePoll(POLL_LADDER[0]);return;}
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
async function decide(task,decision){
 if(busy)return;
 const action=runAction({
  button:document.querySelector(`[data-decision="${decision}"]`),label:'Recording…',
  slot:'#detail-pending',shape:'row-h',count:1,surface:'#detail-error',
  failTitle:'The decision was not recorded.'
 });
 try{await post('/ceo/api/decision',{task_id:task.id,decision});toast('Decision recorded.');closeDetail();await refresh();}
 catch(error){action.fail(error.message);}
 finally{action.done();}
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
async function publish(task){
 const line=$('#publish-state');
 if(!publishRequest){
  if(line)line.textContent='This card has no current publish instruction. Reopen the Impact tab.';
  return;
 }
 if(!confirm('Merge '+task.id+' to main and publish it to itarang.com?'))return;
 if(busy)return;
 const action=runAction({
  button:document.querySelector('#publish-block [data-publish]'),label:'Publishing…',
  surface:line,failTitle:'The publish did not go through.'
 });
 try{
  const outcome=await post('/ceo/publish',{task:task.id,request_id:publishRequest});
  publishRequest='';
  toast('Published. Merge commit '+(outcome.merge_commit||'').slice(0,7)+'.');
  await refresh();await renderDetail(true);
 }catch(error){
  action.fail(error.message);publishRequest='';
 }finally{action.done();}
}

/* ------------------------------------------------------------------- events */
document.addEventListener('click',event=>{
 /* A sortable header is a click target in its own right, padding included. */
 const header=event.target.closest('th[data-sort]');
 if(header){
  const key=header.closest('table').id==='queries-table'?'queries':'pages';
  const field=header.dataset.sort;
  const same=ui[key].sort===field;
  setUi(key,{sort:field,dir:same&&ui[key].dir==='desc'?'asc':'desc',page:1});
  renderSearchConsole();
  return;
 }
 const button=event.target.closest('button');
 if(!button)return;
 const data=button.dataset;
 if(data.view)showView(data.view);
 if(data.focus){showView(data.focus==='competitor'?'analytics':'topics');$('#'+data.focus)?.focus();}
 if(data.open)openDetail(data.open);
 if(data.detail){detailTab=data.detail;renderDetail(true);}
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
 if(data.suggestOpen)openInlineForm(data.suggestOpen,'suggest');
 if(data.rejectOpen)openInlineForm(data.rejectOpen,'reject');
 if(data.formSubmit)submitInlineForm(data.formSubmit);
 if(data.formCancel){const form=document.querySelector(`[data-form="${data.formCancel}"]`);if(form)form.hidden=true;}
 if(data.undo)undoRejection(data.undo);
 if(data.reader){
  const task=findTask(openTask);
  if(data.reader==='edit'){editing=true;editorText=task.article?.text||'';editorBase=editorText;renderDetail(true);}
  if(data.reader==='download')downloadArticle(task);
  if(data.reader==='print')window.print();
 }
 if(data.editor){
  const task=findTask(openTask);
  if(data.editor==='save')saveEdit(task);
  if(data.editor==='cancel')cancelEdit(task);
 }
 if(data.retry)retryBlog(data.retry);
 if(data.decision)decide(findTask(openTask),data.decision);
 if(data.revision)revise(findTask(openTask));
 if(data.publish)publish(findTask(openTask));
 if(data.blogPublish)publishBlog(findTask(openTask));
 if(data.recheck)refreshBlogPublish(findTask(openTask));
});
document.addEventListener('change',event=>{
 const target=event.target;
 if(target.matches('[data-upload]')&&target.files[0])upload(findTask(openTask),target.dataset.upload,target.files[0]);
 if(target.matches('[data-size]')){setUi(target.dataset.size,{size:Number(target.value),page:1});renderAll();}
});
document.addEventListener('input',event=>{
 const target=event.target;
 if(target.id==='topics-search'){setUi('topics',{search:target.value});renderProposals();}
 if(target.id==='blogs-search'){setUi('blogs',{search:target.value});renderBlogs();}
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
 if(/^[1-3]$/.test(event.key)){showView(VIEWS[Number(event.key)-1]);return;}
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
$('#analyse-competitor').addEventListener('click',analyseCompetitor);
$('#competitor').addEventListener('keydown',event=>{if(event.key==='Enter')analyseCompetitor();});
$('#subject').addEventListener('keydown',event=>{if(event.key==='Enter')researchSubject();});
$('#watch-keyword').addEventListener('click',()=>{const keyword=$('#trend-keyword').value.trim();if(keyword)updateWatch(keyword,'add');});
$('#apply-range').addEventListener('click',()=>{
 setUi('analytics',{range:'custom',start:$('#range-start').value,end:$('#range-end').value},false);
 refresh();
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
