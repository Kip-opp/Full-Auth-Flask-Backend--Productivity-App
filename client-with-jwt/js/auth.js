/**
 * Authentication module
 *
 * Renders the minimalistic sign-in / sign-up screen, owns the auth
 * state, and wires the dark-mode toggle. The "Continue with Google"
 * option only appears when the backend has Google credentials
 * configured; the client never holds OAuth secrets.
 */

const authModule = (() => {
    let currentUser = null;
    let isSignup = false;
    let googleAvailable = false;

    const SVG_SUN = '<svg class="auth-theme-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/></svg>';
    const SVG_MOON = '<svg class="auth-theme-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';

    const SVG_GOOGLE = '<svg class="auth-google-icon" viewBox="0 0 24 24" aria-hidden="true">'
        + '<path fill="#EA4335" d="M12 10.2v3.9h5.5c-.2 1.3-1.6 3.9-5.5 3.9-3.3 0-6-2.7-6-6.1s2.7-6.1 6-6.1c1.9 0 3.2.8 3.9 1.5l2.6-2.5C16.7 3.1 14.6 2.2 12 2.2 6.5 2.2 2 6.7 2 12.2s4.5 10 10 10c5.8 0 9.6-4.1 9.6-9.8 0-.7-.1-1.2-.2-1.7H12z"/>'
        + '<path fill="#4285F4" d="M12 22.2c2.6 0 4.8-.9 6.4-2.3l-3-2.4c-.8.6-1.9 1-3.4 1-2.6 0-4.8-1.7-5.6-4.1H3.3v2.5C4.9 19.9 8.2 22.2 12 22.2z"/>'
        + '<path fill="#FBBC05" d="M6.4 14.3c-.2-.6-.3-1.2-.3-1.8s.1-1.2.3-1.8V8.2H3.3C2.5 9.6 2 11.3 2 12.5s.5 2.9 1.3 4.3l3.1-2.5z"/>'
        + '<path fill="#34A853" d="M12 5.9c1.5 0 2.5.6 3.1 1.2l2.3-2.3C15.9 3.4 14.1 2.5 12 2.5c-3.8 0-7.1 2.3-8.7 5.7l3.1 2.5C7.2 7.6 9.4 5.9 12 5.9z"/>'
        + '</svg>';

    const init = async () => {
        themeModule.init();
        await detectGoogle();
        const token = localStorage.getItem('token');
        if (token) {
            try {
                const response = await api.getMe();
                currentUser = response.data;
                showDashboard();
                return;
            } catch (error) {
                api.clearToken();
            }
        }
        await showGuest();
    };

    async function detectGoogle() {
        try {
            const response = await api.googleConfig();
            googleAvailable = Boolean(response.data && response.data.enabled);
        } catch (error) {
            googleAvailable = false;
        }
    }

    function showAuth() {
        document.getElementById('auth-container').style.display = 'block';
        document.getElementById('dashboard-container').style.display = 'none';
        renderAuthPage();
    }

    async function showGuest() {
        try {
            const response = await api.getDemoWorkspace();
            currentUser = null;
            showDashboard(null, { guest: true, demo: response.data });
        } catch (error) {
            showAuth();
        }
    }

    function showDashboard(user = currentUser, options = {}) {
        currentUser = user;
        document.getElementById('auth-container').style.display = 'none';
        document.getElementById('dashboard-container').style.display = 'block';
        workspaceModule.init(currentUser, options);
    }

    function renderAuthPage() {
        const container = document.getElementById('auth-container');
        container.innerHTML = `
            <div class="auth-shell">
                <aside class="auth-aside" aria-hidden="false">
                    <div>
                        <div class="auth-aside-brand">
                            <span class="auth-aside-mark">N</span>
                            <span>Notebook</span>
                        </div>
                    </div>
                    <div>
                        <h1 class="auth-aside-headline">A workspace for the sources you trust.</h1>
                        <p class="auth-aside-sub">Import articles, write notes, and ask grounded questions. Every answer is cited; every claim is auditable.</p>
                    </div>
                    <div class="auth-aside-footer">
                        <span><strong>Private by default.</strong> Your sources and notes are visible only to you.</span>
                    </div>
                </aside>
                <main class="auth-main">
                    <div class="auth-topbar">
                        <div class="auth-topbar-brand">
                            <span class="auth-topbar-brand-mark">N</span>
                            <span>Notebook</span>
                        </div>
                        <button class="auth-theme" type="button" id="auth-theme-btn" aria-label="Toggle theme">
                            <span id="auth-theme-icon">${themeModule.current() === 'dark' ? SVG_SUN : SVG_MOON}</span>
                            <span id="auth-theme-label">${themeModule.current() === 'dark' ? 'Light' : 'Dark'}</span>
                        </button>
                    </div>
                    <div class="auth-card-wrap">
                        <section class="auth-card" aria-labelledby="auth-title">
                            <header>
                                <h1 class="auth-title" id="auth-title">${isSignup ? 'Create your notebook' : 'Sign in to your notebook'}</h1>
                                <p class="auth-subtitle">${isSignup ? 'A private workspace is ready when you are.' : 'Welcome back. Continue where you left off.'}</p>
                            </header>
                            <div class="auth-message" id="auth-message" role="status" aria-live="polite"></div>
                            ${googleAvailable ? `
                                <button class="auth-button auth-google btn-full" type="button" id="auth-google-btn">
                                    ${SVG_GOOGLE}
                                    <span>Continue with Google</span>
                                </button>
                                <div class="auth-divider"><span>or with email</span></div>
                            ` : ''}
                            <form class="auth-form" id="auth-form" novalidate>
                                ${isSignup ? `
                                    <div class="auth-field">
                                        <label for="auth-username">Username</label>
                                        <input id="auth-username" name="username" type="text" required minlength="3" maxlength="80" autocomplete="username" placeholder="janedoe">
                                    </div>
                                ` : ''}
                                <div class="auth-field">
                                    <label for="auth-identifier">${isSignup ? 'Email' : 'Email or username'}</label>
                                    <input id="auth-identifier" name="${isSignup ? 'email' : 'identifier'}" type="${isSignup ? 'email' : 'text'}" required autocomplete="${isSignup ? 'email' : 'username'}" placeholder="${isSignup ? 'you@example.com' : 'you@example.com'}">
                                </div>
                                <div class="auth-field">
                                    <label for="auth-password">Password</label>
                                    <input id="auth-password" name="password" type="password" required minlength="8" autocomplete="${isSignup ? 'new-password' : 'current-password'}" placeholder="At least 8 characters">
                                </div>
                                <button class="auth-button auth-button-primary btn-full" type="submit" id="auth-submit-btn">
                                    ${isSignup ? 'Create account' : 'Sign in'}
                                </button>
                            </form>
                            <p class="auth-switch">
                                ${isSignup
                                    ? 'Already have an account? <a href="#" id="auth-toggle">Sign in</a>'
                                    : "Don't have an account? <a href=\"#\" id=\"auth-toggle\">Create one</a>"}
                            </p>
                        </section>
                    </div>
                    <div class="auth-foot">Notebook is private to you. No password recovery is offered in this build.</div>
                </main>
            </div>
        `;

        document.getElementById('auth-form').addEventListener('submit', handleSubmit);
        document.getElementById('auth-toggle').addEventListener('click', (e) => {
            e.preventDefault();
            isSignup = !isSignup;
            renderAuthPage();
        });
        document.getElementById('auth-theme-btn').addEventListener('click', onToggleTheme);
        const googleBtn = document.getElementById('auth-google-btn');
        if (googleBtn) {
            googleBtn.addEventListener('click', onGoogleSignIn);
        }
    }

    function onToggleTheme() {
        themeModule.toggle();
        const isDark = themeModule.current() === 'dark';
        document.getElementById('auth-theme-icon').innerHTML = isDark ? SVG_SUN : SVG_MOON;
        document.getElementById('auth-theme-label').textContent = isDark ? 'Light' : 'Dark';
    }

    async function handleSubmit(event) {
        event.preventDefault();
        const message = document.getElementById('auth-message');
        message.className = 'auth-message';
        message.textContent = '';
        const submit = document.getElementById('auth-submit-btn');
        submit.disabled = true;
        try {
            const identifier = document.getElementById('auth-identifier').value.trim();
            const password = document.getElementById('auth-password').value;
            let response;
            if (isSignup) {
                const username = document.getElementById('auth-username').value.trim();
                response = await api.signup(username, identifier, password);
            } else {
                response = await api.login(identifier, password);
            }
            api.setToken(response.data.token);
            currentUser = response.data.user;
            showDashboard();
        } catch (error) {
            showAuthError(message, error);
        } finally {
            submit.disabled = false;
        }
    }

    function showAuthError(messageEl, error) {
        messageEl.className = 'auth-message is-error';
        if (error.details) {
            const lines = Object.entries(error.details)
                .map(([field, msgs]) => `${field}: ${(msgs || []).join(', ')}`)
                .join(' · ');
            messageEl.textContent = lines || error.message || 'Authentication failed';
        } else {
            messageEl.textContent = error.message || 'Authentication failed';
        }
    }

    async function onGoogleSignIn() {
        const message = document.getElementById('auth-message');
        message.className = 'auth-message';
        message.textContent = '';
        try {
            const idToken = await requestGoogleIdToken();
            if (!idToken) return;
            const response = await api.loginWithGoogle(idToken);
            api.setToken(response.data.token);
            currentUser = response.data.user;
            showDashboard();
        } catch (error) {
            showAuthError(message, error);
        }
    }

    function requestGoogleIdToken() {
        return new Promise((resolve) => {
            try {
                const clientId = window.GOOGLE_CLIENT_ID;
                if (!clientId || !window.google || !google.accounts) {
                    messageError('Google sign-in is not configured on this deployment.');
                    resolve(null);
                    return;
                }
                const tokenClient = google.accounts.oauth2.initTokenClient({
                    client_id: clientId,
                    scope: 'openid email profile',
                    callback: (response) => {
                        if (response && response.access_token) {
                            resolve(response.access_token);
                        } else {
                            resolve(null);
                        }
                    },
                    error_callback: () => resolve(null),
                });
                tokenClient.requestAccessToken();
            } catch (err) {
                messageError('Google sign-in is not available in this browser.');
                resolve(null);
            }
        });
    }

    function messageError(text) {
        const message = document.getElementById('auth-message');
        if (message) {
            message.className = 'auth-message is-error';
            message.textContent = text;
        }
    }

    async function logout() {
        try {
            await api.logout();
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            api.clearToken();
            currentUser = null;
            if (typeof workspaceModule !== 'undefined' && workspaceModule.clearState) {
                workspaceModule.clearState();
            }
            showAuth();
        }
    }

    function requireAuth() {
        if (!currentUser) {
            showAuth();
            return false;
        }
        return true;
    }

    function confirmLogout() {
        const confirmed = window.confirm('Sign out of your notebook?');
        if (confirmed) logout();
    }

    function getCurrentUser() { return currentUser; }

    return { init, logout, confirmLogout, getCurrentUser, showDashboard, requireAuth };
})();

