/**
 * Theme module
 * Owns the light/dark palette toggle. The active theme is persisted to
 * localStorage and applied to <html data-theme="..."> before the page
 * paints, so there is no flash of the wrong palette. The system
 * `prefers-color-scheme` setting is honoured until the user makes an
 * explicit choice.
 */

const themeModule = (() => {
    const STORAGE_KEY = 'notebook.theme';
    const VALID = new Set(['light', 'dark']);

    function systemPrefers() {
        return window.matchMedia &&
            window.matchMedia('(prefers-color-scheme: dark)').matches
            ? 'dark'
            : 'light';
    }

    function readStored() {
        try {
            const value = localStorage.getItem(STORAGE_KEY);
            return VALID.has(value) ? value : null;
        } catch (err) {
            return null;
        }
    }

    function writeStored(value) {
        try {
            localStorage.setItem(STORAGE_KEY, value);
        } catch (err) {
            // localStorage may be unavailable; fall through silently.
        }
    }

    function apply(theme) {
        const next = VALID.has(theme) ? theme : 'light';
        document.documentElement.setAttribute('data-theme', next);
    }

    function init() {
        const stored = readStored();
        apply(stored || systemPrefers());
    }

    function current() {
        return document.documentElement.getAttribute('data-theme') || 'light';
    }

    function set(theme) {
        if (!VALID.has(theme)) return;
        apply(theme);
        writeStored(theme);
        document.dispatchEvent(
            new CustomEvent('notebook:theme-changed', { detail: { theme } })
        );
    }

    function toggle() {
        set(current() === 'dark' ? 'light' : 'dark');
    }

    function clear() {
        try {
            localStorage.removeItem(STORAGE_KEY);
        } catch (err) {
            // ignore
        }
    }

    return { init, current, set, toggle, clear };
})();
