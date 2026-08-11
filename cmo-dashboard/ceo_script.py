SCRIPT = r'''const $=selector=>document.querySelector(selector);
const $$=selector=>[...document.querySelectorAll(selector)];
const esc=value=>String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
let token=sessionStorage.getItem('cmo_token')||'';
let email=sessionStorage.getItem('cmo_email')||'';
let role=sessionStorage.getItem('cmo_role')||'';
let state=null;
let currentView='topics';
let openTask=null;
let detailTab='read';
let publishRequest='';
let darkReading=false;

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
function notice(message,error=false){const node=$('#notice');node.textContent=message||'';node.classList.toggle('error',error);}
function value(item){return item===null||item===undefined||item===''?'—':esc(item);}
function delta(item){return item===null||item===undefined?'':`<span class="delta">${item>0?'+':''}${esc(item)} vs previous window</span>`;}
function findTask(id){return [...(state?.topics||[]),...(state?.blogs||[])].find(item=>item.id===id);}

function showView(name){
 currentView=name;
 $$('.screen').forEach(node=>node.hidden=node.id!==`panel-${name}`);
 $$('.primary button').forEach(node=>node.classList.toggle('active',node.dataset.view===name));
}
function topicCard(task){
 const brief=task.research_brief;
 const note=task.topic_approved_by?`<p class="meta">Legacy topic note by ${esc(task.topic_approved_by)} — not a writing or publication gate.</p>`:'';
 const briefHtml=brief?`<details><summary>Read research brief</summary><div class="article-sheet"><pre>${esc(brief.text)}</pre></div></details>`:'<p class="meta">No research brief is attached yet.</p>';
 return `<article class="card"><div class="card-row"><div><span class="pill">${esc(task.topic_stage||'proposed')}</span><h3>${esc(task.title||task.id)}</h3><p class="meta">${esc(task.id)} · ${esc(task.status||'')}</p><p class="meta">Submitting this topic is the instruction to research and write it; no separate topic approval is required.</p>${note}</div></div>${briefHtml}</article>`;
}
function renderTopics(){
 $('#topic-list').innerHTML=(state.topics||[]).map(topicCard).join('')||'<p class="empty">No content topics are on the board.</p>';
}
function renderTrends(){
 const keyword=$('#trend-keyword').value.trim().toLocaleLowerCase();
 const rows=(state.trending||[]).filter(row=>!keyword||String(row.title||'').toLocaleLowerCase().includes(keyword));
 $('#trend-list').innerHTML=rows.map(row=>`<div class="trend-row"><div><strong>${esc(row.title)}</strong><br><span class="source">${esc(row.source)}</span> · ${esc(row.metric||'metric unavailable')}</div><div>${value(row.current??row.summary)} ${delta(row.delta)}</div></div>`).join('')||'<p class="empty">No connected source returned matching trends.</p>';
 $('#trend-messages').innerHTML=(state.trending_messages||[]).map(message=>`<p>${esc(message)}</p>`).join('');
 $('#watchlist').innerHTML=(state.watchlist||[]).map(keyword=>`<div class="watch-row"><span>${esc(keyword)}</span><button class="ghost" data-unwatch="${esc(keyword)}" type="button">Remove</button></div>`).join('')||'<p class="empty">Nothing is being watched. Watchlist entries never create board cards.</p>';
}
function renderBlogs(){
 $('#blog-list').innerHTML=(state.blogs||[]).map(task=>`<article class="card"><div class="card-row"><button class="open" data-open="${esc(task.id)}" type="button"><span class="pill">${esc(task.decision_status)}</span><h3>${esc(task.title||task.id)}</h3><p class="meta">${esc(task.id)} · ${task.article?.word_count??0} words · ${task.article?.read_minutes??0} min read</p></button><span class="meta">${esc(task.change_status||task.status||'')}</span></div></article>`).join('')||'<p class="empty">No blog has been written yet. Writing is blocked until the content KPI set is approved; only cards backed by an artifact under artifacts/ appear here.</p>';
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
function renderAll(){renderTopics();renderTrends();renderBlogs();renderGsc();renderGa4();}

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
 if(quiet&&openTask)return;
 const range=$('#range').value;const device=$('#device').value;
 try{state=await api(`/ceo/api/state?range=${encodeURIComponent(range)}&device=${encodeURIComponent(device)}`);renderAll();if(!quiet)notice('');}
 catch(error){if(!quiet)notice(error.message,true);}
}
async function addTopics(){
 const topics=$('#topic-batch').value.split(/\n/).map(value=>value.trim()).filter(Boolean);
 try{const result=await api('/ceo/api/topics',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({topics})});const skipped=(result.skipped||[]).map(item=>`${item.title}: ${item.reason}`).join(' · ');$('#topic-result').textContent=`Added ${result.added.length}.${skipped?' Skipped — '+skipped:''}`;$('#topic-batch').value='';await refresh();}
 catch(error){$('#topic-result').textContent=error.message;$('#topic-result').classList.add('error');}
}
async function updateWatch(keyword,action){try{const result=await api('/ceo/api/watchlist',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({keyword,action})});state.watchlist=result.watchlist;renderTrends();}catch(error){notice(error.message,true);}}
async function decide(task,decision){try{await api('/ceo/api/decision',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({task_id:task.id,decision})});closeDetail();await refresh();}catch(error){notice(error.message,true);}}
async function revise(task){const comment=$('#revision-comment').value;try{await api('/ceo/api/revision',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({task_id:task.id,comment})});closeDetail();await refresh();}catch(error){notice(error.message,true);}}
async function upload(task,slot,file){try{await api(`/ceo/api/upload?task=${encodeURIComponent(task.id)}&slot=${encodeURIComponent(slot)}`,{method:'POST',headers:{'X-Filename':file.name},body:file});await refresh();openTask=task.id;detailTab='files';await renderDetail();}catch(error){notice(error.message,true);}}

async function publish(task){
 if(!publishRequest){notice('This card has no current publish instruction. Reopen the Impact tab.',true);return;}
 if(!confirm('Merge '+task.id+' to main and publish it to itarang.com?'))return;
 const button=$('#publish-block [data-publish]');if(button)button.disabled=true;
 try{
  const outcome=await api('/ceo/publish',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({task:task.id,request_id:publishRequest})});
  publishRequest='';
  notice('Published. Merge commit '+(outcome.merge_commit||'').slice(0,7)+'.');
  await refresh();await renderDetail();
 }catch(error){notice(error.message,true);publishRequest='';await refreshPublish(task);}
}
document.addEventListener('click',event=>{
 const button=event.target.closest('button');if(!button)return;
 if(button.dataset.view)showView(button.dataset.view);
 if(button.dataset.open)openDetail(button.dataset.open);
 if(button.dataset.detail){detailTab=button.dataset.detail;renderDetail();}
 if(button.dataset.unwatch)updateWatch(button.dataset.unwatch,'remove');
 if(button.dataset.reader){const task=findTask(openTask);if(button.dataset.reader==='dark'){darkReading=!darkReading;renderDetail();}if(button.dataset.reader==='download')downloadArticle(task);if(button.dataset.reader==='pdf')openPdf(task);if(button.dataset.reader==='print')window.print();}
 if(button.dataset.decision)decide(findTask(openTask),button.dataset.decision);
 if(button.dataset.revision)revise(findTask(openTask));
 if(button.dataset.publish)publish(findTask(openTask));
});
document.addEventListener('change',event=>{if(event.target.matches('[data-upload]')&&event.target.files[0])upload(findTask(openTask),event.target.dataset.upload,event.target.files[0]);if(event.target.matches('#range,#device,#metric'))refresh();});
document.addEventListener('keydown',event=>{if(event.key==='Escape'&&openTask)closeDetail();if(event.key==='/'&&!event.ctrlKey&&!event.metaKey&&!/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName)){event.preventDefault();showView('trending');$('#trend-keyword').focus();}if(/^[1-4]$/.test(event.key)&&!/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName))showView(['topics','trending','blogs','analytics'][Number(event.key)-1]);});
$('#add-topics').addEventListener('click',addTopics);
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