function renderDashboard() {
    const container = document.getElementById('dashboard-container');
    const user = authModule.getCurrentUser();

    container.innerHTML = `
        <div class="dashboard">
            <div class="sidebar">
                <div class="sidebar-brand">Notebook</div>
                <ul class="sidebar-menu">
                    <li><a href="#" class="nav-link active" data-page="notes">My Notes</a></li>
                    <li><a href="#" class="nav-link" data-page="archived">Archived</a></li>
                    <li><a href="#" class="nav-link" onclick="authModule.confirmLogout(); return false;">Sign out</a></li>
                </ul>
            </div>
            <div class="main-content">
                <div class="topbar">
                    <h2 class="topbar-title">My Notes</h2>
                    <div class="topbar-user">
                        <span>${user ? escapeHtml(user.username) : ''}</span>
                        <div class="user-avatar">${user ? escapeHtml(user.username[0].toUpperCase()) : '?'}</div>
                    </div>
                </div>
                <div class="content">
                    <div id="page-content"></div>
                </div>
            </div>
        </div>
    `;

    document.querySelectorAll('.nav-link').forEach((link) => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            document.querySelectorAll('.nav-link').forEach((l) => l.classList.remove('active'));
            link.classList.add('active');
            const page = link.dataset.page;
            notesModule.loadPage(page);
        });
    });

    notesModule.loadPage('notes');
}
