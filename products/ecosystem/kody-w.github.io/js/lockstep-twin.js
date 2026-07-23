// Lockstep digital twin proof
(function () {
  var root = document.getElementById('lockstep-twin-app');
  var simulation = window.lockstepTwinSimulation;
  var runtime = simulation && simulation.runtime ? simulation.runtime : {};

  if (!root || !simulation || !simulation.actions || simulation.actions.length === 0) {
    return;
  }

  var actions = simulation.actions.map(function (action) {
    action.diffs = diffStates(action.twinState, action.liveState);
    action.matches = action.diffs.length === 0;
    action.twinHash = hashState(action.twinState);
    action.liveHash = hashState(action.liveState);
    return action;
  });

  var executedCount = 0;
  var currentActionIndex = -1;
  var status = 'ready';
  var autorunTimer = null;
  var isRunningAll = false;
  var autoPlayDelayMs = Math.max(400, Number(runtime.autoPlayDelayMs || 900));

  function escapeHtml(value) {
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function stateSignature(state) {
    return Object.keys(state || {}).sort().map(function (key) {
      return key + '=' + String(state[key]);
    }).join('|');
  }

  function simpleHash(value) {
    var hash = 0;
    var index;

    for (index = 0; index < value.length; index += 1) {
      hash = ((hash << 5) - hash) + value.charCodeAt(index);
      hash |= 0;
    }

    return 'hx-' + Math.abs(hash).toString(16);
  }

  function hashState(state) {
    return simpleHash(stateSignature(state));
  }

  function diffStates(twinState, liveState) {
    var keys = {};
    var diffs = [];

    Object.keys(twinState || {}).forEach(function (key) {
      keys[key] = true;
    });

    Object.keys(liveState || {}).forEach(function (key) {
      keys[key] = true;
    });

    Object.keys(keys).sort().forEach(function (key) {
      var twinValue = twinState && twinState[key] != null ? String(twinState[key]) : 'n/a';
      var liveValue = liveState && liveState[key] != null ? String(liveState[key]) : 'n/a';

      if (twinValue !== liveValue) {
        diffs.push({
          field: key,
          twin: twinValue,
          live: liveValue
        });
      }
    });

    return diffs;
  }

  function clearAutorun() {
    if (autorunTimer) {
      window.clearTimeout(autorunTimer);
      autorunTimer = null;
    }

    isRunningAll = false;
  }

  function actionStatus(index) {
    if (index < executedCount) {
      if (status === 'drift' && index === currentActionIndex) {
        return 'drift';
      }

      return 'applied';
    }

    if (status === 'drift' && index > currentActionIndex) {
      return 'blocked';
    }

    if (index === executedCount) {
      return 'next';
    }

    return 'queued';
  }

  function currentAction() {
    if (currentActionIndex >= 0) {
      return actions[currentActionIndex];
    }

    return actions[0];
  }

  function renderBanner(action) {
    if (status === 'ready') {
      return '<div class="lockstep-banner is-ready">Ready. The next accepted action will be mirrored into both systems.</div>';
    }

    if (status === 'drift') {
      return '<div class="lockstep-banner is-drift">Drift detected on ' + escapeHtml(action.label) + '. Execution halted.</div>';
    }

    if (status === 'complete') {
      return '<div class="lockstep-banner is-complete">All actions landed without drift. The twin stayed valid.</div>';
    }

    if (isRunningAll) {
      return '<div class="lockstep-banner is-running">Auto-running until drift. Lockstep still holds through ' + escapeHtml(action.label) + '.</div>';
    }

    return '<div class="lockstep-banner is-healthy">Lockstep maintained through ' + escapeHtml(action.label) + '.</div>';
  }

  function renderRules() {
    return '<ul class="lockstep-rule-list">' + (simulation.rules || []).map(function (rule) {
      return '<li>' + escapeHtml(rule) + '</li>';
    }).join('') + '</ul>';
  }

  function renderRequest(action) {
    return '<div class="lockstep-request">' +
      '<div><span>Operation</span><strong>' + escapeHtml(action.request.operation) + '</strong></div>' +
      '<div><span>Target</span><strong>' + escapeHtml(action.request.target) + '</strong></div>' +
      '<div><span>Payload</span><strong>' + escapeHtml(action.request.payload) + '</strong></div>' +
      '<p>' + escapeHtml(action.note) + '</p>' +
    '</div>';
  }

  function renderInputs(action) {
    return '<ul class="lockstep-input-list">' + (action.inputs || []).map(function (item) {
      return '<li>' +
        '<div class="lockstep-input-head">' +
          '<strong>' + escapeHtml(item.name) + '</strong>' +
          '<span class="lockstep-input-chip is-' + escapeHtml(item.mode) + '">' + escapeHtml(item.mode) + '</span>' +
        '</div>' +
        '<span>' + escapeHtml(item.source) + '</span>' +
        '<p>' + escapeHtml(item.note) + '</p>' +
      '</li>';
    }).join('') + '</ul>';
  }

  function renderQueue() {
    return '<ol class="lockstep-queue">' + actions.map(function (action, index) {
      var state = actionStatus(index);
      var label = state.charAt(0).toUpperCase() + state.slice(1);

      return '<li class="lockstep-queue-item is-' + state + '">' +
        '<div class="lockstep-queue-head">' +
          '<strong>' + escapeHtml(action.label) + '</strong>' +
          '<span class="lockstep-chip is-' + state + '">' + escapeHtml(label) + '</span>' +
        '</div>' +
        '<span>' + escapeHtml(action.clock) + '</span>' +
        '<p>' + escapeHtml(action.note) + '</p>' +
      '</li>';
    }).join('') + '</ol>';
  }

  function renderStateComparison(action) {
    var keys = {};

    Object.keys(action.twinState || {}).forEach(function (key) {
      keys[key] = true;
    });

    Object.keys(action.liveState || {}).forEach(function (key) {
      keys[key] = true;
    });

    return '<div class="lockstep-table-wrap"><table class="lockstep-state-table">' +
      '<thead><tr><th>Field</th><th>Twin</th><th>Live</th></tr></thead>' +
      '<tbody>' + Object.keys(keys).sort().map(function (key) {
        var twinValue = action.twinState[key];
        var liveValue = action.liveState[key];
        var different = String(twinValue) !== String(liveValue);

        return '<tr class="lockstep-state-row ' + (different ? 'is-different' : 'is-matching') + '">' +
          '<td>' + escapeHtml(key) + '</td>' +
          '<td>' + escapeHtml(twinValue) + '</td>' +
          '<td>' + escapeHtml(liveValue) + '</td>' +
        '</tr>';
      }).join('') + '</tbody></table></div>';
  }

  function renderDiffs(action) {
    if (!action || action.diffs.length === 0) {
      return '<p class="lockstep-empty">No drift detected in the current action.</p>';
    }

    return '<ul class="lockstep-diff-list">' + action.diffs.map(function (diff) {
      return '<li><strong>' + escapeHtml(diff.field) + '</strong><span>Twin: ' + escapeHtml(diff.twin) + '</span><span>Live: ' + escapeHtml(diff.live) + '</span></li>';
    }).join('') + '</ul>';
  }

  function runNextAction() {
    var action;

    if (status === 'drift' || status === 'complete' || executedCount >= actions.length) {
      clearAutorun();
      return;
    }

    action = actions[executedCount];
    currentActionIndex = executedCount;
    executedCount += 1;

    if (action.matches) {
      status = executedCount >= actions.length ? 'complete' : 'healthy';
    } else {
      status = 'drift';
      clearAutorun();
    }

    render();
  }

  function scheduleAutorun() {
    clearTimeout(autorunTimer);

    if (!isRunningAll || status === 'drift' || status === 'complete') {
      return;
    }

    autorunTimer = window.setTimeout(function () {
      runNextAction();

      if (status !== 'drift' && status !== 'complete') {
        scheduleAutorun();
      }
    }, autoPlayDelayMs);
  }

  function runUntilDrift() {
    if (status === 'drift' || status === 'complete') {
      return;
    }

    isRunningAll = true;
    runNextAction();

    if (status !== 'drift' && status !== 'complete') {
      scheduleAutorun();
    }
  }

  function resetSimulation() {
    clearAutorun();
    executedCount = 0;
    currentActionIndex = -1;
    status = 'ready';
    render();
  }

  function bindControls() {
    var nextButton = root.querySelector('[data-lockstep-next]');
    var autoButton = root.querySelector('[data-lockstep-auto]');
    var resetButton = root.querySelector('[data-lockstep-reset]');

    if (nextButton) {
      nextButton.addEventListener('click', function () {
        clearAutorun();
        runNextAction();
      });
    }

    if (autoButton) {
      autoButton.addEventListener('click', function () {
        runUntilDrift();
      });
    }

    if (resetButton) {
      resetButton.addEventListener('click', function () {
        resetSimulation();
      });
    }
  }

  function render() {
    var action = currentAction();
    var executedLabel = executedCount + ' / ' + actions.length;
    var driftCount = action && action.diffs ? action.diffs.length : 0;
    var nextDisabled = status === 'drift' || status === 'complete' || executedCount >= actions.length;
    var autoDisabled = nextDisabled || isRunningAll;

    root.innerHTML = '' +
      '<div class="lockstep-shell">' +
        '<section class="lockstep-hero">' +
          '<div class="lockstep-kicker">Executable mirror proof</div>' +
          '<h2>' + escapeHtml(simulation.title) + '</h2>' +
          '<p class="lockstep-summary">' + escapeHtml(simulation.subtitle) + '</p>' +
          renderBanner(action) +
          '<div class="lockstep-controls">' +
            '<button class="lockstep-button lockstep-button-primary" data-lockstep-next ' + (nextDisabled ? 'disabled' : '') + '>Run next action</button>' +
            '<button class="lockstep-button" data-lockstep-auto ' + (autoDisabled ? 'disabled' : '') + '>' + (isRunningAll ? 'Running until drift...' : 'Run until drift') + '</button>' +
            '<button class="lockstep-button" data-lockstep-reset>Reset twin</button>' +
          '</div>' +
          '<div class="lockstep-meta">' +
            '<span><strong>Twin:</strong> ' + escapeHtml(simulation.targets.twin) + '</span>' +
            '<span><strong>Live:</strong> ' + escapeHtml(simulation.targets.live) + '</span>' +
            '<span><strong>Executed:</strong> ' + escapeHtml(executedLabel) + '</span>' +
          '</div>' +
        '</section>' +

        '<section class="lockstep-stats">' +
          '<div class="lockstep-stat"><span>Current twin hash</span><strong>' + escapeHtml(action ? action.twinHash : '--') + '</strong></div>' +
          '<div class="lockstep-stat"><span>Current live hash</span><strong>' + escapeHtml(action ? action.liveHash : '--') + '</strong></div>' +
          '<div class="lockstep-stat"><span>Drift fields</span><strong>' + driftCount + '</strong></div>' +
          '<div class="lockstep-stat"><span>Auto-run delay</span><strong>' + escapeHtml(String(autoPlayDelayMs)) + 'ms</strong></div>' +
        '</section>' +

        '<div class="lockstep-grid">' +
          '<section class="lockstep-panel">' +
            '<h3>Lockstep rules</h3>' +
            renderRules() +
          '</section>' +
          '<section class="lockstep-panel">' +
            '<h3>' + escapeHtml(currentActionIndex >= 0 ? 'Current action' : 'Next action') + '</h3>' +
            renderRequest(action) +
          '</section>' +
        '</div>' +

        '<div class="lockstep-grid">' +
          '<section class="lockstep-panel">' +
            '<h3>Action queue</h3>' +
            renderQueue() +
          '</section>' +
          '<section class="lockstep-panel">' +
            '<h3>Action inputs</h3>' +
            renderInputs(action) +
          '</section>' +
        '</div>' +

        '<div class="lockstep-grid">' +
          '<section class="lockstep-panel">' +
            '<h3>State comparison</h3>' +
            renderStateComparison(action) +
          '</section>' +
          '<section class="lockstep-panel">' +
            '<h3>Drift ledger</h3>' +
            renderDiffs(action) +
          '</section>' +
        '</div>' +
      '</div>';

    bindControls();
  }

  render();
})();
