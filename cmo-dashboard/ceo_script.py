SCRIPT = r'''const $=selector=>document.querySelector(selector);
const $$=selector=>[...document.querySelectorAll(selector)];
const esc=value=>String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const VIEWS=['analytics','topics','blogs'];
let token=sessionStorage.getItem('cmo_token')||'';
let email=sessionStorage.getItem('cmo_email')||'';
let role=sessionStorage.getItem('cmo_role')||'';
let state=null;
let currentView='topics';
let openTask=null;
let detailTab='read';
let publishRequest='';
let darkReading=false;
let busy=false;

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
function value(item){return item===null||item===undefined||item===''?'—':esc(item);}
function delta(item){return item===null||item===undefined?'':`<span class="delta">${item>0?'+':''}${esc(item)} vs previous window</span>`;}
function findTask(id){return (state?.blogs||[]).find(item=>item.id===id);}

function showView(name){
 currentView=name;
 $$('.screen').forEach(node=>node.hidden=node.id!==`panel-${name}`);
 $$('.primary button').forEach(node=>node.classList.toggle('active',node.dataset.view===name));
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
 return `<article class="card" data-proposal="${esc(proposal.id)}">
<div class="card-row"><div><span class="pill status-${esc(proposal.status)}">${esc(proposal.status)}</span> ${round}
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
function renderProposals(){
 const topics=state.topics||{};
 const proposals=topics.proposals||[];
 $('#proposal-list').innerHTML=proposals.map(proposalCard).join('')||'<p class="empty">No candidate topics are waiting. Enter a rough subject above and Hermes will research it into candidates.</p>';
 const rejected=topics.rejected||[];
 $('#rejected-count').textContent=rejected.length?`(${rejected.length})`:'(none)';
 $('#rejected-list').innerHTML=rejected.map(item=>`<div class="watch-row"><div><strong>${esc(item.title)}</strong><p class="meta">${esc(item.reason||'no reason recorded')} · ${esc(item.actor)} · ${esc(item.created_at)}</p></div><button class="ghost" data-undo="${esc(item.proposal_id)}" type="button">Undo</button></div>`).join('')||'<p class="empty">Nothing has been rejected.</p>';
 const carded=topics.carded||[];
 $('#carded-count').textContent=carded.length?`(${carded.length})`:'(none)';
 $('#carded-list').innerHTML=carded.map(item=>`<div class="watch-row"><span>${esc(item.title)}</span><span class="meta">${esc(item.task_id)}</span></div>`).join('')||'<p class="empty">No topic has been approved yet.</p>';
 renderCredits();
}
function renderCredits(){
 const budget=(state.topics||{}).budget||{};
 const node=$('#credit-meter');
 if(budget.status==='ready'){node.innerHTML=`Firecrawl: <strong>${esc(budget.remaining)}</strong> credits left · a proposal run reads up to ${esc(budget.page_cap)} pages · refuses at ${esc(budget.stop_threshold)} used`;node.classList.remove('error');return;}
 node.textContent=budget.message||'Firecrawl credit balance is unavailable.';
 node.classList.add('error');
}
async function researchSubject(){
 const subject=$('#subject').value.trim();
 if(!subject){$('#propose-result').textContent='Enter a rough subject first.';return;}
 if(busy)return;
 busy=true;
 const button=$('#research-subject');button.disabled=true;
 $('#propose-result').classList.remove('error');
 $('#propose-result').textContent='Researching… Search Console first, then up to five pages of Firecrawl.';
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
  $('#subject').value='';
  await refresh();
 }catch(error){$('#propose-result').textContent=error.message;$('#propose-result').classList.add('error');}
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
 try{
  if(form.dataset.kind==='suggest'){
   notice('Re-researching this candidate…');
   const result=await post('/ceo/api/proposal/suggest',{proposal_id:Number(id),comment:text});
   notice(`Revised. Cost ${result.credits_used} credits.`);
  }else{
   await post('/ceo/api/proposal/reject',{proposal_id:Number(id),reason:text});
   notice('Rejected and remembered.');
  }
  await refresh();
 }catch(error){notice(error.message,true);}
 finally{busy=false;}
}
async function approveProposal(id){
 if(busy)return;busy=true;
 try{
  const result=await post('/ceo/api/proposal/approve',{proposal_id:Number(id)});
  notice(`Approved. Board card ${result.task_id} is queued for writing.`);
  await refresh();
 }catch(error){notice(error.message,true);}
 finally{busy=false;}
}
async function undoRejection(id){
 if(busy)return;busy=true;
 try{await post('/ceo/api/proposal/undo-rejection',{proposal_id:Number(id)});notice('Rejection undone.');await refresh();}
 catch(error){notice(error.message,true);}
 finally{busy=false;}
}

/* ------------------------------------------------------------------- trends */

function renderTrends(){
 const keyword=$('#trend-keyword').value.trim().toLocaleLowerCase();
 const rows=(state.trending||[]).filter(row=>!keyword||String(row.title||'').toLocaleLowerCase().includes(keyword));
 $('#trend-list').innerHTML=rows.map(row=>`<div class="trend-row"><div><strong>${esc(row.title)}</strong><br><span class="source">${esc(row.source)}</span> · ${esc(row.metric||'metric unavailable')}</div><div>${value(row.current??row.summary)} ${delta(row.delta)}</div></div>`).join('')||'<p class="empty">No connected source returned matching trends.</p>';
 $('#trend-messages').innerHTML=(state.trending_messages||[]).map(message=>`<p>${esc(message)}</p>`).join('');
 $('#watchlist').innerHTML=(state.watchlist||[]).map(keyword=>`<div class="watch-row"><span>${esc(keyword)}</span><button class="ghost" data-unwatch="${esc(keyword)}" type="button">Remove</button></div>`).join('')||'<p class="empty">Nothing is being watched. Watchlist entries never create board cards.</p>';
}
function renderBlogs(){
 $('#blog-list').innerHTML=(state.blogs||[]).map(task=>`<article class="card"><div class="card-row"><button class="open" data-open="${esc(task.id)}" type="button"><span class="pill">${esc(task.decision_status)}</span><h3>${esc(task.title||task.id)}</h3><p class="meta">${esc(task.id)} · ${task.article?.word_count??0} words · ${task.article?.read_minutes??0} min read</p></button><span class="meta">${esc(task.change_status||task.status||'')}</span></div></article>`).join('')||'<p class="empty">No blog has been written yet. A topic has to be approved in Topics &amp; Research before the writer can produce one.</p>';
}
function renderGsc(){
 const data=state.analytics?.search_console||{};
 if(data.status!=='ok'){$('#gsc-panel').innerHTML=`<p class="empty">${esc(data.message||'Search Console data is unavailable.')}</p>`;return;}
 $('#gsc-panel').innerHTML=`<div class="metrics"><div class="metric"><span>Clicks</span><strong>${value(data.clicks)}</strong></div><div class="metric"><span>Impressions</span><strong>${value(data.impressions)}</strong></div><div class="metric"><span>CTR</span><strong>${value(data.ctr)}</strong></div><div class="metric"><span>Position</span><strong>${value(data.position)}</strong></div></div><p class="meta">Collection starts ${value(data.collection_start)} · last successful read ${value(data.last_successful_read)}</p>`;
}
function renderGa4(){
 const data=state.analytics?.ga4||{};
 if(data.status!=='ready'){
  const vars=(data.required_variables||[]).map(esc).join(', ');
  $('#ga4-panel').innerHTML=`<p class="empty">${esc(data.message||'Google Analytics is not connected yet')}</p>${vars?`<p class="meta">Required .env variables: ${vars}</p>`:''}`;
  return;
 }
 const labels={active_users:'Active users',sessions:'Sessions',screen_page_views:'Page views',engagement_rate:'Engagement rate'};
 const selected=$('#metric').value in labels?$('#metric').value:'sessions';
 $('#ga4-panel').innerHTML=`<div class="metrics"><div class="metric"><span>${labels[selected]}</span><strong>${value(data.metrics?.[selected])}</strong>${delta(data.deltas?.[selected])}</div></div>`;
}
function renderAll(){renderProposals();renderTrends();renderBlogs();renderGsc();renderGa4();}

/* ------------------------------------------------------------- blog reading */

function slotHtml(slot){
 if(slot.bound)return `<figure class="image-slot" data-image-url="${esc(slot.url)}"><span>Loading ${esc(slot.caption)}…</span><figcaption>${esc(slot.caption)}</figcaption></figure>`;
 return `<figure class="image-slot"><strong>Image slot: ${esc(slot.id)}</strong><figcaption>${esc(slot.caption)} · No image is bound yet.</figcaption></figure>`;
}
function articleHtml(task){
 const slots=new Map((task.article?.image_slots||[]).map(slot=>[slot.id,slot]));
 return String(task.article?.text||'').split(/\n/).map(line=>{
  const marker=line.trim().match(/^\{\{image:([a-z0-9][a-z0-9_-]{0,40})(?:\|[^}]+)?\}\}$/i);
  if(marker&&slots.has(marker[1].toLowerCase()))return slotHtml(slots.get(marker[1].toLowerCase()));
  if(/^###\s+/.test(line))return `<h3>${esc(line.replace(/^###\s+/,''))}</h3>`;
  if(/^##\s+/.test(line))return `<h2>${esc(line.replace(/^##\s+/,''))}</h2>`;
  if(/^#\s+/.test(line))return `<h1>${esc(line.replace(/^#\s+/,''))}</h1>`;
  return line.trim()?`<p>${esc(line)}</p>`:'<br>';
 }).join('');
}
async function hydrateImages(){
 for(const figure of $$('#detail-body [data-image-url]')){
  try{const response=await api(figure.dataset.imageUrl,{raw:true});const blob=await response.blob();const image=document.createElement('img');image.alt=figure.querySelector('figcaption')?.textContent||'';image.src=URL.createObjectURL(blob);figure.prepend(image);figure.querySelector('span')?.remove();}
  catch(error){figure.querySelector('span').textContent='Image unavailable';}
 }
}
function pipelineHtml(task){
 const item=task.publishing_pipeline;
 if(!item)return '<p class="empty">This card has no website publishing pipeline.</p>';
 const link=(url,label)=>url?`<a href="${esc(url)}" target="_blank" rel="noopener">${label}</a>`:'—';
 return `<div class="pipeline"><strong>Approval is Gate 1, not publication.</strong><p>${esc(item.waiting_on)}</p><dl><dt>Change status</dt><dd>${value(item.change_status)}</dd><dt>Branch</dt><dd>${value(item.branch)}</dd><dt>Commit</dt><dd>${item.commit_url?link(item.commit_url,esc(item.commit||'Open commit')):value(item.commit)}</dd><dt>Preview</dt><dd>${link(item.preview_url,'Open preview')}</dd><dt>Lighthouse evidence</dt><dd>${value(item.lighthouse_evidence)}</dd></dl>${publishHtml()}</div>`;
}
function publishHtml(){
 return `<div class="publish" id="publish-block"><h4>Gate 2 — publish to website</h4><p class="meta" id="publish-state">Checking whether this commit can be published…</p><div id="publish-evidence"></div><div class="actions"><button data-publish="1" type="button" disabled>Publish to website</button></div><p class="meta">Publishing merges the approved commit to main. Your name is recorded in approvals.log and in the merge commit trailer.</p></div>`;
}
function scoreCell(before,after){
 if(before==null&&after==null)return '—';
 const delta=(before!=null&&after!=null)?after-before:null;
 const arrow=delta==null?'':(delta>0?` (+${delta.toFixed(0)})`:delta<0?` (${delta.toFixed(0)})`:' (no change)');
 return `${before==null?'—':before}&nbsp;→&nbsp;${after==null?'—':after}${arrow}`;
}
function publishEvidenceHtml(check){
 if(!check.comparison||!check.comparison.length)return '<p class="empty">No baseline-to-preview comparison is attached.</p>';
 const rows=check.comparison.map(row=>`<tr><td>${esc(row.path)}</td><td>${scoreCell(row.performance_before,row.performance_after)}</td><td>${scoreCell(row.weight_before==null?null:Math.round(row.weight_before/1024),row.weight_after==null?null:Math.round(row.weight_after/1024))}</td></tr>`).join('');
 return `<table class="evidence"><thead><tr><th>Route</th><th>Performance</th><th>Weight (KB)</th></tr></thead><tbody>${rows}</tbody></table>`;
}
async function refreshPublish(task){
 const block=$('#publish-block');if(!block)return;
 const state=$('#publish-state'),button=block.querySelector('[data-publish]');
 try{
  const check=await api('/ceo/publish-check?task='+encodeURIComponent(task.id));
  publishRequest=check.request_id||'';
  $('#publish-evidence').innerHTML=publishEvidenceHtml(check);
  if(check.eligible){
   state.textContent=`Ready: commit ${(check.commit||'').slice(0,7)} is current, the preview is deployed and the evidence is attached.`;
   button.disabled=false;
  }else{
   state.innerHTML='Cannot publish yet:<ul>'+check.blockers.map(reason=>`<li>${esc(reason)}</li>`).join('')+'</ul>';
   button.disabled=true;
  }
 }catch(error){state.textContent='Could not check publish eligibility: '+error.message;button.disabled=true;}
}
function detailRead(task){
 return `<div class="reader-actions actions"><button data-reader="dark" type="button">${darkReading?'Light':'Dark'} reading</button><button data-reader="download" type="button">Download</button><button data-reader="pdf" type="button">Open as PDF</button><button data-reader="print" type="button">Print/PDF</button></div><p class="meta">${task.article?.word_count??0} words · ${task.article?.read_minutes??0} min read</p><article class="article-sheet${darkReading?' dark':''}">${articleHtml(task)}</article>`;
}
function detailImpact(task){return `<h3>Expected impact</h3><p>${value(task.metric||task.declared_metric)}</p>${pipelineHtml(task)}`;}
function detailDiscussion(task){return `<h3>Decision</h3><p>Status: ${esc(task.decision_status)}</p><div class="actions"><button data-decision="approve" type="button" ${task.decision_approved?'disabled':''}>Approve</button></div><label class="field">Ask for changes<textarea id="revision-comment" rows="3" placeholder="State the exact change needed"></textarea></label><button data-revision="1" type="button">Ask for changes</button><p class="meta">Revision round: ${esc(task.revision_round||'0')}. A revision keeps the card in its current lane and is refused after any human decision.</p>`;}
function detailFiles(task){
 const files=(task.article?.files||[]).map(file=>`<div class="file-row"><span>${esc(file.name)} · ${esc(file.kind)}</span><span>${esc(file.bytes)} bytes</span></div>`).join('');
 const slots=(task.article?.image_slots||[]).map(slot=>`<div class="file-row"><span>${esc(slot.caption)} · ${slot.bound?esc(slot.filename):'unbound placeholder'}</span><label class="ghost">Bind image<input data-upload="${esc(slot.id)}" type="file" accept=".png,.jpg,.jpeg,.webp,.gif" hidden></label></div>`).join('');
 return `<h3>Files</h3>${files||'<p class="empty">No files.</p>'}<h3>Image slots</h3>${slots||'<p class="empty">The article declares no image slots.</p>'}<p class="meta">Images: PNG, JPG, JPEG, WEBP or GIF, maximum 5 MB. SVG is not allowed.</p>`;
}
async function renderDetail(){
 const task=findTask(openTask);if(!task)return;
 $('#detail-id').textContent=task.id;$('#detail-title').textContent=task.title||task.id;
 $$('.nested button').forEach(node=>node.classList.toggle('active',node.dataset.detail===detailTab));
 const render={read:detailRead,impact:detailImpact,discussion:detailDiscussion,files:detailFiles}[detailTab];
 $('#detail-body').innerHTML=render(task);
 if(detailTab==='read')await hydrateImages();
 if(detailTab==='impact')await refreshPublish(task);
}
async function openDetail(id){openTask=id;detailTab='read';await renderDetail();$('#detail').showModal();}
function closeDetail(){openTask=null;$('#detail').close();}
function paperDocument(task){const rendered=$('#detail-body .article-sheet')?.innerHTML||articleHtml(task);return `<!doctype html><html><head><meta charset="utf-8"><title>${esc(task.title||task.id)}</title><style>body{margin:0;background:#eee;color:#17211d;font:16px/1.65 system-ui,sans-serif}.sheet{max-width:760px;margin:24px auto;padding:48px;background:white}img{max-width:100%}@media print{body{background:white}.sheet{margin:0;max-width:none}}</style></head><body><article class="sheet">${rendered}</article></body></html>`;}
function openPdf(task){const popup=window.open('','_blank');if(!popup){notice('Allow pop-ups to open the browser PDF view.',true);return;}popup.opener=null;popup.document.write(paperDocument(task));popup.document.close();setTimeout(()=>popup.print(),250);}
function downloadArticle(task){const blob=new Blob([task.article?.text||''],{type:'text/markdown;charset=utf-8'});const link=document.createElement('a');link.href=URL.createObjectURL(blob);link.download=(task.article?.metadata?.slug||task.id)+'.md';link.click();setTimeout(()=>URL.revokeObjectURL(link.href),1000);}

async function refresh(quiet=false){
 if(quiet&&(openTask||busy))return;
 const range=$('#range').value;const device=$('#device').value;
 try{state=await api(`/ceo/api/state?range=${encodeURIComponent(range)}&device=${encodeURIComponent(device)}`);renderAll();if(!quiet)notice('');}
 catch(error){if(!quiet)notice(error.message,true);}
}
async function updateWatch(keyword,action){try{const result=await post('/ceo/api/watchlist',{keyword,action});state.watchlist=result.watchlist;renderTrends();}catch(error){notice(error.message,true);}}
async function decide(task,decision){try{await post('/ceo/api/decision',{task_id:task.id,decision});closeDetail();await refresh();}catch(error){notice(error.message,true);}}
async function revise(task){const comment=$('#revision-comment').value;try{await post('/ceo/api/revision',{task_id:task.id,comment});closeDetail();await refresh();}catch(error){notice(error.message,true);}}
async function upload(task,slot,file){try{await api(`/ceo/api/upload?task=${encodeURIComponent(task.id)}&slot=${encodeURIComponent(slot)}`,{method:'POST',headers:{'X-Filename':file.name},body:file});await refresh();openTask=task.id;detailTab='files';await renderDetail();}catch(error){notice(error.message,true);}}

async function publish(task){
 if(!publishRequest){notice('This card has no current publish instruction. Reopen the Impact tab.',true);return;}
 if(!confirm('Merge '+task.id+' to main and publish it to itarang.com?'))return;
 const button=$('#publish-block [data-publish]');if(button)button.disabled=true;
 try{
  const outcome=await post('/ceo/publish',{task:task.id,request_id:publishRequest});
  publishRequest='';
  notice('Published. Merge commit '+(outcome.merge_commit||'').slice(0,7)+'.');
  await refresh();await renderDetail();
 }catch(error){notice(error.message,true);publishRequest='';await refreshPublish(task);}
}
document.addEventListener('click',event=>{
 const button=event.target.closest('button');if(!button)return;
 const data=button.dataset;
 if(data.view)showView(data.view);
 if(data.open)openDetail(data.open);
 if(data.detail){detailTab=data.detail;renderDetail();}
 if(data.unwatch)updateWatch(data.unwatch,'remove');
 if(data.approve)approveProposal(data.approve);
 if(data.suggestOpen)openInlineForm(data.suggestOpen,'suggest');
 if(data.rejectOpen)openInlineForm(data.rejectOpen,'reject');
 if(data.formSubmit)submitInlineForm(data.formSubmit);
 if(data.formCancel){const form=document.querySelector(`[data-form="${data.formCancel}"]`);if(form)form.hidden=true;}
 if(data.undo)undoRejection(data.undo);
 if(data.reader){const task=findTask(openTask);if(data.reader==='dark'){darkReading=!darkReading;renderDetail();}if(data.reader==='download')downloadArticle(task);if(data.reader==='pdf')openPdf(task);if(data.reader==='print')window.print();}
 if(data.decision)decide(findTask(openTask),data.decision);
 if(data.revision)revise(findTask(openTask));
 if(data.publish)publish(findTask(openTask));
});
document.addEventListener('change',event=>{if(event.target.matches('[data-upload]')&&event.target.files[0])upload(findTask(openTask),event.target.dataset.upload,event.target.files[0]);if(event.target.matches('#range,#device,#metric'))refresh();});
document.addEventListener('keydown',event=>{
 const typing=/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName);
 if(event.key==='Escape'&&openTask)closeDetail();
 if(event.key==='/'&&!event.ctrlKey&&!event.metaKey&&!typing){event.preventDefault();showView('topics');$('#subject').focus();}
 if(/^[1-3]$/.test(event.key)&&!typing)showView(VIEWS[Number(event.key)-1]);
});
$('#research-subject').addEventListener('click',researchSubject);
$('#subject').addEventListener('keydown',event=>{if(event.key==='Enter')researchSubject();});
$('#trend-keyword').addEventListener('input',renderTrends);
$('#watch-keyword').addEventListener('click',()=>{const keyword=$('#trend-keyword').value.trim();if(keyword)updateWatch(keyword,'add');});
$('#close-detail').addEventListener('click',closeDetail);
$('#signout').addEventListener('click',expire);

async function boot(){
 if(!token){expire();return;}
 try{const session=await api('/api/session');email=session.email;role=session.role;sessionStorage.setItem('cmo_email',email);sessionStorage.setItem('cmo_role',role);if(session.console!=='/ceo'){location.replace(session.console);return;}$('#account').textContent=email;await refresh();setInterval(()=>refresh(true),60000);}
 catch(error){notice(error.message,true);}
}
boot();'''
