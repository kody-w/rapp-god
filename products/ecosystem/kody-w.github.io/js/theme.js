// Dark mode toggle with localStorage persistence and system preference detection
(function () {
  var toggle = document.getElementById('theme-toggle');
  var icon = toggle ? toggle.querySelector('i') : null;
  var storedTheme = localStorage.getItem('theme');
  var systemDark = window.matchMedia('(prefers-color-scheme: dark)');

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    if (icon) {
      icon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    }
  }

  // Initialize: stored preference > system preference > light
  if (storedTheme) {
    applyTheme(storedTheme);
  } else if (systemDark.matches) {
    applyTheme('dark');
  }

  if (toggle) {
    toggle.addEventListener('click', function () {
      var current = document.documentElement.getAttribute('data-theme');
      var next = current === 'dark' ? 'light' : 'dark';
      localStorage.setItem('theme', next);
      applyTheme(next);
    });
  }

  // React to system preference changes (only if no stored preference)
  systemDark.addEventListener('change', function (e) {
    if (!localStorage.getItem('theme')) {
      applyTheme(e.matches ? 'dark' : 'light');
    }
  });
})();
