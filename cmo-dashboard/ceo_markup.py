"""The console's document.

Three tabs, in the order the work happens: find a subject, read what came back,
check whether it landed. Every list carries a toolbar above it and a pager below
it, because none of these lists is short.
"""

BODY = '''<main id="app">
<header class="topbar"><div class="mark" aria-hidden="true">iT</div><div class="topbar-title"><p class="eyebrow">iTarang CEO Console</p><h1>Content flow</h1></div><span id="account" class="meta"></span><button id="signout" class="ghost small" type="button">Sign out</button></header>
<nav class="primary" aria-label="CEO workflow">
<button class="active" data-view="topics" type="button"><kbd>1</kbd> Topics &amp; Research<span class="tab-badge" data-badge="topics" hidden></span></button>
<button data-view="blogs" type="button"><kbd>2</kbd> Blogs<span class="tab-badge" data-badge="blogs" hidden></span></button>
<button data-view="analytics" type="button"><kbd>3</kbd> Analytics</button>
<span class="tab-indicator" aria-hidden="true"></span>
</nav>
<p id="notice" class="notice" role="status"></p>

<section id="panel-topics" class="screen paper">
<div class="section-head"><div><h2>Topics &amp; Research</h2><p class="meta">Enter a rough subject. Hermes researches it and proposes candidate topics for you to decide on.</p></div><span id="credit-meter" class="meta"></span></div>
<div class="subject-box"><label class="field">Rough subject<input id="subject" type="text" maxlength="180" placeholder="three wheeler battery data"></label><button id="research-subject" type="button">Research this subject</button></div>
<p class="meta">Researching costs Firecrawl credits and creates no board card. Only a topic you approve becomes one.</p>
<p id="propose-result" class="notice"></p>

<details id="queued-box"><summary>Queued from Analytics <span id="queued-count" class="meta"></span></summary>
<p class="meta">Subjects you sent over from the Analytics tab. Nothing has been spent on them yet.</p>
<div id="queued-list" class="rows"></div></details>

<h3 class="rule">Candidate topics awaiting your decision</h3>
<div class="toolbar">
<label class="field search"><span class="visually-hidden">Search proposals and keywords</span><input id="topics-search" type="search" placeholder="Search proposals and keywords" autocomplete="off"></label>
<div class="chip-group"><span class="label">Show</span><div class="chips" id="topics-filter"></div></div>
<span class="count" id="topics-count"></span>
</div>
<!-- Where a slow action shows itself: the skeleton while it runs, the reason it
     failed if it did. Both sit where the results will land, not in a toast. -->
<div id="topics-pending" class="rows" aria-live="polite" hidden></div>
<p id="topics-new" class="new-line" role="status" hidden></p>
<div id="proposal-list" class="rows" role="list"></div>
<nav class="pager" id="topics-pager" aria-label="Candidate topics pages"></nav>

<details id="rejected-box"><summary>Rejected topics <span id="rejected-count" class="meta"></span></summary><p class="meta">These are remembered so the agent does not propose them again. Undo returns one to the pool.</p><div id="rejected-list" class="rows"></div></details>
<details id="carded-box"><summary>Approved and queued for writing <span id="carded-count" class="meta"></span></summary><div id="carded-list" class="rows"></div></details>

<h3 class="rule">Trends from connected sources</h3>
<div class="subject-box"><label class="field">Keyword box<input id="trend-keyword" type="search" placeholder="Filter the connected trend sources" autocomplete="off"></label><button id="watch-keyword" class="ghost" type="button">Add to watchlist</button></div>
<p class="meta">This keyword steers the trend list below. It does not create a topic or a card.</p>
<div id="trend-list" class="rows"></div>
<nav class="pager" id="trends-pager" aria-label="Trend pages"></nav>
<div id="trend-messages" class="notice"></div>
<h4>Watchlist</h4><div id="watchlist" class="rows"></div>
</section>

<section id="panel-blogs" class="screen paper" hidden>
<div class="section-head"><div><h2>Blogs</h2><p class="meta">Articles the writer produced from topics you approved. Open one to read it, edit it, or decide on it.</p></div></div>
<div class="toolbar">
<label class="field search"><span class="visually-hidden">Search titles and article text</span><input id="blogs-search" type="search" placeholder="Search titles and article text" autocomplete="off"></label>
<div class="chip-group"><span class="label">Status</span><div class="chips" id="blogs-filter"></div></div>
<span class="count" id="blogs-count"></span>
</div>
<div id="blogs-pending" class="rows" aria-live="polite" hidden></div>
<p id="blogs-new" class="new-line" role="status" hidden></p>
<div id="blog-list" class="rows" role="list"></div>
<nav class="pager" id="blogs-pager" aria-label="Blog pages"></nav>
</section>

<section id="panel-analytics" class="screen paper" hidden>
<div class="section-head"><div><h2>Analytics</h2><p class="meta">What Google Search recorded for itarang.com, and what it suggests writing next.</p></div></div>

<div class="toolbar">
<div class="chip-group"><span class="label">Range</span><div class="chips" id="range-chips"></div></div>
<div class="chip-group"><span class="label">Device</span><div class="chips" id="device-chips"></div></div>
</div>
<div id="custom-range" class="subject-box" hidden>
<label class="field">From<input id="range-start" type="date"></label>
<label class="field">To<input id="range-end" type="date"></label>
<button id="apply-range" class="ghost" type="button">Apply</button>
</div>

<div id="search-status"></div>
<div class="tiles" id="stat-tiles"></div>

<div class="chart-card">
<div class="chart-head">
<div class="chip-group"><span class="label">Chart</span><div class="chips" id="chart-metrics"></div></div>
<div class="legend" id="chart-legend"></div>
</div>
<div class="chart-wrap"><div id="chart"></div><div id="chart-tip" class="tip" role="status" hidden></div></div>
</div>

<h3 class="rule">Worth writing about next<span class="meta">Queries and pages that qualify on measured numbers. The button sends one to Topics &amp; Research.</span></h3>
<div id="opportunity-list" class="rows" role="list"></div>
<nav class="pager" id="opportunities-pager" aria-label="Opportunity pages"></nav>

<h3 class="rule">What people searched for</h3>
<div class="table-scroll"><table class="data" id="queries-table"><thead><tr>
<th data-sort="query" aria-sort="none"><button type="button">Query</button></th>
<th class="n" data-sort="impressions" aria-sort="descending"><button type="button">Impressions</button></th>
<th class="n" data-sort="clicks" aria-sort="none"><button type="button">Clicks</button></th>
<th class="n" data-sort="ctr" aria-sort="none"><button type="button">CTR</button></th>
<th class="n" data-sort="position" aria-sort="none"><button type="button">Position</button></th>
</tr></thead><tbody></tbody></table></div>
<nav class="pager" id="queries-pager" aria-label="Query table pages"></nav>

<h3 class="rule">Which pages people chose</h3>
<div class="table-scroll"><table class="data" id="pages-table"><thead><tr>
<th data-sort="page" aria-sort="none"><button type="button">Page</button></th>
<th class="n" data-sort="impressions" aria-sort="descending"><button type="button">Impressions</button></th>
<th class="n" data-sort="clicks" aria-sort="none"><button type="button">Clicks</button></th>
<th class="n" data-sort="ctr" aria-sort="none"><button type="button">CTR</button></th>
<th class="n" data-sort="position" aria-sort="none"><button type="button">Position</button></th>
</tr></thead><tbody></tbody></table></div>
<nav class="pager" id="pages-pager" aria-label="Page table pages"></nav>

<p class="footnote" id="analytics-footnote"></p>

<h3 class="rule">Google Analytics 4<span class="meta">What visitors do after they reach the site.</span></h3>
<div id="ga4-panel"></div>

<h3 class="rule">Which website do you want to replicate?<span class="meta">Reads their sitemap free, then up to 10 of their pages, and scores each topic against our own Search Console position.</span></h3>
<div class="subject-box"><label class="field">Competitor website<input id="competitor" type="text" maxlength="253" placeholder="example.com"></label><button id="analyse-competitor" type="button">Analyse</button></div>
<p id="competitor-result" class="notice" hidden></p>
<div id="competitor-panel"></div>
<nav class="pager" id="competitor-pager" aria-label="Competitor finding pages"></nav>
</section>

<footer class="shortcuts"><span><kbd>1</kbd><kbd>2</kbd><kbd>3</kbd> tabs</span><span><kbd>/</kbd> search</span><span><kbd>j</kbd><kbd>k</kbd> move</span><span><kbd>Enter</kbd> open</span><span><kbd>Esc</kbd> close</span></footer>
<!-- Rendered server-side, never by the script: it identifies the bytes that were
     served. Visible at every width, including the phone. -->
<p class="build" id="build-stamp">@@CMO_BUILD_STAMP@@</p>
<div id="toast" class="toast" role="status" aria-live="polite" hidden></div>

<dialog id="detail" aria-labelledby="detail-title">
<div class="dialog-head"><div class="section-head"><div><p id="detail-id" class="eyebrow"></p><h2 id="detail-title"></h2></div><button id="close-detail" class="ghost small" type="button">Close</button></div></div>
<nav class="nested" aria-label="Blog detail"><button class="active" data-detail="read" type="button">Read</button><button data-detail="process" type="button">Process</button><button data-detail="impact" type="button">Impact</button><button data-detail="discussion" type="button">Discussion</button><button data-detail="files" type="button">Files</button></nav>
<div class="dialog-body"><div id="detail-body"></div></div>
</dialog>
</main>'''

MARKUP = BODY
