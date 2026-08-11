/* A DOM small enough to run the CEO console script under node.
 *
 * The console's rendering used to live in a JavaScript string that nothing ever
 * executed, which is how a reader that printed raw Markdown passed every suite.
 * This harness executes it: it boots the script against a fixture state and
 * prints the HTML each panel produced, so a Python test can assert on it.
 *
 * Usage: node console_harness.js <script.js> <fixture.json>
 */
'use strict';
const fs = require('fs');

const [, , scriptPath, fixturePath] = process.argv;
const fixture = JSON.parse(fs.readFileSync(fixturePath, 'utf8'));

function makeElement(id, tag) {
  const set = new Set();
  const sub = {};
  return {
    id: id || '',
    tagName: (tag || 'div').toUpperCase(),
    dataset: {},
    style: {},
    hidden: false,
    value: '',
    textContent: '',
    files: [],
    _html: '',
    classList: {
      add(...names) { names.forEach(name => set.add(name)); },
      remove(...names) { names.forEach(name => set.delete(name)); },
      contains(name) { return set.has(name); },
      toggle(name, force) {
        const on = force === undefined ? !set.has(name) : Boolean(force);
        if (on) set.add(name); else set.delete(name);
        return on;
      },
      get list() { return [...set]; },
    },
    get innerHTML() { return this._html; },
    set innerHTML(value) { this._html = String(value == null ? '' : value); },
    get clientWidth() { return 760; },
    get offsetWidth() { return 120; },
    get offsetLeft() { return 0; },
    setAttribute() {}, getAttribute() { return null; }, removeAttribute() {},
    toggleAttribute() {}, addEventListener() {}, removeEventListener() {},
    focus() {}, select() {}, blur() {}, click() {}, remove() {},
    prepend() {}, replaceChildren() {}, scrollIntoView() {},
    insertAdjacentHTML(position, html) {
      this._html = position === 'afterbegin' ? html + this._html : this._html + html;
    },
    getBoundingClientRect() { return { left: 0, top: 0, width: 120, height: 24 }; },
    closest() { return null; },
    querySelector(selector) {
      if (!sub[selector]) sub[selector] = makeElement(`${id}${selector}`, 'div');
      return sub[selector];
    },
    querySelectorAll() { return []; },
  };
}

const registry = new Map();
function byId(id) {
  if (!registry.has(id)) registry.set(id, makeElement(id, id.includes('table') ? 'table' : 'div'));
  return registry.get(id);
}

const panels = ['topics', 'blogs', 'analytics'].map(name => {
  const panel = makeElement(`panel-${name}`, 'section');
  panel.hidden = name !== 'topics';
  registry.set(`panel-${name}`, panel);
  return panel;
});
const primaryButtons = ['topics', 'blogs', 'analytics'].map(name => {
  const button = makeElement('', 'button');
  button.dataset.view = name;
  if (name === 'topics') button.classList.add('active');
  return button;
});
const nestedButtons = ['read', 'impact', 'discussion', 'files'].map(name => {
  const button = makeElement('', 'button');
  button.dataset.detail = name;
  return button;
});

const document = {
  activeElement: { tagName: 'BODY', blur() {} },
  // This harness renders one frame and exits; it is not a visible tab, so the
  // version poller correctly never starts here. console_live_harness.js is the
  // one that drives polling, and it owns `hidden` as a settable flag.
  hidden: true,
  addEventListener() {},
  createElement(tag) { return makeElement('', tag); },
  querySelector(selector) {
    if (selector.startsWith('#')) return byId(selector.slice(1));
    if (selector === '.primary button.active') return primaryButtons.find(b => b.classList.contains('active')) || null;
    if (selector === '.tab-indicator') return makeElement('', 'span');
    if (selector === '.chart-wrap') return makeElement('', 'div');
    return null;
  },
  querySelectorAll(selector) {
    if (selector === '.screen') return panels;
    if (selector === '.primary button') return primaryButtons;
    if (selector === '.nested button') return nestedButtons;
    return [];
  },
};

function makeStorage() {
  const store = new Map();
  return {
    getItem(key) { return store.has(key) ? store.get(key) : null; },
    setItem(key, value) { store.set(key, String(value)); },
    removeItem(key) { store.delete(key); },
  };
}
const sessionStorage = makeStorage();
sessionStorage.setItem('cmo_token', 'harness-token');
const localStorage = makeStorage();
if (fixture.ui) localStorage.setItem('cmo_console_ui_v2', JSON.stringify(fixture.ui));

const requests = [];
async function fetchStub(path) {
  requests.push(String(path));
  const url = String(path);
  let payload;
  if (url.startsWith('/api/session')) {
    payload = { email: 'sanchit@itarang.com', role: 'ceo', console: '/ceo' };
  } else if (url.startsWith('/ceo/api/state')) {
    payload = fixture.state;
  } else {
    payload = { ok: true };
  }
  return {
    ok: true, status: 200, statusText: 'OK',
    json: async () => payload,
    blob: async () => ({}),
  };
}

const location = { replace(target) { throw new Error('unexpected redirect to ' + target); } };
const globals = {
  document, sessionStorage, localStorage, location,
  fetch: fetchStub,
  window: { addEventListener() {}, print() {}, open() { return null; } },
  requestAnimationFrame(callback) { callback(); },
  setInterval() { return 0; },
  CSS: { escape: value => String(value).replace(/["\\]/g, '\\$&') },
  confirm: () => true,
  alert: () => {},
};
Object.assign(globalThis, globals);

const source = fs.readFileSync(scriptPath, 'utf8')
  + '\n;globalThis.__console={renderAll,renderDetail,detailRead,editorHtml,figure,page,showView,'
  + 'get state(){return state},set state(value){state=value},get ui(){return ui},'
  + 'set editing(value){editing=value},set editorText(value){editorText=value},'
  + 'set openTask(value){openTask=value},setUi};';
(0, eval)(source);

setTimeout(() => {
  const api = globalThis.__console;
  const html = id => byId(id).innerHTML;
  const task = (fixture.state.blogs || [])[0];
  let readHtml = '';
  let editorHtmlOut = '';
  if (task) {
    readHtml = api.detailRead(task);
    api.editorText = task.article ? task.article.text : '';
    editorHtmlOut = api.editorHtml(task);
  }
  process.stdout.write(JSON.stringify({
    requests,
    ui: api.ui,
    activeView: primaryButtons.filter(b => b.classList.contains('active')).map(b => b.dataset.view),
    visiblePanels: panels.filter(p => !p.hidden).map(p => p.id),
    proposals: html('proposal-list'),
    topicsPager: html('topics-pager'),
    topicsCount: byId('topics-count').textContent,
    topicsFilter: html('topics-filter'),
    blogs: html('blog-list'),
    blogsPager: html('blogs-pager'),
    blogsCount: byId('blogs-count').textContent,
    tiles: html('stat-tiles'),
    chart: html('chart'),
    chartLegend: html('chart-legend'),
    opportunities: html('opportunity-list'),
    queriesBody: byId('queries-table').querySelector('tbody').innerHTML,
    pagesBody: byId('pages-table').querySelector('tbody').innerHTML,
    queriesPager: html('queries-pager'),
    footnote: byId('analytics-footnote').textContent,
    creditMeter: byId('credit-meter').innerHTML + byId('credit-meter').textContent,
    creditMeterError: byId('credit-meter').classList.contains('error'),
    ga4: html('ga4-panel'),
    queued: html('queued-list'),
    read: readHtml,
    editor: editorHtmlOut,
  }), () => process.exit(0));
}, 20);
