/**
 * RAPPsquare Local Configuration
 *
 * SETUP:
 * 1. Copy this file to config.local.js
 * 2. Replace the placeholder values with your actual endpoints
 * 3. config.local.js is gitignored - your secrets stay local
 *
 * GETTING YOUR AZURE FUNCTION URL:
 * 1. Deploy the RAPP Azure Function from openrapp repository
 * 2. Get your function URL: Azure Portal > Function App > Functions > Get Function URL
 * 3. Paste the full URL including the function key below
 */

window.RAPP_LOCAL_CONFIG = {
    // Your Azure Function endpoint (required for API features)
    // Format: https://YOUR-FUNCTION-APP.azurewebsites.net/api/businessinsightbot_function?code=YOUR_FUNCTION_KEY
    RAPP_API: 'https://YOUR-FUNCTION-APP.azurewebsites.net/api/businessinsightbot_function',

    // Optional: Override public data endpoints if using your own fork
    // RAPPBOOK_DATA: 'https://raw.githubusercontent.com/YOUR-USER/CommunityRAPP/main/rappbook/index.json',
    // RAPPZOO_TICK: 'https://raw.githubusercontent.com/YOUR-USER/CommunityRAPP/main/rappzoo/world/current_tick.json',
    // RAPPZOO_STATE: 'https://raw.githubusercontent.com/YOUR-USER/CommunityRAPP/main/rappzoo/world/state.json',
};
