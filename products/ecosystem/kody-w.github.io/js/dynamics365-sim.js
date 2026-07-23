// Frame-by-frame Dynamics 365 simulation proof
(function () {
  var root = document.getElementById('d365-sim-app');
  var simulation = window.d365Simulation;
  var liveOverlay = simulation && simulation.liveOverlay ? simulation.liveOverlay : null;
  var runtime = simulation && simulation.runtime ? simulation.runtime : {};

  if (!root || !simulation || !simulation.frames || simulation.frames.length === 0) {
    return;
  }

  var currentIndex = 0;
  var isPlaying = false;
  var playbackTimer = null;
  var runtimeLabel = runtime.label || 'Runtime projection';
  var frameIntervalMs = Math.max(500, Number(runtime.frameIntervalMs || runtime.intervalMs || 1800));
  var endBehavior = runtime.endBehavior === 'loop' ? 'loop' : 'stop';
  var liveOverlayState = {
    status: liveOverlay ? 'loading' : 'disabled',
    data: null,
    error: '',
    sourceLabel: ''
  };

  function formatCurrency(value) {
    return '$' + Number(value || 0).toLocaleString('en-US');
  }

  function formatInterval(value) {
    return (Math.round((Number(value) / 100)) / 10).toLocaleString('en-US') + 's';
  }

  function escapeHtml(value) {
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function renderKeyValueCards(items) {
    return items.map(function (item) {
      return '<div class="d365-state-item">' +
        '<span class="d365-state-label">' + escapeHtml(item.label) + '</span>' +
        '<strong class="d365-state-value">' + escapeHtml(item.value) + '</strong>' +
      '</div>';
    }).join('');
  }

  function openPipeline(frame) {
    return (frame.entities.opportunities || []).reduce(function (total, opportunity) {
      return opportunity.stage.indexOf('Closed') === 0 ? total : total + Number(opportunity.amount || 0);
    }, 0);
  }

  function openCases(frame) {
    return (frame.entities.cases || []).filter(function (item) {
      return item.status !== 'Resolved' && item.status !== 'Closed';
    }).length;
  }

  function activeTasks(frame) {
    return (frame.entities.tasks || []).filter(function (item) {
      return item.status !== 'Done' && item.status !== 'Closed';
    }).length;
  }

  function activeAutomations(frame) {
    return (frame.automations || []).filter(function (item) {
      return item.status !== 'Complete';
    }).length;
  }

  function atRiskAccounts(frame) {
    return (frame.entities.accounts || []).filter(function (item) {
      return item.health === 'At Risk' || item.health === 'Watch';
    }).length;
  }

  function renderTable(title, rows, columns) {
    if (!rows || rows.length === 0) {
      return '<section class="d365-panel"><h3>' + title + '</h3><p class="d365-empty">No records in this frame.</p></section>';
    }

    var header = columns.map(function (column) {
      return '<th>' + escapeHtml(column.label) + '</th>';
    }).join('');

    var body = rows.map(function (row) {
      return '<tr>' + columns.map(function (column) {
        return '<td>' + escapeHtml(row[column.key]) + '</td>';
      }).join('') + '</tr>';
    }).join('');

    return '<section class="d365-panel">' +
      '<h3>' + title + '</h3>' +
      '<div class="d365-table-wrap">' +
      '<table class="d365-table"><thead><tr>' + header + '</tr></thead><tbody>' + body + '</tbody></table>' +
      '</div>' +
      '</section>';
  }

  function renderMachineStates(machine) {
    return renderKeyValueCards(Object.keys(machine).map(function (key) {
      return {
        label: key,
        value: machine[key]
      };
    }));
  }

  function renderTransitions(transitions) {
    return transitions.map(function (item) {
      return '<li>' +
        '<strong>' + escapeHtml(item.entity) + '</strong>' +
        '<span>' + escapeHtml(item.from) + ' -> ' + escapeHtml(item.to) + '</span>' +
        '<p>' + escapeHtml(item.note) + '</p>' +
      '</li>';
    }).join('');
  }

  function renderAutomations(items) {
    if (!items || items.length === 0) {
      return '<p class="d365-empty">No automations fired in this frame.</p>';
    }

    return '<ul class="d365-automation-list">' + items.map(function (item) {
      return '<li>' +
        '<strong>' + escapeHtml(item.id) + '</strong>' +
        '<span>' + escapeHtml(item.trigger) + '</span>' +
        '<p>' + escapeHtml(item.action) + '</p>' +
        '<em>' + escapeHtml(item.status) + '</em>' +
      '</li>';
    }).join('') + '</ul>';
  }

  function lineageModeClass(mode) {
    if (mode === 'reference') {
      return 'is-reference';
    }

    if (mode === 'derived') {
      return 'is-derived';
    }

    return 'is-embedded';
  }

  function renderLineage(items) {
    if (!items || items.length === 0) {
      return '<p class="d365-empty">This frame carries all required state directly.</p>';
    }

    return '<ul class="d365-lineage-list">' + items.map(function (item) {
      return '<li>' +
        '<div class="d365-lineage-head">' +
          '<strong>' + escapeHtml(item.name) + '</strong>' +
          '<span class="d365-lineage-chip ' + lineageModeClass(item.mode) + '">' + escapeHtml(item.mode) + '</span>' +
        '</div>' +
        '<span>' + escapeHtml(item.source) + '</span>' +
        '<p>' + escapeHtml(item.note) + '</p>' +
      '</li>';
    }).join('') + '</ul>';
  }

  function overlayFrame(frame) {
    if (!liveOverlayState.data || !liveOverlayState.data.frames) {
      return null;
    }

    return liveOverlayState.data.frames[frame.id] || null;
  }

  function activeSystemItems(frame) {
    var items = [
      { label: 'Frame source', value: 'Serialized frame ledger' },
      { label: 'Sales state', value: frame.machine.sales },
      { label: 'Service state', value: frame.machine.service },
      { label: 'Automation', value: frame.machine.automation }
    ];
    var overlayData = overlayFrame(frame);

    if (overlayData && overlayData.activeSystemData) {
      items = items.concat(overlayData.activeSystemData);
    }

    return items;
  }

  function hydrationFieldCount(frame) {
    var overlayData = overlayFrame(frame);

    if (!overlayData || !overlayData.activeSystemData) {
      return 0;
    }

    return overlayData.activeSystemData.length;
  }

  function overlayStatusMode(frame) {
    if (!liveOverlay) {
      return {
        label: 'Disabled',
        className: 'is-disabled',
        detail: 'No runtime overlay configured for this proof.'
      };
    }

    if (liveOverlayState.status === 'loading') {
      return {
        label: 'Hydrating',
        className: 'is-loading',
        detail: 'Trying GitHub raw first, then the checked-in cache.'
      };
    }

    if (liveOverlayState.status === 'error') {
      return {
        label: 'Offline',
        className: 'is-error',
        detail: liveOverlayState.error || 'Overlay fetch failed.'
      };
    }

    if (overlayFrame(frame) && liveOverlayState.sourceLabel === 'checked-in cache') {
      return {
        label: 'Cache fallback',
        className: 'is-cache',
        detail: 'Using the simulated running state preserved in the repo.'
      };
    }

    if (liveOverlayState.status === 'ready') {
      return {
        label: 'Live raw',
        className: 'is-live',
        detail: 'Using GitHub raw user data as the active overlay.'
      };
    }

    return {
      label: 'Ready',
      className: 'is-ready',
      detail: 'Overlay sources are configured and waiting to hydrate.'
    };
  }

  function renderHydrationSummary(frame) {
    var mode = overlayStatusMode(frame);

    return '<div class="d365-source-summary">' +
      '<div class="d365-source-row">' +
        '<span class="d365-source-chip ' + mode.className + '">' + escapeHtml(mode.label) + '</span>' +
        '<strong>Hydration source: ' + escapeHtml(liveOverlayState.sourceLabel || liveOverlay && liveOverlay.label || 'None') + '</strong>' +
      '</div>' +
      '<div class="d365-source-meta">' +
        '<span><strong>Overlay fields:</strong> ' + hydrationFieldCount(frame) + '</span>' +
        '<span><strong>Mode:</strong> ' + escapeHtml(mode.detail) + '</span>' +
      '</div>' +
    '</div>';
  }

  function renderOverlayStatus(frame) {
    var overlayData = overlayFrame(frame);

    if (!liveOverlay) {
      return '<p class="d365-active-note">No GitHub raw overlay is configured for this proof.</p>';
    }

    if (liveOverlayState.status === 'loading') {
      return '<p class="d365-active-note">Hydrating active system data from GitHub raw user data.</p>';
    }

    if (liveOverlayState.status === 'error') {
      return '<p class="d365-active-note is-error">GitHub raw hydration failed: ' + escapeHtml(liveOverlayState.error) + '</p>';
    }

    if (liveOverlayState.status === 'ready' && !overlayData) {
      return '<p class="d365-active-note">Overlay is synced from ' + escapeHtml(liveOverlayState.sourceLabel) + ', but this frame has no extra active-system fields cached yet.</p>';
    }

    if (liveOverlayState.status === 'ready') {
      return '<p class="d365-active-note">Active system data synced from ' + escapeHtml(liveOverlayState.sourceLabel) + ' / ' + escapeHtml(liveOverlayState.data.lastUpdated || 'unknown timestamp') + '.</p>';
    }

    return '<p class="d365-active-note">The checked-in cache simulates the current running state when external fetches are unavailable.</p>';
  }

  function renderActiveSystemData(frame) {
    return renderHydrationSummary(frame) +
      '<div class="d365-state-grid">' + renderKeyValueCards(activeSystemItems(frame)) + '</div>' +
      renderOverlayStatus(frame);
  }

  function overlaySources() {
    var sources = [];

    if (liveOverlay && liveOverlay.url) {
      sources.push({
        url: liveOverlay.url,
        label: liveOverlay.label || 'GitHub raw user data'
      });
    }

    if (liveOverlay && liveOverlay.cacheUrl) {
      sources.push({
        url: liveOverlay.cacheUrl,
        label: 'checked-in cache'
      });
    }

    return sources;
  }

  function loadOverlaySource(sources, index) {
    if (index >= sources.length) {
      liveOverlayState.status = 'error';
      liveOverlayState.error = 'No overlay sources responded.';
      renderFrame(currentIndex);
      return;
    }

    window.fetch(sources[index].url, { cache: 'no-store' })
      .then(function (response) {
        if (!response.ok) {
          throw new Error('HTTP ' + response.status);
        }

        return response.json();
      })
      .then(function (data) {
        liveOverlayState.status = 'ready';
        liveOverlayState.data = data;
        liveOverlayState.error = '';
        liveOverlayState.sourceLabel = sources[index].label;
        renderFrame(currentIndex);
      })
      .catch(function (error) {
        liveOverlayState.error = error && error.message ? error.message : 'Unknown fetch failure';
        loadOverlaySource(sources, index + 1);
      });
  }

  function loadLiveOverlay() {
    var sources = overlaySources();

    if (!liveOverlay || sources.length === 0) {
      return;
    }

    if (!window.fetch) {
      liveOverlayState.status = 'error';
      liveOverlayState.error = 'Fetch is unavailable in this browser.';
      renderFrame(currentIndex);
      return;
    }

    liveOverlayState.status = 'loading';
    liveOverlayState.error = '';
    renderFrame(currentIndex);
    loadOverlaySource(sources, 0);
  }

  function clearPlaybackTimer() {
    if (playbackTimer) {
      window.clearTimeout(playbackTimer);
      playbackTimer = null;
    }
  }

  function manualNavigate(nextIndex) {
    if (isPlaying) {
      isPlaying = false;
      clearPlaybackTimer();
    }

    currentIndex = Math.max(0, Math.min(simulation.frames.length - 1, nextIndex));
    renderFrame(currentIndex);
  }

  function stopPlayback(shouldRender) {
    isPlaying = false;
    clearPlaybackTimer();

    if (shouldRender) {
      renderFrame(currentIndex);
    }
  }

  function queueNextTick() {
    clearPlaybackTimer();

    if (!isPlaying) {
      return;
    }

    playbackTimer = window.setTimeout(function () {
      if (currentIndex >= simulation.frames.length - 1) {
        if (endBehavior === 'loop') {
          currentIndex = 0;
        } else {
          stopPlayback(true);
          return;
        }
      } else {
        currentIndex += 1;
      }

      renderFrame(currentIndex);
      queueNextTick();
    }, frameIntervalMs);
  }

  function startPlayback() {
    if (simulation.frames.length < 2) {
      return;
    }

    if (currentIndex >= simulation.frames.length - 1) {
      currentIndex = 0;
    }

    isPlaying = true;
    renderFrame(currentIndex);
    queueNextTick();
  }

  function renderFrame(index) {
    var frame = simulation.frames[index];
    var progress = index + 1;
    var runtimeStatusClass = isPlaying ? 'is-running' : 'is-paused';
    var runtimeStatusLabel = isPlaying ? 'Running' : 'Paused';
    var refreshControl = liveOverlay
      ? '<button class="d365-button" data-d365-refresh-live ' + (liveOverlayState.status === 'loading' ? 'disabled' : '') + '>' + (liveOverlayState.status === 'loading' ? 'Loading GitHub raw data...' : 'Refresh GitHub raw data') + '</button>'
      : '';

    root.innerHTML = '' +
      '<div class="d365-shell">' +
        '<section class="d365-hero">' +
          '<div class="d365-kicker">General state machine proof</div>' +
          '<h2>' + escapeHtml(frame.label) + '</h2>' +
          '<p class="d365-summary">' + escapeHtml(frame.summary) + '</p>' +
          '<div class="d365-runtime-row">' +
            '<div class="d365-runtime-pill ' + runtimeStatusClass + '">' + escapeHtml(runtimeLabel) + ': ' + runtimeStatusLabel + '</div>' +
            '<div class="d365-clock-detail">Static clock profile: ' + escapeHtml(formatInterval(frameIntervalMs)) + ' per frame / ' + escapeHtml(endBehavior) + ' at final frame</div>' +
          '</div>' +
          '<div class="d365-controls">' +
            '<div class="d365-control-cluster">' +
              '<button class="d365-button" data-d365-prev ' + (index === 0 ? 'disabled' : '') + '>Previous frame</button>' +
              '<button class="d365-button d365-button-primary" data-d365-play aria-pressed="' + (isPlaying ? 'true' : 'false') + '">' + (isPlaying ? 'Pause frame time' : 'Play in frame time') + '</button>' +
              refreshControl +
              '<button class="d365-button" data-d365-next ' + (index === simulation.frames.length - 1 ? 'disabled' : '') + '>Next frame</button>' +
            '</div>' +
            '<input class="d365-range" type="range" min="0" max="' + (simulation.frames.length - 1) + '" value="' + index + '" data-d365-range>' +
          '</div>' +
          '<div class="d365-meta">' +
            '<span><strong>Clock:</strong> ' + escapeHtml(frame.clock) + '</span>' +
            '<span><strong>Frame:</strong> ' + progress + ' / ' + simulation.frames.length + '</span>' +
          '</div>' +
          '<p class="d365-note">' + escapeHtml(frame.note) + '</p>' +
        '</section>' +

        '<section class="d365-stats">' +
          '<div class="d365-stat"><span>Open pipeline</span><strong>' + formatCurrency(openPipeline(frame)) + '</strong></div>' +
          '<div class="d365-stat"><span>Open cases</span><strong>' + openCases(frame) + '</strong></div>' +
          '<div class="d365-stat"><span>Active tasks</span><strong>' + activeTasks(frame) + '</strong></div>' +
          '<div class="d365-stat"><span>Live automations</span><strong>' + activeAutomations(frame) + '</strong></div>' +
          '<div class="d365-stat"><span>At-risk accounts</span><strong>' + atRiskAccounts(frame) + '</strong></div>' +
        '</section>' +

        '<div class="d365-grid">' +
          '<section class="d365-panel">' +
            '<h3>Machine state</h3>' +
            '<div class="d365-state-grid">' + renderMachineStates(frame.machine) + '</div>' +
          '</section>' +
          '<section class="d365-panel">' +
            '<h3>Active system data</h3>' +
            renderActiveSystemData(frame) +
          '</section>' +
          '<section class="d365-panel">' +
            '<h3>State lineage</h3>' +
            renderLineage(frame.lineage) +
          '</section>' +
        '</div>' +

        '<div class="d365-grid">' +
          '<section class="d365-panel">' +
            '<h3>State transition log</h3>' +
            '<ul class="d365-transition-list">' + renderTransitions(frame.transitions) + '</ul>' +
          '</section>' +
          '<section class="d365-panel"><h3>Automations</h3>' + renderAutomations(frame.automations) + '</section>' +
        '</div>' +

        '<div class="d365-grid">' +
          renderTable('Accounts', frame.entities.accounts, [
            { key: 'id', label: 'ID' },
            { key: 'name', label: 'Name' },
            { key: 'lifecycle', label: 'Lifecycle' },
            { key: 'owner', label: 'Owner' },
            { key: 'health', label: 'Health' }
          ]) +
          renderTable('Leads', frame.entities.leads, [
            { key: 'id', label: 'ID' },
            { key: 'company', label: 'Company' },
            { key: 'stage', label: 'Stage' },
            { key: 'score', label: 'Score' },
            { key: 'owner', label: 'Owner' }
          ]) +
        '</div>' +

        '<div class="d365-grid">' +
          renderTable('Opportunities', frame.entities.opportunities, [
            { key: 'id', label: 'ID' },
            { key: 'name', label: 'Name' },
            { key: 'stage', label: 'Stage' },
            { key: 'amount', label: 'Amount' },
            { key: 'next', label: 'Next step' }
          ]) +
          renderTable('Cases', frame.entities.cases, [
            { key: 'id', label: 'ID' },
            { key: 'title', label: 'Title' },
            { key: 'severity', label: 'Severity' },
            { key: 'status', label: 'Status' },
            { key: 'owner', label: 'Owner' }
          ]) +
        '</div>' +

        '<div class="d365-grid">' +
          renderTable('Tasks', frame.entities.tasks, [
            { key: 'id', label: 'ID' },
            { key: 'queue', label: 'Queue' },
            { key: 'title', label: 'Task' },
            { key: 'status', label: 'Status' }
          ]) +
        '</div>' +
      '</div>';

    bindControls();
  }

  function bindControls() {
    var prev = root.querySelector('[data-d365-prev]');
    var play = root.querySelector('[data-d365-play]');
    var refresh = root.querySelector('[data-d365-refresh-live]');
    var next = root.querySelector('[data-d365-next]');
    var range = root.querySelector('[data-d365-range]');

    if (prev) {
      prev.addEventListener('click', function () {
        manualNavigate(currentIndex - 1);
      });
    }

    if (play) {
      play.addEventListener('click', function () {
        if (isPlaying) {
          stopPlayback(true);
          return;
        }

        startPlayback();
      });
    }

    if (refresh) {
      refresh.addEventListener('click', function () {
        loadLiveOverlay();
      });
    }

    if (next) {
      next.addEventListener('click', function () {
        manualNavigate(currentIndex + 1);
      });
    }

    if (range) {
      range.addEventListener('input', function () {
        manualNavigate(Number(this.value));
      });
    }
  }

  renderFrame(currentIndex);
  loadLiveOverlay();

  if (runtime.autoPlay) {
    startPlayback();
  }
})();
