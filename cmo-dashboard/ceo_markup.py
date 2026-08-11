BODY = '''<main id="app">
<header class="topbar"><div class="mark" aria-hidden="true">iT</div><div><p class="eyebrow">iTarang CEO Console</p><h1>Content flow</h1></div><span id="account" class="meta"></span><button id="signout" class="ghost" type="button">Sign out</button></header>
<nav class="primary" aria-label="CEO workflow">
<button class="active" data-view="topics" type="button"><span>1</span> Topics</button>
<button data-view="trending" type="button"><span>2</span> Research</button>
<button data-view="blogs" type="button"><span>3</span> Blogs</button>
<button data-view="analytics" type="button"><span>4</span> Analytics</button>
</nav>
<p id="notice" class="notice" role="status"></p>
<section id="panel-topics" class="screen paper">
<div class="section-head"><div><p class="eyebrow">Step 1</p><h2>Give iTarang topics</h2></div><span class="meta">One topic per line · up to 25</span></div>
<label class="field">Topic batch<textarea id="topic-batch" rows="6" placeholder="Battery intelligence for fleet operators&#10;How EV battery warranties really work"></textarea></label>
<div class="actions"><button id="add-topics" type="button">Add topic batch</button></div>
<div id="topic-result" class="notice"></div><div id="topic-list"></div>
</section>
<section id="panel-trending" class="screen paper" hidden>
<div class="section-head"><div><p class="eyebrow">Step 2</p><h2>Research and trends</h2></div></div>
<div class="keyword-box"><label class="field">Keyword box<input id="trend-keyword" type="search" placeholder="Filter the connected trend sources"></label><button id="watch-keyword" type="button">Add to watchlist</button></div>
<p class="meta">This keyword steers the trend list below. It does not create a Topic card.</p>
<h3>Trends from connected sources</h3><div id="trend-list"></div><div id="trend-messages" class="notice"></div>
<h3>Watchlist</h3><div id="watchlist"></div>
</section>
<section id="panel-blogs" class="screen paper" hidden>
<div class="section-head"><div><p class="eyebrow">Step 3</p><h2>Read and decide on blogs</h2></div></div>
<div id="blog-list"></div>
</section>
<section id="panel-analytics" class="screen paper" hidden>
<div class="section-head"><div><p class="eyebrow">Step 4</p><h2>See what the content moves</h2></div></div>
<div class="controls">
<label>Range<select id="range"><option value="7">7 days</option><option value="28" selected>28 days</option><option value="90">90 days</option></select></label>
<label>Device<select id="device"><option value="all">All devices</option><option value="desktop">Desktop</option><option value="mobile">Mobile</option><option value="tablet">Tablet</option></select></label>
<label>Metric<select id="metric"><option value="sessions">Sessions</option><option value="active_users">Active users</option><option value="screen_page_views">Page views</option><option value="engagement_rate">Engagement rate</option></select></label>
</div>
<div class="analytics-grid"><article><h3>Google Search Console</h3><p class="meta">How people find iTarang in Google Search.</p><div id="gsc-panel"></div></article><article><h3>Google Analytics 4</h3><p class="meta">What visitors do after reaching the site.</p><div id="ga4-panel"></div></article></div>
</section>
<dialog id="detail"><div class="dialog-head"><div><p id="detail-id" class="eyebrow"></p><h2 id="detail-title"></h2></div><button id="close-detail" class="ghost" type="button" aria-label="Close">Close</button></div>
<nav class="nested" aria-label="Blog detail"><button class="active" data-detail="read" type="button">Read</button><button data-detail="impact" type="button">Impact</button><button data-detail="discussion" type="button">Discussion</button><button data-detail="files" type="button">Files</button></nav>
<div id="detail-body"></div></dialog>
</main>'''

MARKUP = BODY
