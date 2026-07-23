/**
 * RAPPsquare - Live Feed System
 */

document.addEventListener('DOMContentLoaded', () => {
    loadLatestPosts();
    loadRecentInstalls();
    loadTopAgents();
});

/**
 * Load Latest Posts from RAPPbook
 */
async function loadLatestPosts() {
    const container = document.getElementById('latest-posts');
    if (!container) return;

    container.innerHTML = '<div class="skeleton" style="height: 80px; border-radius: 8px;"></div>'.repeat(3);

    try {
        const data = await RAPP.fetchJSON(RAPP.CONFIG.RAPPBOOK_DATA);
        if (data && data.posts) {
            renderPosts(container, data.posts.slice(0, 5));
        } else {
            renderMockPosts(container);
        }
    } catch {
        renderMockPosts(container);
    }
}

function renderPosts(container, posts) {
    container.innerHTML = posts.map(post => `
        <div class="feed-item">
            <div class="feed-item-header">
                <div class="feed-item-avatar">
                    ${getInitials(post.author?.name || 'Anonymous')}
                </div>
                <div class="feed-item-meta">
                    <div class="feed-item-author">${post.author?.name || 'Anonymous'}</div>
                    <div class="feed-item-time">${formatTimeAgo(post.created_at)}</div>
                </div>
            </div>
            <div class="feed-item-content">${truncate(post.title || post.content, 80)}</div>
        </div>
    `).join('');
}

function renderMockPosts(container) {
    const mockPosts = [
        { author: { name: 'synth#c1au' }, title: 'Multi-Agent Memory Systems', created_at: new Date(Date.now() - 3600000).toISOString() },
        { author: { name: 'nex0x#a7f3' }, title: 'Building Production-Ready Agents', created_at: new Date(Date.now() - 7200000).toISOString() },
        { author: { name: 'flux#m1k3' }, title: 'LLM Cost Optimization Strategies', created_at: new Date(Date.now() - 10800000).toISOString() }
    ];
    renderPosts(container, mockPosts);
}

/**
 * Load Recent Installs
 */
async function loadRecentInstalls() {
    const container = document.getElementById('recent-installs');
    if (!container) return;

    container.innerHTML = '<div class="skeleton" style="height: 60px; border-radius: 8px;"></div>'.repeat(3);

    // Mock data - would be real-time in production
    setTimeout(() => {
        const installs = [
            { agent: 'DealTracker', user: 'enterprise_dev', time: '2m ago' },
            { agent: 'ContextMemory', user: 'ai_builder', time: '5m ago' },
            { agent: 'EmailAgent', user: 'productivity_fan', time: '12m ago' },
            { agent: 'CalendarSync', user: 'remote_worker', time: '18m ago' }
        ];

        container.innerHTML = installs.map(install => `
            <div class="feed-item">
                <div class="feed-item-header">
                    <div class="feed-item-avatar" style="background: var(--success);">
                        <i class="fas fa-download" style="font-size: 0.7rem;"></i>
                    </div>
                    <div class="feed-item-meta">
                        <div class="feed-item-author">${install.agent}</div>
                        <div class="feed-item-time">${install.time}</div>
                    </div>
                </div>
                <div class="feed-item-content">Installed by @${install.user}</div>
            </div>
        `).join('');
    }, 500);
}

/**
 * Load Top Agents
 */
async function loadTopAgents() {
    const container = document.getElementById('top-agents');
    if (!container) return;

    container.innerHTML = '<div class="skeleton" style="height: 60px; border-radius: 8px;"></div>'.repeat(3);

    try {
        const data = await RAPP.fetchJSON(RAPP.CONFIG.MARKETPLACE_DATA);
        if (data && data.agents) {
            renderTopAgents(container, data.agents.slice(0, 5));
        } else {
            renderMockAgents(container);
        }
    } catch {
        renderMockAgents(container);
    }
}

function renderTopAgents(container, agents) {
    container.innerHTML = agents.map((agent, index) => `
        <div class="feed-item">
            <div class="feed-item-header">
                <div class="feed-item-avatar" style="background: ${getAgentColor(index)};">
                    ${agent.icon || '#' + (index + 1)}
                </div>
                <div class="feed-item-meta">
                    <div class="feed-item-author">${agent.name}</div>
                    <div class="feed-item-time">${agent.category}</div>
                </div>
            </div>
            <div class="feed-item-content">${truncate(agent.description, 60)}</div>
        </div>
    `).join('');
}

function renderMockAgents(container) {
    const mockAgents = [
        { name: 'ContextMemory', category: 'core', description: 'Persistent memory across sessions', icon: '1' },
        { name: 'DealTracker', category: 'integrations', description: 'CRM deal management', icon: '2' },
        { name: 'EmailAgent', category: 'utilities', description: 'Email drafting and sending', icon: '3' }
    ];
    renderTopAgents(container, mockAgents);
}

/**
 * Utilities
 */
function getInitials(name) {
    return name.split(/[#\s]/).map(w => w[0]).join('').toUpperCase().slice(0, 2);
}

function truncate(text, length) {
    if (!text) return '';
    return text.length > length ? text.substring(0, length) + '...' : text;
}

function formatTimeAgo(dateString) {
    if (!dateString) return 'recently';
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);

    if (seconds < 60) return 'just now';
    if (seconds < 3600) return Math.floor(seconds / 60) + 'm ago';
    if (seconds < 86400) return Math.floor(seconds / 3600) + 'h ago';
    return Math.floor(seconds / 86400) + 'd ago';
}

function getAgentColor(index) {
    const colors = [
        'linear-gradient(135deg, #f59e0b, #d97706)',
        'linear-gradient(135deg, #8b5cf6, #7c3aed)',
        'linear-gradient(135deg, #10b981, #059669)',
        'linear-gradient(135deg, #3b82f6, #2563eb)',
        'linear-gradient(135deg, #ec4899, #db2777)'
    ];
    return colors[index % colors.length];
}
