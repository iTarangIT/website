SCRIPT = r'''
const $ = selector => document.querySelector(selector);
const esc = value => String(value ?? '').replace(/[&<>"']/g, char => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
}[char]));

let token = sessionStorage.getItem('cmo_token') || '';
let email = sessionStorage.getItem('cmo_email') || '';
let role = sessionStorage.getItem('cmo_role') || '';
let state = null;
let tab = 'board';

function clearSession(message = '') {
  sessionStorage.removeItem('cmo_token');
  sessionStorage.removeItem('cmo_email');
  sessionStorage.removeItem('cmo_role');
  location.replace(message === 'expired' ? '/?msg=expired' : '/');
}

async function api(path, options = {}) {
  options.headers = {...(options.headers || {}), Authorization: 'Bearer ' + token};
  const response = await fetch(path, options);
  if (response.status === 401 || response.status === 403) {
    clearSession('expired');
    throw new Error('Session expired');
  }
  const payload = await response.json().catch(() => ({error: response.statusText}));
  if (!response.ok) throw new Error(payload.error || response.statusText);
  return payload;
}

function value(item) {
  return item === null || item === undefined || item === '' ? '—' : esc(item);
}

function boardView() {
  const lanes = ['Backlog', 'In Progress', 'CMO Review', 'Human Approval', 'Completed'];
  return '<div class="board">' + lanes.map(lane =>
    '<section class="column"><h2>' + esc(lane) + '</h2>' +
    ((state.board[lane] || []).map(task =>
      '<article class="card" data-task="' + esc(task.id) + '">' +
      '<strong>' + esc(task.title || task.id) + '</strong>' +
      '<p class="meta">' + esc(task.id) + ' · ' + esc(task.skill || task.owner || '—') +
      ' · ' + esc(task.priority || '—') + '</p></article>'
    ).join('') || '<p class="empty">No cards</p>') + '</section>'
  ).join('') + '</div>';
}

function runtimeView() {
  const runtime = state.runtime;
  const runs = ['plan', 'execute', 'review'].map(name => {
    const run = runtime.last_runs[name];
    return '<tr><th>' + esc(name) + '</th><td>' + value(run && run.timestamp) +
      '</td><td>' + value(run && run.skill) + '</td><td>' + value(run && run.source) + '</td></tr>';
  }).join('');
  const skills = runtime.skills.map(skill =>
    '<tr><td>' + esc(skill.name) + '</td><td>' +
    ((skill.files || []).map(esc).join('<br>') || '—') + '</td><td>' +
    value(skill.disabled_reason) + '</td></tr>'
  ).join('');
  return '<div class="grid">' +
    '<div class="tile"><span>Current run type</span><strong>' + value(runtime.current_run_type) + '</strong></div>' +
    '<div class="tile"><span>In progress</span><strong>' + value(runtime.in_progress_task) + '</strong></div>' +
    '<div class="tile"><span>Gateway</span><strong>' + value(runtime.gateway.state) + '</strong><p>' + value((runtime.gateway.pids || []).join(', ')) + '</p></div>' +
    '<div class="tile"><span>Dashboard</span><strong>' + value(runtime.dashboard.state) + '</strong><p>PID ' + value(runtime.dashboard.pid) + '</p></div>' +
    '</div><section class="panel"><h2>Last runs</h2><table><thead><tr><th>Run</th><th>Timestamp</th><th>Skill</th><th>Source</th></tr></thead><tbody>' + runs +
    '</tbody></table><h2>CMO skill files</h2><table><thead><tr><th>Skill</th><th>Files</th><th>Availability</th></tr></thead><tbody>' + skills +
    '</tbody></table><h2>Structural validator</h2><button id="validate" type="button">Run validator</button><pre id="validation">Not run</pre>' +
    '<h2>Logs</h2><button data-log="hourly-cycle.log" type="button">Load hourly cycle</button> ' +
    '<button data-log="morning-review.log" type="button">Load morning review</button><pre id="logs">Load on demand</pre></section>';
}

function spendView() {
  const spend = state.spend;
  const providerRows = Object.entries(spend.providers || {}).map(([name, item]) =>
    '<tr><td>' + esc(name) + '</td><td>' + esc(item.calls) + '</td><td>' + esc(item.unmeasured) + '</td></tr>'
  ).join('');
  const rows = spend.runs.map(row => '<tr><td>' + value(row.date) + '</td><td>' +
    value(row.run_type) + '</td><td>' + value(row.skill) + '</td><td>' + value(row.tokens) +
    '</td><td>' + (row.rupee_cost === null ? 'unmeasured' : esc(row.rupee_cost)) +
    '</td><td>' + value(row.provider) + '</td></tr>').join('');
  return '<div class="grid">' +
    '<div class="tile"><span>Firecrawl credits today</span><strong>' + value(spend.firecrawl.today) + '</strong><p>' + esc(spend.firecrawl.today_detail || '') + '</p></div>' +
    '<div class="tile"><span>Firecrawl month / 1,000</span><strong>' + value(spend.firecrawl.month) + '</strong><p>' + esc(spend.firecrawl.month_detail || '') + '</p></div>' +
    '<div class="tile"><span>Unmeasured cost rows</span><strong>' + esc(spend.unmeasured) + '</strong></div>' +
    '<div class="tile"><span>₹300 daily halt</span><strong>' + esc(spend.daily_halt_state) + '</strong><p>Measured today: ₹' + esc(spend.daily_rupees) + '; unmeasured rows: ' + esc(spend.today_unmeasured) + '</p></div>' +
    '</div><section class="panel"><h2>Calls by provider</h2><table><thead><tr><th>Provider</th><th>Calls</th><th>Unmeasured cost</th></tr></thead><tbody>' + providerRows +
    '</tbody></table><h2>Per-run accounting</h2><div class="table-wrap"><table><thead><tr><th>Date</th><th>Run type</th><th>Skill</th><th>Tokens</th><th>Rupee cost</th><th>Provider</th></tr></thead><tbody>' + rows + '</tbody></table></div></section>';
}

function infrastructureView() {
  return '<div class="grid">' + state.infrastructure.map(tile =>
    '<div class="tile"><span>' + esc(tile.name) + '</span><strong>' + esc(tile.value) +
    '</strong><p>' + esc(tile.meaning) + '</p><p class="meta">' + esc(tile.detail) + '</p></div>'
  ).join('') + '</div>';
}

function gscPanel(gsc) {
  const pages = (gsc.pages || []).map(page => '<tr><td>' + value(page.page) + '</td><td>' +
    value(page.impressions) + '</td><td>' + value(page.clicks) + '</td><td>' +
    value(page.average_position) + '</td></tr>').join('');
  return '<section class="panel"><h2>Google Search Console</h2><p>' + esc(gsc.message || '') +
    '</p><p>Collection start: ' + value(gsc.collection_start) + '</p><div class="grid">' +
    '<div class="tile"><span>Impressions</span><strong>' + value(gsc.impressions) + '</strong></div>' +
    '<div class="tile"><span>Clicks</span><strong>' + value(gsc.clicks) + '</strong></div>' +
    '<div class="tile"><span>Average position</span><strong>' + value(gsc.average_position) + '</strong></div>' +
    '<div class="tile"><span>Indexation coverage</span><strong>' + value(gsc.indexation_coverage) + '</strong><p>' +
    value(gsc.indexed_pages) + ' indexed / ' + value(gsc.submitted_pages) + ' submitted</p></div></div>' +
    '<h3>Per-page discovery</h3><div class="table-wrap"><table><thead><tr><th>Page</th><th>Impressions</th><th>Clicks</th><th>Position</th></tr></thead><tbody>' +
    (pages || '<tr><td colspan="4">No Search Console page data</td></tr>') + '</tbody></table></div></section>';
}

function ga4Panel(ga4) {
  if (!ga4 || ga4.status !== 'ready') {
    return '<section class="panel"><h2>Google Analytics 4</h2><p>' + esc((ga4 && ga4.message) || 'Google Analytics is not connected yet') +
      '</p><p>Collection start: ' + value(ga4 && ga4.collection_start) + '</p></section>';
  }
  const metrics = Object.entries(ga4.metrics || {}).map(([name, metric]) =>
    '<div class="tile"><span>' + esc(name.replaceAll('_', ' ')) + '</span><strong>' +
    value(metric) + '</strong><p>' +
    (ga4.deltas && ga4.deltas[name] !== null && ga4.deltas[name] !== undefined ? esc(ga4.deltas[name]) + ' change' : 'No comparison window') + '</p></div>'
  ).join('');
  const pages = (ga4.pages || []).map(page => '<tr><td>' + value(page.page) + '</td><td>' +
    value(page.screen_page_views) + '</td><td>' + value(page.sessions) + '</td><td>' +
    value(page.engagement_rate) + '</td></tr>').join('');
  return '<section class="panel"><h2>Google Analytics 4</h2><p>' + esc(ga4.detail_message || '') + '</p><p>Collection start: ' + value(ga4.collection_start) +
    '</p><div class="grid">' + metrics + '</div><h3>Per-page behavior</h3><div class="table-wrap"><table><thead><tr><th>Page</th><th>Views</th><th>Sessions</th><th>Engagement rate</th></tr></thead><tbody>' +
    (pages || '<tr><td colspan="4">No GA4 page data</td></tr>') + '</tbody></table></div></section>';
}

function analyticsView() {
  return gscPanel(state.analytics.search_console || {}) + ga4Panel(state.analytics.ga4 || {});
}

function render() {
  const views = {board: boardView, runtime: runtimeView, spend: spendView,
    infrastructure: infrastructureView, analytics: analyticsView};
  $('#view').innerHTML = views[tab]();
  bind();
}

function bind() {
  document.querySelectorAll('[data-task]').forEach(element => {
    element.onclick = () => detail(element.dataset.task);
  });
  const validator = $('#validate');
  if (validator) validator.onclick = validateBoard;
  document.querySelectorAll('[data-log]').forEach(element => {
    element.onclick = () => loadLog(element.dataset.log);
  });
}

function formatField(name) {
  return name.replaceAll('_', ' ').replace(/\b\w/g, char => char.toUpperCase());
}

function detail(id) {
  const task = state.tasks.find(item => item.id === id);
  const hidden = new Set(['approval_thread', 'article', 'research_brief']);
  const fields = Object.entries(task).filter(([name]) => !hidden.has(name)).map(([name, item]) =>
    '<tr><th>' + esc(formatField(name)) + '</th><td>' +
    esc(item && typeof item === 'object' ? JSON.stringify(item) : item) + '</td></tr>'
  ).join('');
  const thread = (task.approval_thread || []).map((event, index) =>
    '<li><strong>' + esc(event.timestamp || 'No timestamp') + '</strong> · ' +
    esc(event.approver_id || event.author || 'Unknown author') + ' · ' +
    esc(event.decision || event.outcome || 'event') + ' via ' + esc(event.surface || 'unknown surface') +
    (event.send_back_text ? '<p>' + esc(event.send_back_text) + '</p>' : '') + '</li>'
  ).join('');
  const canApprove = task.section === 'Human Approval' && !task.decision_summary;
  $('#detail-body').innerHTML = '<h2>' + esc(task.title || task.id) + '</h2><table>' + fields +
    '</table><h3>Full approval thread</h3><ol>' + (thread || '<li>No approval events</li>') + '</ol>' +
    (canApprove ? '<div class="actions"><button data-approve="' + esc(task.id) + '" type="button">Approve</button></div>' : '');
  $('#detail').showModal();
  const approveButton = document.querySelector('[data-approve]');
  if (approveButton) approveButton.onclick = () => approve(approveButton.dataset.approve);
}

async function approve(id) {
  try {
    await api('/tech/api/decision', {method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({task_id: id, decision: 'approve'})});
    $('#detail').close();
    await load();
  } catch (error) {
    $('#notice').textContent = error.message;
  }
}

async function validateBoard() {
  const result = await api('/tech/api/validate', {method: 'POST'});
  $('#validation').textContent = JSON.stringify(result, null, 2);
}

async function loadLog(name) {
  const result = await api('/tech/api/logs?name=' + encodeURIComponent(name));
  $('#logs').textContent = result.lines.join('\n');
}

async function load() {
  if (!token) {
    location.replace('/');
    return;
  }
  try {
    state = await api('/tech/api/state');
    render();
  } catch (error) {
    $('#notice').textContent = error.message;
  }
}

$('#logout').onclick = () => clearSession();
$('#close-detail').onclick = () => $('#detail').close();
document.querySelectorAll('nav button').forEach(button => {
  button.onclick = () => {
    document.querySelectorAll('nav button').forEach(item => item.classList.remove('active'));
    button.classList.add('active');
    tab = button.dataset.tab;
    render();
  };
});

load();
'''
