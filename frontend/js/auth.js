/**
 * Authentication Module
 * Handles login, signup, and logout flows
 */

const authModule = (() => {
    let currentUser = null;
    let isSignup = false;

    const init = async () => {
        const token = localStorage.getItem('token');
        if (token) {
            try {
                const response = await api.getMe();
                currentUser = response.data;
                showDashboard();
            } catch (error) {
                localStorage.removeItem('token');
                showAuth();
            }
        } else {
            showAuth();
        }
    };

    const showAuth = () => {
        document.getElementById('auth-container').style.display = 'block';
        document.getElementById('dashboard-container').style.display = 'none';
        renderAuthPage();
    };

    const showDashboard = () => {
        document.getElementById('auth-container').style.display = 'none';
        document.getElementById('dashboard-container').style.display = 'block';
        renderDashboard();
    };

    const renderAuthPage = () => {
        const container = document.getElementById('auth-container');
        container.innerHTML = `
            <div class="auth-container">
                <div class="auth-form">
                    <h1>📝 Notes App</h1>

                    <div id="auth-message" style="display: none;"></div>

                    <form id="auth-form">
                        <div id="signup-fields" style="display: none;">
                            <div class="form-group">
                                <label for="username">Username</label>
                                <input type="text" id="username" name="username" required>
                            </div>
                            <div class="form-group">
                                <label for="email">Email</label>
                                <input type="email" id="email" name="email" required>
                            </div>
                        </div>

                        <div id="login-fields">
                            <div class="form-group">
                                <label for="login-username">Username</label>
                                <input type="text" id="login-username" name="username" required>
                            </div>
                        </div>

                        <div class="form-group">
                            <label for="password">Password</label>
                            <input type="password" id="password" name="password" required>
                        </div>

                        <button type="submit" class="btn btn-primary w-full">
                            <span id="auth-button-text">Login</span>
                        </button>
                    </form>

                    <div class="auth-link">
                        <p id="auth-toggle-text">Don't have an account?
                            <a href="#" id="auth-toggle">Sign Up</a>
                        </p>
                    </div>
                </div>
            </div>
        `;

        const form = document.getElementById('auth-form');

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            await handleAuthSubmit();
        });

        updateAuthForm();
    };

    const updateAuthForm = () => {
        const signupFields = document.getElementById('signup-fields');
        const loginFields = document.getElementById('login-fields');

        const username = document.getElementById('username');
        const email = document.getElementById('email');
        const loginUsername = document.getElementById('login-username');

        signupFields.style.display = isSignup ? 'block' : 'none';
        loginFields.style.display = isSignup ? 'none' : 'block';

        username.required = isSignup;
        email.required = isSignup;
        loginUsername.required = !isSignup;

        document.getElementById('auth-button-text').textContent = isSignup ? 'Sign Up' : 'Login';
        document.getElementById('auth-toggle-text').innerHTML = isSignup
            ? 'Already have an account? <a href="#" id="auth-toggle">Login</a>'
            : `Don't have an account? <a href="#" id="auth-toggle">Sign Up</a>`;

        document.getElementById('auth-toggle').addEventListener('click', (e) => {
            e.preventDefault();
            isSignup = !isSignup;
            updateAuthForm();
        });
    };

    const handleAuthSubmit = async () => {
        const messageEl = document.getElementById('auth-message');
        messageEl.style.display = 'none';

        try {
            const response = isSignup
                ? await api.signup(
                    document.getElementById('username').value,
                    document.getElementById('email').value,
                    document.getElementById('password').value
                )
                : await api.login(
                    document.getElementById('login-username').value,
                    document.getElementById('password').value
                );

            api.setToken(response.data.token);
            currentUser = response.data.user;
            showDashboard();
        } catch (error) {
            messageEl.className = 'alert alert-error';

            if (error.details) {
                const messages = Object.entries(error.details)
                    .map(([field, msgs]) => `${field}: ${msgs.join(', ')}`)
                    .join(' | ');
                messageEl.textContent = messages;
            } else {
                messageEl.textContent = error.message;
            }

            messageEl.style.display = 'block';
        }
    };

    const logout = async () => {
        try {
            await api.logout();
            api.clearToken();
            currentUser = null;
            showAuth();
        } catch (error) {
            console.error('Logout error:', error);
            api.clearToken();
            currentUser = null;
            showAuth();
        }
    };

    const getCurrentUser = () => currentUser;

    return {
        init,
        logout,
        getCurrentUser,
        showDashboard,
    };
})();

const renderDashboard = () => {
    const container = document.getElementById('dashboard-container');
    const user = authModule.getCurrentUser();

    container.innerHTML = `
        <div class="dashboard">
            <div class="sidebar">
                <div class="sidebar-brand">📝 Notes</div>
                <ul class="sidebar-menu">
                    <li><a href="#" class="nav-link active" data-page="notes">My Notes</a></li>
                    <li><a href="#" class="nav-link" data-page="archived">Archived</a></li>
                    <li><a href="#" class="nav-link" onclick="authModule.logout(); return false;">Logout</a></li>
                </ul>
            </div>
            
            <div class="main-content">
                <div class="topbar">
                    <h2 class="topbar-title">My Notes</h2>
                    <div class="topbar-user">
                        <span>${user.username}</span>
                        <div class="user-avatar">${user.username[0].toUpperCase()}</div>
                    </div>
                </div>
                
                <div class="content">
                    <div id="page-content"></div>
                </div>
            </div>
        </div>
    `;

    // Setup navigation
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
            link.classList.add('active');
            const page = link.dataset.page;
            notesModule.loadPage(page);
        });
    });

    notesModule.loadPage('notes');
};
