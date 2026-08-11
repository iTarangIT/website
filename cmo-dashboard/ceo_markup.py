BODY = '''<main id="app">
<header class="topbar"><div class="mark" aria-hidden="true">iT</div><div class="topbar-title"><p class="eyebrow">iTarang CEO Console</p><h1>Content flow</h1></div><span id="account" class="meta"></span><button id="signout" class="ghost" type="button">Sign out</button></header>
<nav class="primary" aria-label="CEO workflow">
<button data-view="analytics" type="button"><kbd>1</kbd> Analytics</button>
<button class="active" data-view="topics" type="button"><kbd>2</kbd> Topics &amp; Research</button>
<button data-view="blogs" type="button"><kbd>3</kbd> Blogs</button>
<span class="tab-indicator" aria-hidden="true"></span>
</nav>
<p id="notice" class="notice" role="status"></p>

<section id="panel-analytics" class="screen paper" hidden>
<div class="section-head"><div><h2>Where we stand</h2><p class="meta">Our own numbers, and the sites we are trying to overtake.</p></div></div>
<div class="controls">
<label>Range<select id="range"><option value="7">7 days</option><option value="28" selected>28 days</option><option value="90">90 days</option></select></label>
<label>Device<select id="device"><option value="all">All devices</option><option value="desktop">Desktop</option><option value="mobile">Mobile</option><option value="tablet">Tablet</option></select></label>
<label>Metric<select id="metric"><option value="sessions">Sessions</option><option value="active_users">Active users</option><option value="screen_page_views">Page views</option><option value="engagement_rate">Engagement rate</option></select></label>
</div>
<div class="analytics-grid"><article class="tile"><h3>Google Search Console</h3><p class="meta">How people find iTarang in Google Search.</p><div id="gsc-panel"></div></article><article class="tile"><h3>Google Analytics 4</h3><p class="meta">What visitors do after reaching the site.</p><div id="ga4-panel"></div></article></div>
<h3 class="rule">Which website do you want to replicate?</h3>
<p class="meta">Reads their sitemap free, then up to 10 of their pages, and scores each topic against our own Search Console position.</p>
<div class="subject-box"><label class="field">Competitor website<input id="competitor" type="text" maxlength="253" placeholder="example.com"></label><button id="analyse-competitor" type="button">Analyse</button></div>
<div id="competitor-panel"></div>
</section>

<section id="panel-topics" class="screen paper">
<div class="section-head"><div><h2>Topics &amp; Research</h2><p class="meta">Enter a rough subject. Hermes researches it and proposes candidate topics for you to decide on.</p></div><span id="credit-meter" class="meta"></span></div>
<div class="subject-box"><label class="field">Rough subject<input id="subject" type="text" maxlength="180" placeholder="three wheeler battery data"></label><button id="research-subject" type="button">Research this subject</button></div>
<p class="meta">Researching costs Firecrawl credits and creates no board card. Only a topic you approve becomes one.</p>
<div id="propose-result" class="notice"></div>
<h3 class="rule">Candidate topics awaiting your decision</h3><div id="proposal-list" class="rows" role="list"></div>
<details id="rejected-box"><summary>Rejected topics <span id="rejected-count" class="meta"></span></summary><p class="meta">These are remembered so the agent does not propose them again. Undo returns one to the pool.</p><div id="rejected-list" class="rows"></div></details>
<details id="carded-box"><summary>Approved and queued for writing <span id="carded-count" class="meta"></span></summary><div id="carded-list" class="rows"></div></details>
<h3 class="rule">Trends from connected sources</h3>
<div class="keyword-box"><label class="field">Keyword box<input id="trend-keyword" type="search" placeholder="Filter the connected trend sources"></label><button id="watch-keyword" class="ghost" type="button">Add to watchlist</button></div>
<p class="meta">This keyword steers the trend list below. It does not create a topic or a card.</p>
<div id="trend-list" class="rows"></div><div id="trend-messages" class="notice"></div>
<h4>Watchlist</h4><div id="watchlist" class="rows"></div>
</section>

<section id="panel-blogs" class="screen paper" hidden>
<div class="section-head"><div><h2>Read and decide on blogs</h2><p class="meta">Articles the writer has produced from approved topics.</p></div></div>
<div id="blog-list" class="rows" role="list"></div>
</section>

<footer class="shortcuts"><span><kbd>1</kbd><kbd>2</kbd><kbd>3</kbd> tabs</span><span><kbd>/</kbd> search</span><span><kbd>j</kbd><kbd>k</kbd> move</span><span><kbd>Enter</kbd> open</span><span><kbd>Esc</kbd> close</span></footer>
<div id="toast" class="toast" role="status" aria-live="polite" hidden></div>
<dialog id="detail"><div class="dialog-head"><div><p id="detail-id" class="eyebrow"></p><h2 id="detail-title"></h2></div><button id="close-detail" class="ghost" type="button" aria-label="Close">Close</button></div>
<nav class="nested" aria-label="Blog detail"><button class="active" data-detail="read" type="button">Read</button><button data-detail="impact" type="button">Impact</button><button data-detail="discussion" type="button">Discussion</button><button data-detail="files" type="button">Files</button></nav>
<div id="detail-body"></div></dialog>
</main>'''

MARKUP = BODY
