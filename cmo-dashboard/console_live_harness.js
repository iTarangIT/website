/* A DOM with identity, so the console's *behaviour* can be asserted on.
 *
 * `console_harness.js` renders one frame and prints the HTML. That is enough to
 * catch a broken renderer and nothing else. The questions this file exists for
 * cannot be answered from a string:
 *
 *   - does the button go dead before the request comes back?
 *   - is the row that did not change still the same node afterwards?
 *   - does an update overwrite a textarea somebody was typing in?
 *   - does anything reach the network while the tab is hidden?
 *
 * So elements here have children with identity, `insertBefore`/`replaceChild`/
 * `removeChild` move real objects, `document.hidden` is settable, and `fetch` is
 * scripted per step — including a request that never resolves, which is how you
 * observe the busy state that exists only while a request is in flight.
 *
 * A row node is a stub standing for one rendered card: it keeps the markup it was
 * built from and reads its own attributes out of it. Nothing here parses HTML
 * properly, and nothing needs to — the console never reaches inside a row it did
 * not just build.
 *
 * Usage: node console_live_harness.js <script.js> <plan.json>
 */
'use strict';
const fs = require('fs');

const [, , scriptPath, planPath] = process.argv;
const plan = JSON.parse(fs.readFileSync(planPath, 'utf8'));

const later = setTimeout;
const report = { steps: [], requests: [] };

/* ------------------------------------------------------------------ elements */

function attributesOf(html) {
  const open = /^<([a-zA-Z0-9]+)([^>]*)>/.exec(String(html)) || [];
  const found = {};
  String(open[2] || '').replace(/([a-zA-Z-]+)(?:="([^"]*)")?/g, (whole, name, value) => {
    found[name] = value === undefined ? '' : value;
    return whole;
  });
  return { tag: (open[1] || 'div').toUpperCase(), found };
}

let serial = 0;

