/**
 * RAPPsquare - Main JavaScript
 *
 * Configuration is loaded from config.js (defaults) and config.local.js (user overrides)
 * See config.local.example.js for setup instructions
 */

// Get configuration (loaded by config.js)
const CONFIG = window.RAPP_CONFIG || {
    // Fallback defaults if config.js not loaded
    RAPP_API: null,
    RAPPBOOK_DATA: 'https://raw.githubusercontent.com/kody-w/CommunityRAPP/main/rappbook/index.json',
    RAPPZOO_TICK: 'https://raw.githubusercontent.com/kody-w/CommunityRAPP/main/rappzoo/world/current_tick.json',
    RAPPZOO_STATE: 'https://raw.githubusercontent.com/kody-w/CommunityRAPP/main/rappzoo/world/state.json',
    MARKETPLACE_DATA: 'https://raw.githubusercontent.com/kody-w/rapp-agent-marketplace/main/manifest.json',
    THEME_KEY: 'rapp-theme',
    USER_KEY: 'rapp-user-guid'
};

// State
let currentTheme = localStorage.getItem(CONFIG.THEME_KEY) || 'dark';
let userGuid = localStorage.getItem(CONFIG.USER_KEY) || generateGuid();

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initNavigation();
    initPlatformCards();
    animateStats();
});

/**
 * Theme Management
 */
function initTheme() {
    document.documentElement.setAttribute('data-theme', currentTheme);
    updateThemeIcon();

    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
}

function toggleTheme() {
    currentTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', currentTheme);
    localStorage.setItem(CONFIG.THEME_KEY, currentTheme);
    updateThemeIcon();
}

function updateThemeIcon() {
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        const icon = themeToggle.querySelector('i');
        icon.className = currentTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    }
}

/**
 * Navigation
 */
function initNavigation() {
    // Highlight current page
    const currentPath = window.location.pathname;
    document.querySelectorAll('.nav-link').forEach(link => {
        if (link.getAttribute('href') === currentPath ||
            (currentPath === '/' && link.getAttribute('data-page') === 'home')) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });

    // Connect button
    const connectBtn = document.getElementById('connect-btn');
    if (connectBtn) {
        connectBtn.addEventListener('click', handleConnect);
    }
}

function handleConnect() {
    // Check if already connected
    const storedUser = localStorage.getItem('rapp-github-user');
    if (storedUser) {
        const user = JSON.parse(storedUser);
        showUserMenu(user);
        return;
    }
    
    // Show connection modal
    showConnectionModal();
}

function showConnectionModal() {
    // Create modal
    const modal = document.createElement('div');
    modal.id = 'connect-modal';
    modal.innerHTML = `
        <div class="modal-overlay" onclick="closeConnectionModal()"></div>
        <div class="modal-content">
            <div class="modal-header">
                <h2><i class="fab fa-github"></i> Connect to RAPPverse</h2>
                <button class="modal-close" onclick="closeConnectionModal()"><i class="fas fa-times"></i></button>
            </div>
            <div class="modal-body">
                <p>Connect your GitHub account to:</p>
                <ul class="connect-benefits">
                    <li><i class="fas fa-check" style="color: #10B981;"></i> Post to the federated feed</li>
                    <li><i class="fas fa-check" style="color: #10B981;"></i> Collect and trade cards</li>
                    <li><i class="fas fa-check" style="color: #10B981;"></i> Battle other agents</li>
                    <li><i class="fas fa-check" style="color: #10B981;"></i> Create your own dimension</li>
                </ul>
                <button class="btn-github" onclick="startGitHubAuth()">
                    <i class="fab fa-github"></i> Connect with GitHub
                </button>
                <p class="connect-note">No private data is stored. Authentication via GitHub OAuth.</p>
            </div>
        </div>
    `;
    
    // Add styles
    const style = document.createElement('style');
    style.textContent = `
        #connect-modal { position: fixed; top: 0; left: 0; right: 0; bottom: 0; z-index: 10000; display: flex; align-items: center; justify-content: center; }
        .modal-overlay { position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.8); }
        .modal-content { position: relative; background: var(--bg-secondary, #111); border: 1px solid var(--border-color, #333); border-radius: 16px; max-width: 400px; width: 90%; padding: 2rem; }
        .modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; }
        .modal-header h2 { margin: 0; font-size: 1.25rem; display: flex; align-items: center; gap: 0.5rem; }
        .modal-close { background: none; border: none; color: var(--text-secondary, #999); font-size: 1.25rem; cursor: pointer; }
        .connect-benefits { list-style: none; padding: 0; margin: 1.5rem 0; }
        .connect-benefits li { display: flex; align-items: center; gap: 0.75rem; padding: 0.5rem 0; color: var(--text-secondary, #ccc); }
        .btn-github { width: 100%; padding: 1rem; background: #24292e; color: white; border: none; border-radius: 8px; font-size: 1rem; font-weight: 600; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 0.5rem; transition: background 0.3s; }
        .btn-github:hover { background: #2f363d; }
        .connect-note { text-align: center; font-size: 0.75rem; color: var(--text-muted, #666); margin-top: 1rem; }
    `;
    
    document.head.appendChild(style);
    document.body.appendChild(modal);
}

