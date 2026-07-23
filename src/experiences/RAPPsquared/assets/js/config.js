/**
 * RAPPsquare Configuration
 *
 * This file provides default configuration. To override with your own values:
 * 1. Copy config.local.example.js to config.local.js
 * 2. Edit config.local.js with your values
 * 3. config.local.js is gitignored and will not be committed
 *
 * For GitHub Pages deployment, the defaults use public CommunityRAPP endpoints.
 * For private API access, you must configure your own Azure Function endpoint.
 */

// Default configuration (public endpoints only)
const DEFAULT_CONFIG = {
    // RAPP API - Set your own Azure Function endpoint
    // Leave null to disable API features that require authentication
    RAPP_API: null,

    // Public data endpoints (CommunityRAPP - no auth required)
    RAPPBOOK_DATA: 'https://raw.githubusercontent.com/kody-w/CommunityRAPP/main/rappbook/index.json',
    RAPPZOO_TICK: 'https://raw.githubusercontent.com/kody-w/CommunityRAPP/main/rappzoo/world/current_tick.json',
    RAPPZOO_STATE: 'https://raw.githubusercontent.com/kody-w/CommunityRAPP/main/rappzoo/world/state.json',
    MARKETPLACE_DATA: 'https://raw.githubusercontent.com/kody-w/rapp-agent-marketplace/main/manifest.json',

    // Local storage keys (safe to keep as defaults)
    THEME_KEY: 'rapp-theme',
    USER_KEY: 'rapp-user-guid'
};

// Merge with user overrides from config.local.js (if loaded)
const CONFIG = {
    ...DEFAULT_CONFIG,
    ...(window.RAPP_LOCAL_CONFIG || {})
};

// Validate required config
if (!CONFIG.RAPP_API) {
    console.warn('⚠️ RAPP_API not configured. API features disabled. See config.local.example.js');
}

// Export for use
window.RAPP_CONFIG = CONFIG;
