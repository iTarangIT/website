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
let busy=false;
let focusIndex=-1;
let editing=false;
let editorText='';
let previewTimer=0;

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

/* ----------------------------------------------------------------- vocabulary */
const STATUS={
 proposed:{glyph:'●',label:'awaiting you',tone:'tone-wait'},
 revising:{glyph:'↻',label:'re-researching',tone:'tone-wait'},
 approved:{glyph:'✓',label:'approved',tone:''},
 carded:{glyph:'✓',label:'queued for writing',tone:''},
 rejected:{glyph:'✗',label:'rejected',tone:'tone-stop'},
 'awaiting decision':{glyph:'●',label:'awaiting you',tone:'tone-wait'},
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
 return `<article class="card" role="listitem" data-row="${esc(proposal.id)}" data-proposal="${esc(proposal.id)}">
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
<div class="inline-form" data-form="${esc(proposal.id)}" hidden>
<label class="field"><span data-form-label></span><textarea data-form-input rows="2" maxlength="1000"></textarea></label>
<div class="actions"><button data-form-submit="${esc(proposal.id)}" type="button">Send</button><button class="ghost" data-form-cancel="${esc(proposal.id)}" type="button">Cancel</button></div>
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
 setHtml($('#proposal-list'),view.items.map(proposalCard).join('')||(all.length
  ?emptyState('Nothing matches','No candidate matches this search and filter.','Clear the filters','data-clear="topics"')
  :emptyState('No candidates yet','No topic research has run yet. Enter a rough subject above and Hermes will research it into candidates you can decide on.','Enter a subject','data-focus="subject"')));
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
 if(!subject){$('#propose-result').textContent='Enter a rough subject first.';$('#subject').focus();return;}
 if(busy)return;
 busy=true;
 const button=$('#research-subject');button.disabled=true;
 $('#propose-result').classList.remove('error');
 $('#propose-result').textContent='Researching… Search Console first, then up to five pages of Firecrawl.';
 $('#proposal-list').insertAdjacentHTML('afterbegin',skeleton(1,'card-h'));
 toast('Researching…');
 try{
  const run=await post('/ceo/api/propose',{subject});
  const parts=[`${run.added.length} candidate${run.added.length===1?'':'s'} proposed.`];
  if(run.cache_hit)parts.push('Cached research reused — this run cost 0 credits.');
  else parts.push(`Cost ${run.credits_used} credits; ${run.credits_remaining} left.`);
  if(run.suppressed.length)parts.push(`${run.suppressed.length} suppressed as previously rejected.`);
  if(run.duplicates.length)parts.push(`${run.duplicates.length} already proposed.`);
  if(run.dropped.length)parts.push(`${run.dropped.length} dropped without a source.`);
  (run.messages||[]).forEach(message=>parts.push(message));
  $('#propose-result').textContent=parts.join(' ');
  toast(`${run.added.length} candidate${run.added.length===1?'':'s'} proposed.`);
  $('#subject').value='';
  setUi('topics',{filter:'all',page:1});
  await refresh();
 }catch(error){$('#propose-result').textContent=error.message;$('#propose-result').classList.add('error');toast(error.message,true);}
 finally{busy=false;button.disabled=false;}
}
function openInlineForm(id,kind){
 const form=document.querySelector(`[data-form="${id}"]`);if(!form)return;
 form.hidden=false;form.dataset.kind=kind;
 form.querySelector('[data-form-label]').textContent=kind==='suggest'?'What should be different about this topic?':'Why are you rejecting it? (remembered, so it is not proposed again)';
 form.querySelector('[data-form-input]').focus();
}
async function submitInlineForm(id){
 const form=document.querySelector(`[data-form="${id}"]`);if(!form||busy)return;
 const text=form.querySelector('[data-form-input]').value.trim();
 if(!text){notice(form.dataset.kind==='suggest'?'Say what should change.':'Give a reason so it can be remembered.',true);return;}
 busy=true;
 const card=document.querySelector(`[data-proposal="${id}"]`);
 card?.classList.add('is-pending');
 const suggesting=form.dataset.kind==='suggest';
 toast(suggesting?'Re-researching this candidate…':'Rejecting…');
 try{
  if(suggesting){
   const result=await post('/ceo/api/proposal/suggest',{proposal_id:Number(id),comment:text});
   toast(`Revised. Cost ${result.credits_used} credits.`);
  }else{
   await post('/ceo/api/proposal/reject',{proposal_id:Number(id),reason:text});
   toast('Rejected and remembered.');
  }
  await refresh();
 }catch(error){card?.classList.remove('is-pending');form.hidden=false;toast(error.message,true);notice(error.message,true);}
 finally{busy=false;}
}
async function approveProposal(id){
 if(busy)return;busy=true;
 const card=document.querySelector(`[data-proposal="${id}"]`);
 card?.classList.add('is-pending');
 toast('Approving…');
 try{
  const result=await post('/ceo/api/proposal/approve',{proposal_id:Number(id)});
  toast(`Approved. Board card ${result.task_id} is queued for writing.`);
  await refresh();
 }catch(error){card?.classList.remove('is-pending');toast(error.message,true);notice(error.message,true);}
 finally{busy=false;}
}
async function undoRejection(id){
 if(busy)return;busy=true;
 toast('Returning it to the pool…');
 try{await post('/ceo/api/proposal/undo-rejection',{proposal_id:Number(id)});toast('Rejection undone.');await refresh();}
 catch(error){toast(error.message,true);notice(error.message,true);}
 finally{busy=false;}
}
async function queueSubject(subject,reason,action){
 const card=document.querySelector(`[data-opportunity="${CSS.escape(subject)}"]`);
 card?.classList.toggle('is-queued',action==='add');
 toast(action==='add'?'Queued in Topics & Research.':'Removed from the queue.');
 try{
  const result=await post('/ceo/api/research-queue',{subject,reason,action});
  if(state)state.research_queue=result.research_queue;
  renderProposals();renderOpportunities();
 }catch(error){
  card?.classList.toggle('is-queued',action!=='add');
  toast(error.message,true);notice(error.message,true);
 }
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
function blogStatus(task){
 if(task.decision_approved)return 'approved';
 const change=String(task.change_status||'').toLocaleLowerCase();
 if(change.includes('revision'))return 'revising';
 return 'awaiting decision';
}
function blogCard(task){
 const words=task.article?.word_count??0;
 const minutes=task.article?.read_minutes??0;
 return `<article class="card" role="listitem" data-row="${esc(task.id)}"><div class="card-row">
<div class="card-main"><button class="open" data-open="${esc(task.id)}" type="button">${pill(task.decision_status)}
<h3>${esc(task.title||task.id)}</h3>
<p class="meta"><span class="num">${esc(task.id)}</span> · <span class="num">${grouped.format(words)}</span> words · <span class="num">${minutes}</span> min read${task.change_status?` · ${esc(task.change_status)}`:''}</p></button></div>
<div class="card-figures"><span><span class="stat">${grouped.format(words)}</span><span class="label">words</span></span></div>
</div></article>`;
}
function renderBlogs(){
 const all=state.blogs||[];
 const term=ui.blogs.search.trim().toLocaleLowerCase();
 const counts=all.reduce((total,item)=>{const key=blogStatus(item);total[key]=(total[key]||0)+1;return total;},{});
 chipRow('#blogs-filter',[
  {value:'all',label:'All',count:all.length},
  {value:'awaiting decision',label:'Awaiting you',count:counts['awaiting decision']||0},
  {value:'approved',label:'Approved',count:counts.approved||0},
  {value:'revising',label:'In revision',count:counts.revising||0}
 ],ui.blogs.filter,'blogs-filter');
 const filtered=all.filter(task=>{
  if(ui.blogs.filter!=='all'&&blogStatus(task)!==ui.blogs.filter)return false;
  if(!term)return true;
  return `${task.title||''} ${task.id} ${task.article?.text||''}`.toLocaleLowerCase().includes(term);
 });
 const view=page(filtered,'blogs');
 $('#blogs-count').textContent=filtered.length===all.length
  ?`${grouped.format(all.length)} article${all.length===1?'':'s'}`
  :`${grouped.format(filtered.length)} of ${grouped.format(all.length)}`;
 setHtml($('#blog-list'),view.items.map(blogCard).join('')||(all.length
  ?emptyState('Nothing matches','No article matches this search and filter.','Clear the filters','data-clear="blogs"')
  :emptyState('No article yet','A topic has to be approved in Topics & Research before the writer can produce one.','Go to Topics & Research','data-view="topics"')));
 renderPager('#blogs-pager','blogs',view,'articles');
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
<button class="ghost small" data-queue="${esc(finding.topic)}" data-queue-action="add" data-queue-reason="${esc(finding.recommendation)}" type="button">Research this</button></div></article>`;
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
 if(!target){toast('Enter a competitor website first.',true);$('#competitor').focus();return;}
 if(busy)return;busy=true;
 const button=$('#analyse-competitor');button.disabled=true;
 setHtml($('#competitor-panel'),skeleton(4,'card-h'));
 toast('Reading their sitemap, then up to 10 pages…');
 try{
  const result=await post('/ceo/api/competitor',{target});
  toast(`${result.domain}: ${(result.findings||[]).length} topics scored for ${result.credits_used} credits.`);
  setUi('competitor',{page:1});
  await refresh();
 }catch(error){toast(error.message,true);notice(error.message,true);await refresh();}
 finally{busy=false;button.disabled=false;}
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
 if(busy)return;busy=true;
 const button=document.querySelector('[data-editor="save"]');if(button)button.disabled=true;
 const line=$('#editor-state');if(line)line.textContent='Saving…';
 toast('Saving revision…');
 try{
  const result=await post('/ceo/api/article/edit',{task_id:task.id,text:editorText});
  toast(`Saved as revision ${result.revision_round}. The previous version is kept as ${result.archived_as}.`);
  editing=false;editorText='';
  await refresh();await renderDetail();
 }catch(error){
  if(button)button.disabled=false;
  if(line)line.textContent=error.message;
  toast(error.message,true);
 }finally{busy=false;}
}
function cancelEdit(task){
 if(editorText!==(task.article?.text||'')&&!confirm('Discard your edit?'))return;
 editing=false;editorText='';renderDetail();
}
function pipelineHtml(task){
 const item=task.publishing_pipeline;
 if(!item)return emptyState('No website pipeline','This card publishes nothing to the website, so there is no preview or commit to check.');
 const link=(url,label)=>url?`<a href="${esc(url)}" target="_blank" rel="noopener">${label}</a>`:'—';
 return `<div class="pipeline"><strong>Approval is Gate 1, not publication.</strong><p class="meta">${esc(item.waiting_on)}</p><dl><dt>Change status</dt><dd>${cell(item.change_status)}</dd><dt>Branch</dt><dd>${cell(item.branch)}</dd><dt>Commit</dt><dd>${item.commit_url?link(item.commit_url,esc(item.commit||'Open commit')):cell(item.commit)}</dd><dt>Preview</dt><dd>${link(item.preview_url,'Open preview')}</dd><dt>Lighthouse evidence</dt><dd>${cell(item.lighthouse_evidence)}</dd></dl>${publishHtml()}</div>`;
}
function publishHtml(){
 return `<div class="publish" id="publish-block"><h4>Gate 2 — publish to website</h4><p class="meta" id="publish-state">Checking whether this commit can be published…</p><div id="publish-evidence"></div><div class="actions"><button data-publish="1" type="button" disabled>Publish to website</button></div><p class="meta">Publishing merges the approved commit to main. Your name is recorded in approvals.log and in the merge commit trailer.</p></div>`;
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
function detailDiscussion(task){
 const thread=(task.approval_thread||[]).map(event=>`<div class="history-row"><span class="meta">Round ${esc(event.round)} · ${esc(event.type)}</span><p>${esc(event.text)}</p></div>`).join('');
 return `<h3>Decision</h3><p>Status: ${esc(task.decision_status)}</p>
<div class="actions"><button data-decision="approve" type="button" ${task.decision_approved?'disabled':''}>Approve</button></div>
<label class="field">Ask for changes<textarea id="revision-comment" rows="3" placeholder="State the exact change needed"></textarea></label>
<div class="actions"><button class="ghost" data-revision="1" type="button">Ask for changes</button></div>
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
async function renderDetail(){
 const task=findTask(openTask);if(!task)return;
 $('#detail-id').textContent=task.id;$('#detail-title').textContent=task.title||task.id;
 $$('.nested button').forEach(node=>node.classList.toggle('active',node.dataset.detail===detailTab));
 const render={read:detailRead,impact:detailImpact,discussion:detailDiscussion,files:detailFiles}[detailTab];
 $('#detail-body').innerHTML=render(task);
 painted.delete($('#detail-body'));
 if(detailTab==='read'&&!editing)await hydrateImages();
 if(detailTab==='read'&&editing)$('#editor-input')?.focus();
 if(detailTab==='impact')await refreshPublish(task);
}
async function openDetail(id){openTask=id;detailTab='read';editing=false;editorText='';await renderDetail();$('#detail').showModal();}
function closeDetail(){
 if(editing&&editorText!==(findTask(openTask)?.article?.text||'')&&!confirm('Discard your edit?'))return;
 openTask=null;editing=false;editorText='';$('#detail').close();
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
async function refresh(quiet=false){
 if(quiet&&(openTask||busy||editing))return;
 try{
  state=await api('/ceo/api/state?'+stateQuery());
  renderAll();
  if(!quiet)notice('');
 }catch(error){if(!quiet)notice(error.message,true);}
}
async function updateWatch(keyword,action){
 toast(action==='add'?'Added to the watchlist.':'Removed from the watchlist.');
 try{const result=await post('/ceo/api/watchlist',{keyword,action});state.watchlist=result.watchlist;renderTrends();}
 catch(error){toast(error.message,true);notice(error.message,true);}
}
async function decide(task,decision){
 toast('Recording your decision…');
 try{await post('/ceo/api/decision',{task_id:task.id,decision});toast('Decision recorded.');closeDetail();await refresh();}
 catch(error){toast(error.message,true);notice(error.message,true);}
}
async function revise(task){
 const comment=$('#revision-comment').value;
 toast('Sending the change request…');
 try{await post('/ceo/api/revision',{task_id:task.id,comment});toast('Change requested.');closeDetail();await refresh();}
 catch(error){toast(error.message,true);notice(error.message,true);}
}
async function upload(task,slot,file){
 toast('Uploading the image…');
 try{
  await api(`/ceo/api/upload?task=${encodeURIComponent(task.id)}&slot=${encodeURIComponent(slot)}`,{method:'POST',headers:{'X-Filename':file.name},body:file});
  toast('Image bound to the slot.');
  await refresh();openTask=task.id;detailTab='files';await renderDetail();
 }catch(error){toast(error.message,true);notice(error.message,true);}
}
async function publish(task){
 if(!publishRequest){notice('This card has no current publish instruction. Reopen the Impact tab.',true);return;}
 if(!confirm('Merge '+task.id+' to main and publish it to itarang.com?'))return;
 const button=$('#publish-block [data-publish]');if(button)button.disabled=true;
 toast('Publishing…');
 try{
  const outcome=await post('/ceo/publish',{task:task.id,request_id:publishRequest});
  publishRequest='';
  toast('Published. Merge commit '+(outcome.merge_commit||'').slice(0,7)+'.');
  await refresh();await renderDetail();
 }catch(error){toast(error.message,true);notice(error.message,true);publishRequest='';await refreshPublish(task);}
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
 if(data.detail){detailTab=data.detail;renderDetail();}
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
  if(data.reader==='edit'){editing=true;editorText=task.article?.text||'';renderDetail();}
  if(data.reader==='download')downloadArticle(task);
  if(data.reader==='print')window.print();
 }
 if(data.editor){
  const task=findTask(openTask);
  if(data.editor==='save')saveEdit(task);
  if(data.editor==='cancel')cancelEdit(task);
 }
 if(data.decision)decide(findTask(openTask),data.decision);
 if(data.revision)revise(findTask(openTask));
 if(data.publish)publish(findTask(openTask));
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
  await refresh();
  setInterval(()=>refresh(true),60000);
 }catch(error){notice(error.message,true);}
}
boot();'''
