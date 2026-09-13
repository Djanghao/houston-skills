'use strict';

/* Tabs over iframes.
   A page is fetched only when its tab is first opened — packed pages run to
   several MB each, so an unopened tab must cost nothing. At most MAX_LIVE stay
   in memory; the least recently used is dropped. */

const MAX_LIVE = 3;
const S = { pages: [], at: null, frames: new Map(), lru: [] };

const $ = (id) => document.getElementById(id);
const el = (tag, cls, text) => {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text != null) n.textContent = text;
  return n;
};

function status(html) { $('status').innerHTML = html; $('status').classList.remove('gone'); }
function clearStatus() { $('status').classList.add('gone'); }

function evict() {
  while (S.lru.length > MAX_LIVE) {
    const id = S.lru.shift();
    if (id === S.at) { S.lru.push(id); break; }
    const f = S.frames.get(id);
    if (f) f.remove();
    S.frames.delete(id);
  }
}

function mark() {
  document.querySelectorAll('.tab').forEach((t) => {
    t.setAttribute('aria-selected', String(t.dataset.id === S.at));
    const dot = t.querySelector('.live');
    if (dot) dot.hidden = !S.frames.has(t.dataset.id);
  });
}

function show(id, { reload = false } = {}) {
  const page = S.pages.find((p) => p.id === id);
  if (!page) return;

  if (reload && S.frames.has(id)) { S.frames.get(id).remove(); S.frames.delete(id); }
  let frame = S.frames.get(id);
  const fresh = !frame;

  if (fresh) {
    frame = document.createElement('iframe');
    frame.title = page.title;
    frame.hidden = true;
    frame.src = `pages/${encodeURIComponent(page.file)}`;   // nothing loads before this
    frame.addEventListener('load', () => { if (S.at === id) clearStatus(); });
    frame.addEventListener('error', () => {
      if (S.at === id) status(`<div>无法加载 <code>pages/${page.file}</code></div>`);
    });
    S.frames.set(id, frame);
    $('stage').appendChild(frame);
  }

  S.frames.forEach((f, k) => { f.hidden = k !== id; });
  if (fresh) status('<div class="spin"></div><div>加载中…</div>');
  else clearStatus();

  const i = S.lru.indexOf(id);
  if (i >= 0) S.lru.splice(i, 1);
  S.lru.push(id);
  evict();
  mark();
}

function route() {
  const want = decodeURIComponent(location.hash.replace(/^#\/?/, ''));
  const ids = S.pages.map((p) => p.id);
  const id = ids.includes(want) ? want : ids[0];
  if (!id) return;

  S.at = id;
  const page = S.pages.find((p) => p.id === id);
  document.title = `${page.title} · Experiment Gallery`;
  const solo = $('solo');
  solo.href = `pages/${encodeURIComponent(page.file)}`;
  solo.hidden = false;

  show(id);
  const tab = document.querySelector(`.tab[data-id="${CSS.escape(id)}"]`);
  if (tab) tab.scrollIntoView({ block: 'nearest', inline: 'nearest' });
}

$('again').addEventListener('click', () => { if (S.at) show(S.at, { reload: true }); });

(async function boot() {
  let index;
  try {
    const r = await fetch('pages.json', { cache: 'no-cache' });
    if (!r.ok) throw new Error(String(r.status));
    index = await r.json();
  } catch (_) {
    status('<div>没有 <code>pages.json</code></div><div>跑一次 <code>publish.py</code></div>');
    return;
  }

  S.pages = index.pages || [];
  if (index.title) { $('site').textContent = index.title; document.title = index.title; }
  if (index.generated) $('stamp').textContent = index.generated;

  if (!S.pages.length) {
    status('<div>还没有任何对比页</div>'
         + '<div><code>publish.py spec.json --name my-comparison</code></div>');
    return;
  }

  const tabs = $('tabs');
  for (const p of S.pages) {
    const b = el('button', 'tab');
    b.setAttribute('role', 'tab');
    b.dataset.id = p.id;
    const dot = el('span', 'live');
    dot.hidden = true;
    b.append(dot, el('span', null, p.title));
    if (p.date) b.appendChild(el('span', 'when', p.date));
    b.addEventListener('click', () => { location.hash = `#/${p.id}`; });
    tabs.appendChild(b);
  }

  addEventListener('hashchange', route);
  route();
})();
