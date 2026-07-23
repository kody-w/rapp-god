// Learn with Kody — client-side example filter
(function () {
  const grid = document.getElementById('lwk-grid');
  const empty = document.getElementById('lwk-empty');
  const filterRoot = document.getElementById('lwk-filters');
  if (!grid || !filterRoot) return;

  const state = { status: 'all', category: 'all', difficulty: 'all' };

  function apply() {
    const cards = grid.querySelectorAll('.lwk-example-card');
    let visible = 0;
    cards.forEach((card) => {
      const cat = card.dataset.category || '';
      const diff = card.dataset.difficulty || '';
      const status = card.dataset.status || '';
      const matchCat = state.category === 'all' || cat === state.category;
      const matchDiff = state.difficulty === 'all' || diff === state.difficulty;
      const matchStatus = state.status === 'all' || status === state.status;
      const show = matchCat && matchDiff && matchStatus;
      card.style.display = show ? '' : 'none';
      if (show) visible++;
    });
    if (empty) empty.hidden = visible !== 0;
  }

  function syncButtons(type) {
    filterRoot
      .querySelectorAll(`.lwk-filter-btn[data-filter-type="${type}"]`)
      .forEach((button) => {
        const isCurrent = button.dataset.filterValue === state[type];
        button.classList.toggle('is-active', isCurrent);
        button.setAttribute('aria-pressed', isCurrent ? 'true' : 'false');
      });
  }

  filterRoot.addEventListener('click', (e) => {
    const btn = e.target.closest('.lwk-filter-btn');
    if (!btn) return;
    const type = btn.dataset.filterType;
    const value = btn.dataset.filterValue;
    if (!type || !value || !Object.prototype.hasOwnProperty.call(state, type)) return;
    state[type] = value;
    syncButtons(type);
    apply();
  });

  Object.keys(state).forEach(syncButtons);
  apply();
})();