function closeConnectionModal() {
    const modal = document.getElementById('connect-modal');
    if (modal) modal.remove();
}

function startGitHubAuth() {
    // GitHub OAuth client ID for RAPPverse
    const clientId = 'Ov23liCJ0pLcKoM1r0el';
    const redirectUri = encodeURIComponent(window.location.origin + '/callback.html');
    const scope = 'read:user';
    const state = generateGuid();
    
    localStorage.setItem('oauth-state', state);
    
    const authUrl = `https://github.com/login/oauth/authorize?client_id=${clientId}&redirect_uri=${redirectUri}&scope=${scope}&state=${state}`;
    
    // Open in popup or redirect
    const width = 600, height = 700;
    const left = (screen.width - width) / 2;
    const top = (screen.height - height) / 2;
    
    const popup = window.open(authUrl, 'GitHub Auth', `width=${width},height=${height},left=${left},top=${top}`);
    
    if (!popup) {
        // Fallback to redirect
        window.location.href = authUrl;
    } else {
        // Listen for callback
        const checkPopup = setInterval(() => {
            try {
                if (popup.closed) {
                    clearInterval(checkPopup);
                    // Check if auth succeeded
                    const user = localStorage.getItem('rapp-github-user');
                    if (user) {
                        closeConnectionModal();
                        showToast('Connected! Welcome to the RAPPverse.', 'success');
                        updateConnectButton(JSON.parse(user));
                    }
                }
            } catch (e) {}
        }, 500);
    }
}

function showUserMenu(user) {
    showToast(`Connected as ${user.login}`, 'success');
}

function updateConnectButton(user) {
    const connectBtn = document.getElementById('connect-btn');
    if (connectBtn && user) {
        connectBtn.innerHTML = `<img src="${user.avatar_url}" style="width: 24px; height: 24px; border-radius: 50%;"> ${user.login}`;
        connectBtn.onclick = () => showUserMenu(user);
    }
}

/**
 * Platform Cards Interaction
 */
function initPlatformCards() {
    document.querySelectorAll('.platform-card').forEach(card => {
        card.addEventListener('click', () => {
            const platform = card.dataset.platform;
            navigateToPlatform(platform);
        });
    });
}

function navigateToPlatform(platform) {
    const routes = {
        'marketplace': 'pages/marketplace.html',
        'rappbook': 'pages/rappbook.html',
        'cards': 'pages/cards.html',
        'rappverse': 'pages/rappverse.html',
        'core': 'pages/api-docs.html'
    };

    if (routes[platform]) {
        window.location.href = routes[platform];
    }
}

/**
 * Stats Animation
 */
function animateStats() {
    const stats = {
        'agent-count': 47,
        'user-count': 1247,
        'deploy-count': 5832
    };

    Object.entries(stats).forEach(([id, target]) => {
        const el = document.getElementById(id);
        if (el) {
            animateNumber(el, target);
        }
    });
}

function animateNumber(el, target) {
    const duration = 2000;
    const start = 0;
    const startTime = performance.now();

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = easeOutQuart(progress);
        const current = Math.floor(start + (target - start) * eased);

        el.textContent = formatNumber(current);

        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }

    requestAnimationFrame(update);
}

function easeOutQuart(x) {
    return 1 - Math.pow(1 - x, 4);
}

function formatNumber(num) {
    if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

/**
 * Utility Functions
 */
function generateGuid() {
    const guid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
    localStorage.setItem(CONFIG.USER_KEY, guid);
    return guid;
}

function showToast(message, type = 'info') {
    // Remove existing toasts
    document.querySelectorAll('.toast').forEach(t => t.remove());

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <i class="fas fa-${getToastIcon(type)}"></i>
        <span>${message}</span>
    `;

    // Style the toast
    Object.assign(toast.style, {
        position: 'fixed',
        bottom: '20px',
        right: '20px',
        padding: '12px 20px',
        background: type === 'error' ? 'var(--error)' :
                   type === 'success' ? 'var(--success)' :
                   type === 'warning' ? 'var(--warning)' : 'var(--info)',
        color: 'white',
        borderRadius: 'var(--border-radius-sm)',
        display: 'flex',
        alignItems: 'center',
        gap: '10px',
        zIndex: '9999',
        boxShadow: 'var(--shadow-lg)',
        animation: 'fadeIn 0.3s ease'
    });

    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

function getToastIcon(type) {
    const icons = {
        'success': 'check-circle',
        'error': 'exclamation-circle',
        'warning': 'exclamation-triangle',
        'info': 'info-circle'
    };
    return icons[type] || icons.info;
}

/**
 * API Helpers
 */
async function fetchJSON(url) {
    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error('Fetch error:', error);
        return null;
    }
}

async function callRAPP(input, history = []) {
    try {
        const response = await fetch(CONFIG.RAPP_API, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_input: input,
                conversation_history: history,
                user_guid: userGuid
            })
        });

        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error('RAPP API error:', error);
        return null;
    }
}

// Export for use in other modules
window.RAPP = {
    CONFIG,
    showToast,
    fetchJSON,
    callRAPP,
    userGuid
};
