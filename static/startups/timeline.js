(() => {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const root = document.documentElement;
  const snapshot = JSON.parse($('funding-data').textContent);
  const items = new Map(snapshot.items.map(item => [item.id, item]));
  const events = [...document.querySelectorAll('.event')];
  const mobile = matchMedia('(max-width: 767px)');
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
  const storage = {get(key, fallback) {try {return JSON.parse(localStorage.getItem(key)) ?? fallback;} catch {return fallback;}}, set(key, value) {try {localStorage.setItem(key, JSON.stringify(value));} catch {}}};
  const savedValue = storage.get('signal-startups-saved', []);
  const saved = new Set(Array.isArray(savedValue) ? savedValue.filter(id => typeof id === 'string') : []);
  let savedOnly = false;
  let stage = 'All';
  let layout = storage.get('signal-startups-layout', 'horizontal');
  let opener;
  const dateText = (value, options) => new Date(value + 'T12:00:00Z').toLocaleDateString('en-US', {...options, timeZone:'UTC'});
  const headline = item => `${item.company} raises ${item.amount} ${item.round}${item.investor ? ` led by ${item.investor}` : ''}`;
  function announce(text) {$('announcement').textContent = text;}
  function setTheme(theme) {
    root.dataset.theme = theme;
    $('theme').setAttribute('aria-pressed', String(theme === 'light'));
    $('theme').setAttribute('aria-label', `Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`);
    $('theme').querySelector('img').src = `static/startups/icons/${theme === 'dark' ? 'moon' : 'sun'}.svg`;
    storage.set('signal-startups-theme', theme);
  }
  setTheme(storage.get('signal-startups-theme', 'dark') === 'light' ? 'light' : 'dark');
  $('theme').addEventListener('click', () => setTheme(root.dataset.theme === 'dark' ? 'light' : 'dark'));
  function setLayout() {
    const vertical = mobile.matches || layout === 'vertical';
    root.dataset.layout = vertical ? 'vertical' : 'horizontal';
    $('timeline').classList.toggle('vertical', vertical);
    document.querySelectorAll('[data-layout][aria-label]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.layout === root.dataset.layout)));
    $('timeline').scrollTo({left:0,top:0});
  }
  setLayout();
  mobile.addEventListener('change', setLayout);
  document.querySelectorAll('.layout-switch button').forEach(button => button.addEventListener('click', () => {
    layout = button.dataset.layout;
    storage.set('signal-startups-layout', layout);
    setLayout();
  }));
  events.forEach(event => {
    const item = items.get(event.dataset.id);
    event.querySelector('time').textContent = dateText(item.date, {month:'short',day:'numeric'});
    const days = Math.max(0, Math.floor((Date.now() - Date.parse(item.date + 'T00:00:00Z')) / 86400000));
    event.querySelector('.age').textContent = days === 0 ? 'today' : `${days}d ago`;
  });
  function filter() {
    const query = $('search').value.trim().toLocaleLowerCase();
    let count = 0;
    const visible = [], hidden = [];
    events.forEach(event => {
      const item = items.get(event.dataset.id);
      const haystack = [item.company, item.investor, item.amount, item.round, item.description || ''].join(' ').toLocaleLowerCase();
      const match = (stage === 'All' || item.round === stage) && (!savedOnly || saved.has(item.id)) && query.split(/\s+/).every(word => haystack.includes(word));
      event.hidden = !match;
      (match ? visible : hidden).push(event);
      if (match) count++;
    });
    $('track').append(...visible, ...hidden);
    $('empty').hidden = count !== 0;
    $('count').textContent = `${count} ROUND${count === 1 ? '' : 'S'}`;
    $('filter-status').textContent = `${count} ${savedOnly ? 'saved ' : ''}round${count === 1 ? '' : 's'}${stage !== 'All' ? ` · ${stage}` : ''}`;
    $('clear-search').hidden = !query;
    $('intro').hidden = savedOnly || Boolean(query) || stage !== 'All';
    $('timeline').scrollTo({left:0,top:0});
    announce($('filter-status').textContent);
  }
  $('search').addEventListener('input', filter);
  $('clear-search').addEventListener('click', () => {$('search').value = ''; filter(); $('search').focus();});
  document.querySelectorAll('[data-stage]').forEach(button => button.addEventListener('click', () => {
    stage = button.dataset.stage;
    document.querySelectorAll('[data-stage]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.stage === stage)));
    filter();
  }));
  $('saved').addEventListener('click', () => {
    savedOnly = !savedOnly;
    $('saved').setAttribute('aria-pressed', String(savedOnly));
    $('saved').setAttribute('aria-label', savedOnly ? 'Show all rounds' : 'Show saved rounds');
    filter();
  });
  $('reset').addEventListener('click', () => {
    stage = 'All'; savedOnly = false; $('search').value = '';
    $('saved').setAttribute('aria-pressed', 'false'); $('saved').setAttribute('aria-label', 'Show saved rounds');
    document.querySelectorAll('[data-stage]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.stage === 'All')));
    filter();
  });
  function topics(open) {
    $('topics').hidden = !open;
    $('topics-toggle').setAttribute('aria-expanded', String(open));
    $('intro').hidden = open || savedOnly || Boolean($('search').value) || stage !== 'All';
  }
  $('topics-toggle').addEventListener('click', () => topics($('topics').hidden));
  document.addEventListener('pointerdown', event => {if (!event.target.closest('#topics, #topics-toggle')) topics(false);});
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && !$('topics').hidden) {topics(false); $('topics-toggle').focus();}
    if (event.key === '/' && !event.target.closest('input, textarea') && !$('detail').open && !$('about-dialog').open) {event.preventDefault(); $('search').focus();}
  });
  const safeLink = url => {try {return new URL(url).protocol === 'https:' ? url : '#';} catch {return '#';}};
  function el(tag, text, className) {const node = document.createElement(tag); if (text) node.textContent = text; if (className) node.className = className; return node;}
  function link(text, url) {const node = el('a', text); node.href = safeLink(url); node.target = '_blank'; node.rel = 'noopener noreferrer'; return node;}
  function showDetail(item, trigger) {
    opener = trigger;
    topics(false);
    const content = $('detail-content'); content.replaceChildren();
    if (item.image) {const image = el('img', '', 'detail-art'); image.src = item.image; image.alt = item.company; content.append(image);}
    const copy = el('div', '', 'detail-copy');
    copy.append(el('p', dateText(item.date,{month:'long',day:'numeric',year:'numeric'}), 'date'));
    const title = el('h2', headline(item)); title.id = 'detail-title'; copy.append(title);
    if (item.description) copy.append(el('p', item.description.split(' Find top early-stage startups')[0]));
    copy.append(el('p', `${item.company} raised ${item.amount} in ${item.round === 'Seed' || item.round === 'Pre-Seed' ? 'a ' + item.round.toLowerCase() : 'a ' + item.round} round${item.investor ? ` led by ${item.investor}` : ''}, according to Startups Gallery. Read the original announcement for the full details.`));
    const facts = el('dl');
    [['Round', item.round], ['Raised', item.amount], ['Lead investor', item.investor || 'Not listed'], ['Announced', dateText(item.date,{month:'short',day:'numeric',year:'numeric'})]].forEach(([label,value])=>{const group = el('div'); group.append(el('dt',label),el('dd',value));facts.append(group);});
    copy.append(facts);
    const actions = el('div','','detail-actions');
    const save = el('button',saved.has(item.id) ? 'Saved to your timeline' : 'Save round');
    save.id = 'save-round'; save.setAttribute('aria-pressed',String(saved.has(item.id)));
    save.addEventListener('click', () => {
      if (saved.has(item.id)) saved.delete(item.id); else saved.add(item.id);
      storage.set('signal-startups-saved', [...saved]);
      save.textContent = saved.has(item.id) ? 'Saved to your timeline' : 'Save round';
      save.setAttribute('aria-pressed',String(saved.has(item.id)));
      announce(saved.has(item.id) ? 'Round saved on this device' : 'Round removed from saved');
    });
    actions.append(link('Read announcement',item.source_url), link('Company profile',item.company_url),save);
    copy.append(actions,el('p',`Funding data and company artwork: Startups Gallery · Source checked ${snapshot.fetched_at.slice(0,10)}`,'credits'));
    content.append(copy); $('detail').showModal(); $('detail').scrollTop=0; $('close-detail').focus();
  }
  $('track').addEventListener('click', event => {
    const card = event.target.closest('.card');
    if (!card || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault(); showDetail(items.get(card.dataset.id),card);
  });
  $('close-detail').addEventListener('click', () => $('detail').close());
  $('detail').addEventListener('close', () => {if (savedOnly) filter(); if (opener && !opener.closest('[hidden]')) opener.focus(); else $('saved').focus();});
  function about() {topics(false);$('about-dialog').showModal();$('close-about').focus();}
  $('intro').addEventListener('click', about); $('about').addEventListener('click',about);
  $('close-about').addEventListener('click', () => $('about-dialog').close());
  for (const dialog of document.querySelectorAll('dialog')) dialog.addEventListener('click',event=>{if(event.target===dialog){const r=dialog.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)dialog.close();}});
  $('timeline').addEventListener('wheel', event => {
    if (root.dataset.layout !== 'horizontal' || Math.abs(event.deltaX) > Math.abs(event.deltaY) || event.ctrlKey) return;
    event.preventDefault(); $('timeline').scrollLeft += event.deltaY;
  }, {passive:false});
  $('timeline').addEventListener('keydown', event => {
    if (root.dataset.layout !== 'horizontal' || !['ArrowRight','ArrowLeft','Home','End'].includes(event.key)) return;
    event.preventDefault();
    if (event.key==='Home'||event.key==='End') $('timeline').scrollTo({left:event.key==='Home'?0:$('timeline').scrollWidth,behavior:reducedMotion.matches?'instant':'smooth'});
    else $('timeline').scrollBy({left:event.key==='ArrowRight'?360:-360,behavior:reducedMotion.matches?'instant':'smooth'});
  });
  filter();
})();
