MARKUP = '''<main>
<header>
  <div><p class="eyebrow">iTarang / Technical Operations</p><h1>Technical Console</h1></div>
  <button id="logout" type="button">Sign out</button>
</header>
<section id="console">
  <nav aria-label="Technical console sections">
    <button class="active" data-tab="board" type="button">Board</button>
    <button data-tab="runtime" type="button">Runtime</button>
    <button data-tab="spend" type="button">Spend</button>
    <button data-tab="infrastructure" type="button">Infrastructure</button>
    <button data-tab="analytics" type="button">Analytics</button>
  </nav>
  <p id="notice" class="meta" role="status"></p>
  <section id="view" aria-live="polite"></section>
</section>
<dialog id="detail"><button id="close-detail" type="button">Close</button><div id="detail-body"></div></dialog>
</main>'''
