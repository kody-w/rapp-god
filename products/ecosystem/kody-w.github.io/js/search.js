// Client-side search using a pre-built JSON index
(function () {
  var overlay = document.getElementById('search-overlay');
  var input = document.getElementById('search-input');
  var resultsContainer = document.getElementById('search-results');
  var posts = [];

  function openSearch() {
    overlay.classList.add('active');
    input.focus();
    input.value = '';
    resultsContainer.textContent = '';
    if (posts.length === 0) loadIndex();
  }

  function closeSearch() {
    overlay.classList.remove('active');
  }

  function loadIndex() {
    fetch('/search.json')
      .then(function (r) { return r.json(); })
      .then(function (data) {
        posts = Array.isArray(data) ? data : [];
        if (input.value) search(input.value);
      })
      .catch(function () {
        showMessage('Could not load search index.');
      });
  }

  function showMessage(message) {
    var paragraph = document.createElement('p');
    paragraph.className = 'search-no-results';
    paragraph.textContent = message;
    resultsContainer.textContent = '';
    resultsContainer.appendChild(paragraph);
  }

  function textValue(value) {
    return value == null ? '' : String(value);
  }

  function safeLocalUrl(value) {
    return typeof value === 'string' && value.charAt(0) === '/' && value.charAt(1) !== '/'
      ? value
      : '/';
  }

  function renderMatches(matches) {
    var fragment = document.createDocumentFragment();

    matches.forEach(function (post) {
      var link = document.createElement('a');
      var title = document.createElement('span');

      link.className = 'search-result';
      link.href = safeLocalUrl(post.url);
      title.className = 'search-result-title';
      title.textContent = textValue(post.title);
      link.appendChild(title);

      if (post.date) {
        var meta = document.createElement('span');
        meta.className = 'search-result-date';
        meta.textContent = textValue(post.date);
        link.appendChild(meta);
      }

      fragment.appendChild(link);
    });

    resultsContainer.textContent = '';
    resultsContainer.appendChild(fragment);
  }

  function search(query) {
    if (!query) { resultsContainer.textContent = ''; return; }
    var terms = query.toLowerCase().split(/\s+/);
    var matches = posts.filter(function (post) {
      var haystack = [post.title, post.excerpt]
        .map(textValue)
        .join(' ')
        .toLowerCase();
      return terms.every(function (t) { return haystack.indexOf(t) !== -1; });
    }).slice(0, 10);

    if (matches.length === 0) {
      showMessage('No results found.');
      return;
    }
    renderMatches(matches);
  }

  // Keyboard shortcuts
  document.addEventListener('keydown', function (e) {
    // Cmd+K or Ctrl+K to open
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault();
      overlay.classList.contains('active') ? closeSearch() : openSearch();
    }
    // Esc to close
    if (e.key === 'Escape' && overlay.classList.contains('active')) {
      closeSearch();
    }
  });

  // Click outside to close
  overlay.addEventListener('click', function (e) {
    if (e.target === overlay) closeSearch();
  });

  if (input) {
    input.addEventListener('input', function () { search(this.value); });
  }
})();