function makeElement(id, tag, html) {
  const classes = new Set();
  const sub = {};
  const attributes = html ? attributesOf(html).found : {};
  const node = {
    uid: (serial += 1),
    id: id || attributes.id || '',
    tagName: (tag || (html ? attributesOf(html).tag : 'div')).toUpperCase(),
    dataset: {},
    style: {},
    hidden: false,
    disabled: false,
    value: '',
    textContent: '',
    files: [],
    scrollTop: 0,
    children: [],
    _html: html === undefined ? '' : String(html),
    _mode: 'html',
    _source: html === undefined ? '' : String(html),
    classList: {
      add(...names) { names.forEach(name => classes.add(name)); },
      remove(...names) { names.forEach(name => classes.delete(name)); },
      contains(name) { return classes.has(name); },
      toggle(name, force) {
        const on = force === undefined ? !classes.has(name) : Boolean(force);
        if (on) classes.add(name); else classes.delete(name);
        return on;
      },
    },
    get outerHTML() { return this._source || this.innerHTML; },
    get innerHTML() {
      return this._mode === 'children'
        ? this.children.map(child => child.outerHTML).join('')
        : this._html;
    },
    set innerHTML(value) {
      this._mode = 'html';
      this.children.length = 0;
      this._html = String(value == null ? '' : value);
      this._first = this._html ? makeElement('', null, this._html) : null;
    },
    get firstElementChild() {
      if (this._mode === 'children') return this.children[0] || null;
      return this._first || null;
    },
    insertBefore(child, reference) {
      this._mode = 'children';
      const at = this.children.indexOf(child);
      if (at >= 0) this.children.splice(at, 1);
      const index = reference ? this.children.indexOf(reference) : -1;
      if (index < 0) this.children.push(child); else this.children.splice(index, 0, child);
      return child;
    },
    appendChild(child) { return this.insertBefore(child, null); },
    replaceChild(next, old) {
      this._mode = 'children';
      const index = this.children.indexOf(old);
      if (index < 0) this.children.push(next); else this.children[index] = next;
      return old;
    },
    removeChild(child) {
      const index = this.children.indexOf(child);
      if (index >= 0) this.children.splice(index, 1);
      return child;
    },
    setAttribute(name, value) { attributes[name] = String(value); },
    getAttribute(name) { return name in attributes ? attributes[name] : null; },
    removeAttribute(name) { delete attributes[name]; },
    toggleAttribute() {}, addEventListener() {}, removeEventListener() {},
    focus() {}, select() {}, blur() {}, click() {}, remove() {},
    prepend() {}, replaceChildren() {}, scrollIntoView() {},
    insertAdjacentHTML(position, markup) {
      this._html = position === 'afterbegin' ? markup + this._html : this._html + markup;
    },
    getBoundingClientRect() { return { left: 0, top: 0, width: 120, height: 24 }; },
    get clientWidth() { return 760; },
    get offsetWidth() { return 120; },
    get offsetLeft() { return 0; },
    closest() { return null; },
    querySelector(selector) {
      const key = String(selector);
      if (!sub[key]) sub[key] = makeElement(`${this.id}${key}`, 'div');
      return sub[key];
    },
    querySelectorAll() { return []; },
  };
  return node;
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
const nestedButtons = ['read', 'files'].map(name => {
  const button = makeElement('', 'button');
  button.dataset.detail = name;
  return button;
});
/* The tab badges live in the document, not in any panel. */
/* Nodes the document ships with a `hidden` attribute already on them. The
   registry cannot know that, and a test asking "did it stay hidden?" would get a
   free pass if it started visible. */
['topics-pending', 'topics-new', 'blogs-pending', 'blogs-new', 'competitor-result',
 'editor-conflict', 'detail-pending', 'detail-error'].forEach(id => { byId(id).hidden = true; });
const badges = new Map(['topics', 'blogs'].map(name => {
  const badge = makeElement('', 'span');
  badge.hidden = true;
  return [`[data-badge="${name}"]`, badge];
}));
/* Buttons the console looks up by attribute after rendering a row. */
const loose = new Map();
function looseButton(selector) {
  if (!loose.has(selector)) {
    const button = makeElement('', 'button');
    loose.set(selector, button);
  }
  return loose.get(selector);
}

const listeners = new Map();
const document = {
  activeElement: { tagName: 'BODY', blur() {} },
  hidden: false,
  addEventListener(type, handler) {
    if (!listeners.has(type)) listeners.set(type, []);
    listeners.get(type).push(handler);
  },
  createElement(tag) { return makeElement('', tag); },
  querySelector(selector) {
    const key = String(selector);
    if (key.startsWith('#')) return byId(key.slice(1));
    if (badges.has(key)) return badges.get(key);
    if (key === '.primary button.active') return primaryButtons.find(b => b.classList.contains('active')) || null;
    if (key === '.tab-indicator') return makeElement('', 'span');
    if (key === '.chart-wrap') return makeElement('', 'div');
    if (/^\[data-(approve|undo|queue|decision|revision|editor|form-submit|upload|publish)/.test(key)
        || key.startsWith('#publish-block')) return looseButton(key);
    if (key.startsWith('[data-proposal=') || key.startsWith('[data-opportunity=')) return looseButton(key);
    if (key.startsWith('[data-form=')) return looseButton(key);
    return null;
  },
  querySelectorAll(selector) {
    if (selector === '.screen') return panels;
    if (selector === '.primary button') return primaryButtons;
    if (selector === '.nested button') return nestedButtons;
    return [];
  },
};
function fire(type, detail) {
  (listeners.get(type) || []).forEach(handler => handler(detail || {}));
}

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
if (plan.ui) localStorage.setItem('cmo_console_ui_v2', JSON.stringify(plan.ui));

/* -------------------------------------------------------------------- network */
/* `state` and `version` are swapped between steps; `hang` makes the next matching
   request never resolve, which is the only way to see a busy state stand still. */
let currentState = plan.state;
let currentVersion = plan.version || 'v1';
let failNext = null;
let hangNext = null;
/* The publish check's answer, so a test can drive the block's three outcomes:
   refused with reasons, eligible, or malformed. */
let publishCheck = plan.publishCheck || {
  eligible: false, blockers: ['no Gate 1 approval is recorded for this card'],
  files: [], slug: '', category: '', request_id: '',
};

async function fetchStub(path, options) {
  const url = String(path);
  report.requests.push(url);
  if (hangNext && url.startsWith(hangNext)) return new Promise(() => {});
  if (failNext && url.startsWith(failNext.path)) {
    return {
      ok: false, status: failNext.status || 400, statusText: 'Refused',
      json: async () => ({ error: failNext.error }),
    };
  }
  let payload = { ok: true };
  if (url.startsWith('/ceo/blog-publish-check')) payload = publishCheck;
  if (url.startsWith('/api/session')) payload = { email: 'sanchit@itarang.com', role: 'ceo', console: '/ceo' };
  else if (url.startsWith('/ceo/api/state')) payload = currentState;
  else if (url.startsWith('/ceo/api/version')) payload = { version: currentVersion };
  else if (url.startsWith('/ceo/api/propose')) {
    payload = {
      ok: true, added: [{ id: 99 }], suppressed: [], duplicates: [], dropped: [],
      messages: [], cache_hit: false, credits_used: 5, credits_remaining: 120,
    };
  }
  return { ok: true, status: 200, statusText: 'OK', json: async () => payload, blob: async () => ({}) };
}

const scrolls = [];
const location = { replace(target) { throw new Error('unexpected redirect to ' + target); } };
Object.assign(globalThis, {
  document, sessionStorage, localStorage, location,
  fetch: fetchStub,
  window: {
    addEventListener(type, handler) { document.addEventListener(`window:${type}`, handler); },
    print() {}, open() { return null; },
    scrollY: 0,
    scrollTo(x, y) { scrolls.push(y); this.scrollY = y; },
  },
  requestAnimationFrame(callback) { callback(); },
  CSS: { escape: value => String(value).replace(/["\\]/g, '\\$&') },
  confirm: () => true,
  alert: () => {},
});

const source = fs.readFileSync(scriptPath, 'utf8')
  + '\n;globalThis.__console={renderAll,renderDetail,researchSubject,saveEdit,pollVersion,'
  + 'schedulePoll,resumePolling,refresh,showView,patchRows,fresh,'
  + 'get state(){return state},set state(value){state=value},get ui(){return ui},'
  + 'get busy(){return busy},get editing(){return editing},set editing(value){editing=value},'
  + 'get editorText(){return editorText},set editorText(value){editorText=value},'
  + 'get editorBase(){return editorBase},set editorBase(value){editorBase=value},'
  + 'set openTask(value){openTask=value},get openTask(){return openTask},'
  + 'set detailTab(value){detailTab=value},get detailTab(){return detailTab},'
  + 'set checkTimeout(value){CHECK_TIMEOUT_MS=value},refreshBlogPublish,'
  + 'get pollTimer(){return Boolean(pollTimer)},'
  + 'get pollStep(){return pollStep},get pollDelay(){return POLL_LADDER[pollStep]},'
  + 'get versionToken(){return versionToken},setUi};';
(0, eval)(source);

/* ---------------------------------------------------------------------- steps */

const rowsOf = id => byId(id).children.map(child => ({ uid: child.uid, key: child.getAttribute('data-key') }));
const settle = () => new Promise(resolve => later(resolve, 5));

async function main() {
  await settle();
  for (const step of plan.steps || []) {
    if (step.state) currentState = step.state;
    if (step.version) currentVersion = step.version;
    if (step.hidden !== undefined) document.hidden = step.hidden;
    if (step.fail !== undefined) failNext = step.fail;
    if (step.hang !== undefined) hangNext = step.hang;
    if (step.ui) Object.keys(step.ui).forEach(key => globalThis.__console.setUi(key, step.ui[key], false));
    if (step.searchBox) byId(`${step.searchBox.view}-search`).value = step.searchBox.text;
    if (step.subject) byId('subject').value = step.subject;
    if (step.editing) {
      globalThis.__console.openTask = step.editing.task;
      globalThis.__console.editing = true;
      globalThis.__console.editorBase = step.editing.base;
      globalThis.__console.editorText = step.editing.text;
    }

    const before = { proposals: rowsOf('proposal-list'), blogs: rowsOf('blog-list') };
    const started = report.requests.length;
    let immediate = null;

    if (step.do === 'poll') await globalThis.__console.pollVersion();
    if (step.do === 'refresh') await globalThis.__console.refresh(Boolean(step.quiet));
    if (step.do === 'showView') globalThis.__console.showView(step.view);
    // Open one card on one detail tab. The decision controls live here, and
    // whether they are rendered at all depends on the card's lane.
    if (step.publishCheck !== undefined) publishCheck = step.publishCheck;
    if (step.checkTimeout) globalThis.__console.checkTimeout = step.checkTimeout;
    if (step.do === 'detail') {
      globalThis.__console.openTask = step.task;
      globalThis.__console.detailTab = step.tab || 'discussion';
      await globalThis.__console.renderDetail(true);
    }
    if (step.do === 'fire') fire(step.event);
    if (step.do === 'research') {
      const running = globalThis.__console.researchSubject(step.subject);
      // Read the button in the same turn the click happened: the busy state has
      // to be there before anything comes back, not after.
      const button = byId('research-subject');
      immediate = {
        disabled: button.disabled,
        label: button.textContent,
        busy: globalThis.__console.busy,
        skeleton: byId('topics-pending').innerHTML,
        skeletonHidden: byId('topics-pending').hidden,
      };
      if (!step.hang) await running;
    }

    const after = { proposals: rowsOf('proposal-list'), blogs: rowsOf('blog-list') };
    report.steps.push({
      name: step.name || step.do || 'step',
      immediate,
      requests: report.requests.slice(started),
      rowsBefore: before,
      rowsAfter: after,
      proposalsHtml: byId('proposal-list').innerHTML,
      blogsHtml: byId('blog-list').innerHTML,
      topicsPending: byId('topics-pending').innerHTML,
      topicsPendingHidden: byId('topics-pending').hidden,
      topicsNew: byId('topics-new').innerHTML,
      topicsNewHidden: byId('topics-new').hidden,
      blogsNew: byId('blogs-new').innerHTML,
      blogsNewHidden: byId('blogs-new').hidden,
      badges: ['topics', 'blogs'].map(name => {
        const badge = badges.get(`[data-badge="${name}"]`);
        return { view: name, text: badge.textContent, hidden: badge.hidden };
      }),
      proposeResult: byId('propose-result').textContent,
      editorText: globalThis.__console.editorText,
      editorInput: byId('editor-input').value,
      editorConflict: byId('editor-conflict').textContent,
      editorConflictHidden: byId('editor-conflict').hidden,
      pollActive: globalThis.__console.pollTimer,
      pollDelay: globalThis.__console.pollDelay,
      pollStep: globalThis.__console.pollStep,
      versionToken: globalThis.__console.versionToken,
      ui: globalThis.__console.ui,
      searchBoxes: {
        topics: byId('topics-search').value,
        blogs: byId('blogs-search').value,
      },
      scrolls: scrolls.slice(),
      detailBody: byId('detail-body').innerHTML,
      /* The publish block reports itself. detail-body holds the string setHtml put
         there; refreshBlogPublish then writes into child nodes, and this fake DOM
         does not fold a child's innerHTML back into its parent's. Reading the
         parent would show the placeholder forever and call it a pass. */
      blogPublish: {
        state: byId('blog-publish-state').innerHTML || byId('blog-publish-state').textContent,
        checked: byId('blog-publish-block').dataset.checked || '',
        disabled: Boolean(byId('blog-publish-block').querySelector('[data-blog-publish]').disabled),
      },
    });
  }
  report.requests = report.requests.slice();
  process.stdout.write(JSON.stringify(report), () => process.exit(0));
}

main();
