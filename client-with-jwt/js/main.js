/**
 * Main Application Entry Point
 * Initialises the theme as early as possible, then the auth module.
 */
document.addEventListener('DOMContentLoaded', () => {
    themeModule.init();
    authModule.init();
});
