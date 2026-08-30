/**
 * Workspace module
 * Renders the workspace shell, navigation, and the workspace pages
 * (Overview, Sources, Notebook notes, Ask notebook, Slides, Mind map,
 * Data tables, Quizzes, Summary, and the legacy Notes / Archived areas).
 *
 * The browser never holds provider keys or model prompts; it calls the
 * backend API and polls jobs.
 */

const workspaceModule = (() => {
    const state = {
        workspaceId: null,
        workspaceName: '',
        sources: [],
        notes: [],
        queries: [],
        artifacts: [],
        currentPage: 'overview',
        activeQuery: null,
        jobPollers: new Set(),
    };

    const PAGES = {
        overview: { label: 'Overview', icon: '◐', render: renderOverview },
        sources: { label: 'Sources', icon: '⌘', render: renderSources },
        'notebook-notes': { label: 'Notebook notes', icon: '✎', render: renderNotebookNotes },
        ask: { label: 'Ask notebook', icon: '?', render: renderAskNotebook },
        slides: { label: 'Slides', icon: '▤', render: (ws) => renderArtifactPage(ws, 'slides', 'Slides') },
        mindmap: { label: 'Mind map', icon: '◇', render: (ws) => renderArtifactPage(ws, 'mindmap', 'Mind map') },
        table: { label: 'Data table', icon: '▦', render: (ws) => renderArtifactPage(ws, 'table', 'Data table') },
        quiz: { label: 'Quiz', icon: '◊', render: (ws) => renderArtifactPage(ws, 'quiz', 'Quiz') },
        summary: { label: 'Summary', icon: '☰', render: (ws) => renderArtifactPage(ws, 'summary', 'Summary') },
        notes: { label: 'Notes', icon: '✎', render: renderLegacyNotes },
        archived: { label: 'Archived', icon: '◌', render: renderLegacyArchived },
    };

    function mount() {
        return `
            <div class="ws-shell">
                <aside class="ws-sidebar" id="ws-sidebar">
                    <div class="ws-brand">
                        <span class="ws-brand-mark">◍</span>
                        <span class="ws-brand-text">Notebook</span>
                    </div>
                    <div class="ws-workspace-switcher">
                        <label for="ws-switcher">Workspace</label>
                        <select id="ws-switcher" aria-label="Switch workspace"></select>
                        <button class="btn btn-ghost btn-sm" id="ws-new-btn" type="button">+ New</button>
                    </div>
                    <nav class="ws-nav" aria-label="Workspace navigation">
                        <div class="ws-nav-group">
                            <div class="ws-nav-heading">Workspace</div>
                            ${navItem('overview')}
                            ${navItem('sources')}
                            ${navItem('notebook-notes')}
                            ${navItem('ask')}
                        </div>
                        <div class="ws-nav-group">
                            <div class="ws-nav-heading">Generate</div>
                            ${navItem('slides')}
                            ${navItem('mindmap')}
                            ${navItem('table')}
                            ${navItem('quiz')}
                            ${navItem('summary')}
                        </div>
                        <div class="ws-nav-group">
                            <div class="ws-nav-heading">Legacy</div>
                            ${navItem('notes')}
                            ${navItem('archived')}
                        </div>
                    </nav>
                    <div class="ws-account">
                        <div class="ws-account-name" id="ws-account-name"></div>
                        <button class="btn btn-ghost btn-sm" type="button" id="ws-logout">Sign out</button>
                    </div>
                </aside>
                <div class="ws-backdrop" id="ws-backdrop" hidden></div>
                <main class="ws-main">
                    <header class="ws-topbar">
                        <button class="ws-nav-toggle" id="ws-nav-toggle" type="button" aria-label="Toggle navigation">☰</button>
                        <nav class="ws-breadcrumb" aria-label="Breadcrumb">
                            <span class="ws-breadcrumb-item" id="ws-bc-workspace">Notebook</span>
                            <span class="ws-breadcrumb-sep">›</span>
                            <span class="ws-breadcrumb-item" id="ws-bc-page">Overview</span>
                        </nav>
                        <div class="ws-topbar-actions">
                            <button class="btn btn-primary" id="ws-ask-btn" type="button">Ask notebook</button>
                        </div>
                    </header>
                    <section class="ws-content" id="ws-content" tabindex="-1"></section>
                </main>
            </div>
        `;
    }

    function navItem(key) {
        const p = PAGES[key];
        return `<a href="#" class="ws-nav-item" data-page="${key}">
            <span class="ws-nav-icon" aria-hidden="true">${p.icon}</span>
            <span class="ws-nav-label">${p.label}</span>
        </a>`;
    }

    async function init(currentUser) {
        const container = document.getElementById('dashboard-container');
        container.innerHTML = mount();

        document.getElementById('ws-account-name').textContent =
            currentUser ? currentUser.username : '';

        await loadWorkspaces();

        document.getElementById('ws-new-btn').addEventListener('click', onNewWorkspace);
        document.getElementById('ws-logout').addEventListener('click', () => authModule.confirmLogout());
        document.getElementById('ws-ask-btn').addEventListener('click', () => navigate('ask'));
        document.getElementById('ws-nav-toggle').addEventListener('click', toggleSidebar);
        document.getElementById('ws-backdrop').addEventListener('click', closeSidebar);

        document.querySelectorAll('.ws-nav-item').forEach((el) => {
            el.addEventListener('click', (e) => {
                e.preventDefault();
                navigate(el.dataset.page);
                if (window.innerWidth < 900) closeSidebar();
            });
        });

        document.getElementById('ws-switcher').addEventListener('change', (e) => {
            setWorkspace(parseInt(e.target.value, 10));
        });

        navigate('overview');
    }

    async function loadWorkspaces() {
        try {
            const response = await api.listWorkspaces();
            const items = response.data.items || [];
            const select = document.getElementById('ws-switcher');
            select.innerHTML = items.map((w) => `<option value="${w.id}">${escapeHtml(w.name)}</option>`).join('');
            if (items.length === 0) {
                const ws = await onNewWorkspace(true);
                if (!ws) return;
            } else {
                setWorkspace(items[0].id, items[0].name);
            }
        } catch (error) {
            showError('Failed to load workspaces');
        }
    }

    async function onNewWorkspace(silent = false) {
        const name = silent ? 'My Notebook' : (window.prompt('Workspace name', 'New workspace') || '').trim();
        if (!name) return null;
        try {
            const response = await api.createWorkspace(name, '');
            const ws = response.data;
            const select = document.getElementById('ws-switcher');
            const opt = document.createElement('option');
            opt.value = ws.id;
            opt.textContent = ws.name;
            select.appendChild(opt);
            select.value = String(ws.id);
            setWorkspace(ws.id, ws.name);
            if (!silent) showSuccess('Workspace created');
            return ws;
        } catch (error) {
            showError('Failed to create workspace');
            return null;
        }
    }

    function setWorkspace(id, name) {
        state.workspaceId = id;
        state.workspaceName = name || '';
        document.getElementById('ws-bc-workspace').textContent = state.workspaceName || 'Notebook';
        const select = document.getElementById('ws-switcher');
        if (select) select.value = String(id);
        navigate(state.currentPage || 'overview', { reload: true });
    }

    function navigate(page, { reload = false } = {}) {
        if (!PAGES[page]) page = 'overview';
        if (!reload && state.currentPage === page) {
            return;
        }
        stopJobPollers();
        state.currentPage = page;
        document.querySelectorAll('.ws-nav-item').forEach((el) => {
            el.classList.toggle('active', el.dataset.page === page);
        });
        document.getElementById('ws-bc-page').textContent = PAGES[page].label;
        PAGES[page].render(state);
    }

    function stopJobPollers() {
        state.jobPollers.forEach((id) => clearInterval(id));
        state.jobPollers.clear();
    }

    function trackPoller(id) {
        state.jobPollers.add(id);
        return id;
    }

    function renderLoading(label = 'Loading…') {
        const content = document.getElementById('ws-content');
        content.innerHTML = `
            <div class="ws-page">
                <div class="ws-state ws-state-loading">
                    <span class="spinner" role="status" aria-label="${escapeHtml(label)}"></span>
                    <span>${escapeHtml(label)}</span>
                </div>
            </div>
        `;
    }

    function renderEmpty(heading, body, actionLabel, actionHandler) {
        const content = document.getElementById('ws-content');
        content.innerHTML = `
            <div class="ws-page">
                <div class="ws-state ws-state-empty">
                    <h2>${escapeHtml(heading)}</h2>
                    <p>${escapeHtml(body)}</p>
                    ${actionLabel ? `<button class="btn btn-primary" type="button" id="ws-empty-action">${escapeHtml(actionLabel)}</button>` : ''}
                </div>
            </div>
        `;
        if (actionLabel && actionHandler) {
            document.getElementById('ws-empty-action').addEventListener('click', actionHandler);
        }
    }

    function renderError(message) {
        const content = document.getElementById('ws-content');
        content.innerHTML = `
            <div class="ws-page">
                <div class="ws-state ws-state-error">
                    <h2>Something went wrong</h2>
                    <p>${escapeHtml(message)}</p>
                </div>
            </div>
        `;
    }

    async function refreshWorkspace() {
        if (!state.workspaceId) return;
        try {
            const [src, notes, arts, qs] = await Promise.all([
                api.listSources(state.workspaceId),
                api.listNotes(state.workspaceId),
                api.listArtifacts(state.workspaceId),
                api.listQueries(state.workspaceId),
            ]);
            state.sources = src.data.items || [];
            state.notes = notes.data.items || [];
            state.artifacts = arts.data.items || [];
            state.queries = qs.data.items || [];
        } catch (error) {
            showError('Failed to load workspace data');
        }
    }

    // Pages ----------------------------------------------------------------

    async function renderOverview() {
        if (!state.workspaceId) return;
        renderLoading();
        await refreshWorkspace();
        const ready = state.sources.filter((s) => s.status === 'ready').length;
        const queued = state.sources.filter((s) => ['queued', 'processing'].includes(s.status)).length;
        const failed = state.sources.filter((s) => s.status === 'failed').length;
        const artifacts = state.artifacts.length;
        const content = document.getElementById('ws-content');
        content.innerHTML = `
            <div class="ws-page">
                <header class="ws-hero">
                    <div>
                        <p class="ws-eyebrow">Workspace</p>
                        <h1 class="ws-hero-title">${escapeHtml(state.workspaceName || 'Notebook')}</h1>
                        <p class="ws-hero-sub">Ground answers, slides, and quizzes in the sources you trust.</p>
                    </div>
                    <div class="ws-hero-actions">
                        <button class="btn btn-secondary" type="button" data-nav="sources">Add a source</button>
                        <button class="btn btn-primary" type="button" data-nav="ask">Ask notebook</button>
                    </div>
                </header>
                <section class="ws-metrics" aria-label="Workspace metrics">
                    ${metric('Ready sources', ready)}
                    ${metric('In progress', queued)}
                    ${metric('Failed', failed)}
                    ${metric('Artifacts', artifacts)}
                </section>
                <section class="ws-launchers" aria-label="Generate artifacts">
                    <h2 class="ws-section-title">Generate from your evidence</h2>
                    <div class="ws-launcher-grid">
                        ${launcher('Slides', 'slides', 'Outline ready sources into slide decks.')}
                        ${launcher('Mind map', 'mindmap', 'Visualize themes and their supporting sources.')}
                        ${launcher('Data table', 'table', 'Compare sources side by side.')}
                        ${launcher('Quiz', 'quiz', 'Build a study quiz from your sources.')}
                        ${launcher('Summary', 'summary', 'Produce a concise grounded summary.')}
                    </div>
                </section>
                <section class="ws-private-card" aria-label="Privacy">
                    <h3>Your notebook is private by default</h3>
                    <p>Only you can read your sources, notes, and artifacts. Citations are required for every generated claim.</p>
                </section>
            </div>
        `;
        content.querySelectorAll('[data-nav]').forEach((el) => {
            el.addEventListener('click', () => navigate(el.dataset.nav));
        });
    }

    function metric(label, value) {
        return `
            <article class="ws-metric">
                <p class="ws-metric-label">${escapeHtml(label)}</p>
                <p class="ws-metric-value">${value}</p>
            </article>
        `;
    }

    function launcher(title, page, body) {
        return `
            <button class="ws-launcher" type="button" data-page="${page}">
                <span class="ws-launcher-title">${escapeHtml(title)}</span>
                <span class="ws-launcher-body">${escapeHtml(body)}</span>
            </button>
        `;
    }

    async function renderSources() {
        if (!state.workspaceId) return;
        renderLoading();
        await refreshWorkspace();
        const content = document.getElementById('ws-content');
        content.innerHTML = `
            <div class="ws-page">
                <header class="ws-page-header">
                    <div>
                        <h1 class="ws-page-title">Sources</h1>
                        <p class="ws-page-sub">Import HTTP(S) URLs. Sources are ingested in the background and remain private to you.</p>
                    </div>
                </header>
                <form class="ws-card ws-form" id="ws-source-form" novalidate>
                    <div class="ws-form-row">
                        <label for="ws-src-url">Source URL</label>
                        <input id="ws-src-url" name="url" type="url" required maxlength="2048"
                            placeholder="https://example.com/article" autocomplete="off">
                    </div>
                    <div class="ws-form-row">
                        <label for="ws-src-title">Title <span class="ws-optional">(optional)</span></label>
                        <input id="ws-src-title" name="title" type="text" maxlength="512"
                            placeholder="A short name to recognise this source" autocomplete="off">
                    </div>
                    <div class="ws-form-actions">
                        <button class="btn btn-primary" type="submit">Queue source</button>
                    </div>
                </form>
                <div class="ws-card-list" id="ws-source-list" aria-live="polite"></div>
            </div>
        `;
        const form = document.getElementById('ws-source-form');
        form.addEventListener('submit', onCreateSource);

        const list = document.getElementById('ws-source-list');
        if (state.sources.length === 0) {
            list.innerHTML = `<div class="ws-state ws-state-empty">
                <h3>No sources yet</h3>
                <p>Add a public HTTP(S) URL to begin building your notebook.</p>
            </div>`;
            return;
        }
        list.innerHTML = state.sources.map((s) => sourceCard(s)).join('');
        list.querySelectorAll('[data-action="delete"]').forEach((el) => {
            el.addEventListener('click', () => onDeleteSource(parseInt(el.dataset.id, 10)));
        });
        list.querySelectorAll('[data-action="resync"]').forEach((el) => {
            el.addEventListener('click', () => onResyncSource(parseInt(el.dataset.id, 10)));
        });
    }

    function sourceCard(s) {
        const statusClass = `ws-status ws-status-${s.status}`;
        return `
            <article class="ws-card ws-source-row">
                <div class="ws-source-main">
                    <a class="ws-source-title" href="${escapeAttr(s.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(s.title || s.url)}</a>
                    <p class="ws-source-url">${escapeHtml(s.url)}</p>
                    ${s.error_message ? `<p class="ws-source-error">${escapeHtml(s.error_message)}</p>` : ''}
                </div>
                <div class="ws-source-meta">
                    <span class="${statusClass}">${escapeHtml(s.status)}</span>
                    <div class="ws-row-actions">
                        <button class="btn btn-ghost btn-sm" type="button" data-action="resync" data-id="${s.id}">Re-sync</button>
                        <button class="btn btn-danger btn-sm" type="button" data-action="delete" data-id="${s.id}">Delete</button>
                    </div>
                </div>
            </article>
        `;
    }

    async function onCreateSource(e) {
        e.preventDefault();
        const url = document.getElementById('ws-src-url').value.trim();
        const title = document.getElementById('ws-src-title').value.trim();
        if (!url) {
            showError('A public HTTP(S) URL is required');
            return;
        }
        try {
            const response = await api.createSource(state.workspaceId, url, title);
            if (response.data && response.data.duplicate) {
                showSuccess('Source already in this workspace');
            } else {
                showSuccess('Source queued for ingestion');
            }
            await renderSources();
        } catch (error) {
            showError(error.message || 'Failed to add source');
        }
    }

    async function onDeleteSource(id) {
        if (!window.confirm('Delete this source? Generated artifacts will keep their citations.')) return;
        try {
            await api.deleteSource(state.workspaceId, id);
            showSuccess('Source deleted');
            await renderSources();
        } catch (error) {
            showError('Failed to delete source');
        }
    }

    async function onResyncSource(id) {
        try {
            const response = await api.resyncSource(state.workspaceId, id);
            const job = response.data.job;
            showSuccess('Re-sync queued');
            await runJobAndRefresh(job.id);
        } catch (error) {
            showError('Failed to queue re-sync');
        }
    }

    async function runJobAndRefresh(jobId) {
        try {
            await api.runJob(jobId);
        } catch (error) {
            // The local run-job endpoint is best-effort. The worker CLI is
            // the production path. We poll the job to learn the status.
        }
        await pollJob(jobId);
        if (PAGES[state.currentPage] && PAGES[state.currentPage].render) {
            await PAGES[state.currentPage].render(state);
        }
    }

    async function pollJob(jobId) {
        return new Promise((resolve) => {
            const id = setInterval(async () => {
                try {
                    const r = await api.getJob(jobId);
                    if (['succeeded', 'failed'].includes(r.data.status)) {
                        clearInterval(id);
                        state.jobPollers.delete(id);
                        resolve(r.data);
                    }
                } catch (err) {
                    clearInterval(id);
                    state.jobPollers.delete(id);
                    resolve(null);
                }
            }, 1500);
            trackPoller(id);
            // Stop polling after 60 seconds to avoid runaway loops.
            setTimeout(() => {
                clearInterval(id);
                state.jobPollers.delete(id);
                resolve(null);
            }, 60_000);
        });
    }

    async function renderNotebookNotes() {
        if (!state.workspaceId) return;
        renderLoading();
        await refreshWorkspace();
        const content = document.getElementById('ws-content');
        content.innerHTML = `
            <div class="ws-page">
                <header class="ws-page-header">
                    <div>
                        <h1 class="ws-page-title">Notebook notes</h1>
                        <p class="ws-page-sub">Notes are searchable by Ask notebook. Archive notes to remove them from the default scope.</p>
                    </div>
                </header>
                <form class="ws-card ws-form" id="ws-note-form" novalidate>
                    <div class="ws-form-row">
                        <label for="ws-note-title">Title</label>
                        <input id="ws-note-title" name="title" type="text" required maxlength="255"
                            placeholder="A recognisable name for this note" autocomplete="off">
                    </div>
                    <div class="ws-form-row">
                        <label for="ws-note-content">Content</label>
                        <textarea id="ws-note-content" name="content" maxlength="50000"
                            placeholder="Write what you know. Ask notebook will cite this when relevant."></textarea>
                    </div>
                    <div class="ws-form-actions">
                        <button class="btn btn-primary" type="submit">Save note</button>
                    </div>
                </form>
                <div class="ws-card-list" id="ws-note-list" aria-live="polite"></div>
            </div>
        `;
        document.getElementById('ws-note-form').addEventListener('submit', onCreateNote);
        const list = document.getElementById('ws-note-list');
        if (state.notes.length === 0) {
            list.innerHTML = `<div class="ws-state ws-state-empty">
                <h3>No notebook notes yet</h3>
                <p>Add a note to capture your own thinking. Ask notebook will cite it when relevant.</p>
            </div>`;
            return;
        }
        list.innerHTML = state.notes.map((n) => noteCard(n)).join('');
        list.querySelectorAll('[data-action="archive"]').forEach((el) => {
            el.addEventListener('click', () => onArchiveNote(parseInt(el.dataset.id, 10)));
        });
        list.querySelectorAll('[data-action="delete"]').forEach((el) => {
            el.addEventListener('click', () => onDeleteNote(parseInt(el.dataset.id, 10)));
        });
    }

    function noteCard(n) {
        return `
            <article class="ws-card ws-note-row">
                <div class="ws-note-main">
                    <h3 class="ws-note-title">${escapeHtml(n.title)}</h3>
                    <p class="ws-note-content">${escapeHtml(n.content).slice(0, 400)}</p>
                </div>
                <div class="ws-note-meta">
                    <span class="ws-status ws-status-${n.status}">${escapeHtml(n.status)}</span>
                    <div class="ws-row-actions">
                        ${n.status === 'active'
                            ? `<button class="btn btn-ghost btn-sm" type="button" data-action="archive" data-id="${n.id}">Archive</button>`
                            : ''}
                        <button class="btn btn-danger btn-sm" type="button" data-action="delete" data-id="${n.id}">Delete</button>
                    </div>
                </div>
            </article>
        `;
    }

    async function onCreateNote(e) {
        e.preventDefault();
        const title = document.getElementById('ws-note-title').value.trim();
        const content = document.getElementById('ws-note-content').value;
        if (!title) {
            showError('A title is required');
            return;
        }
        try {
            await api.createNote(state.workspaceId, title, content);
            showSuccess('Note saved');
            document.getElementById('ws-note-title').value = '';
            document.getElementById('ws-note-content').value = '';
            await renderNotebookNotes();
        } catch (error) {
            showError('Failed to save note');
        }
    }

    async function onArchiveNote(id) {
        try {
            await api.updateNote(state.workspaceId, id, { status: 'archived' });
            showSuccess('Note archived');
            await renderNotebookNotes();
        } catch (error) {
            showError('Failed to archive note');
        }
    }

    async function onDeleteNote(id) {
        if (!window.confirm('Delete this notebook note?')) return;
        try {
            await api.deleteNote(state.workspaceId, id);
            showSuccess('Note deleted');
            await renderNotebookNotes();
        } catch (error) {
            showError('Failed to delete note');
        }
    }

    async function renderAskNotebook() {
        if (!state.workspaceId) return;
        renderLoading();
        await refreshWorkspace();
        const content = document.getElementById('ws-content');
        const readySources = state.sources.filter((s) => s.status === 'ready');
        const activeNotes = state.notes.filter((n) => n.status === 'active');
        content.innerHTML = `
            <div class="ws-page">
                <header class="ws-page-header">
                    <div>
                        <h1 class="ws-page-title">Ask notebook</h1>
                        <p class="ws-page-sub">Ask anything over your ready sources and active notebook notes. Empty selectors mean <em>search all eligible evidence</em>.</p>
                    </div>
                </header>
                <form class="ws-card ws-form" id="ws-ask-form" novalidate>
                    <div class="ws-form-row">
                        <label for="ws-ask-question">Your question</label>
                        <textarea id="ws-ask-question" required maxlength="2000"
                            placeholder="What is the main claim in the sources?"></textarea>
                    </div>
                    <div class="ws-form-row ws-form-row-2">
                        <div>
                            <label for="ws-ask-sources">Limit to sources <span class="ws-optional">(optional)</span></label>
                            <select id="ws-ask-sources" multiple size="4" aria-describedby="ws-ask-sources-hint">
                                ${readySources.map((s) => `<option value="${s.id}">${escapeHtml(s.title || s.url)}</option>`).join('')}
                            </select>
                            <p class="ws-hint" id="ws-ask-sources-hint">Hold Ctrl/Cmd to select multiple.</p>
                        </div>
                        <div>
                            <label for="ws-ask-notes">Limit to notebook notes <span class="ws-optional">(optional)</span></label>
                            <select id="ws-ask-notes" multiple size="4">
                                ${activeNotes.map((n) => `<option value="${n.id}">${escapeHtml(n.title)}</option>`).join('')}
                            </select>
                        </div>
                    </div>
                    <div class="ws-form-actions">
                        <button class="btn btn-primary" type="submit">Ask</button>
                    </div>
                </form>
                <section class="ws-card ws-answer" id="ws-answer" hidden></section>
                <section class="ws-conversation" aria-label="Recent questions">
                    <h2 class="ws-section-title">Recent questions</h2>
                    <div class="ws-conversation-list" id="ws-conversation"></div>
                </section>
            </div>
        `;
        document.getElementById('ws-ask-form').addEventListener('submit', onAsk);
        renderConversation();
    }

    function renderConversation() {
        const list = document.getElementById('ws-conversation');
        if (!list) return;
        if (!state.queries || state.queries.length === 0) {
            list.innerHTML = `<div class="ws-state ws-state-empty">
                <h3>No questions yet</h3>
                <p>Ask your first question to begin the conversation.</p>
            </div>`;
            return;
        }
        list.innerHTML = state.queries.map((q) => `
            <article class="ws-card ws-query-row">
                <div class="ws-query-q">${escapeHtml(q.question)}</div>
                <div class="ws-query-a">${escapeHtml(q.answer || '').replace(/\n/g, '<br>')}</div>
                <div class="ws-query-meta">
                    <span class="ws-status ws-status-${q.status}">${escapeHtml(q.status)}</span>
                    ${q.citations && q.citations.length
                        ? `<span class="ws-citations">${q.citations.length} citation(s)</span>`
                        : ''}
                </div>
            </article>
        `).join('');
    }

    async function onAsk(e) {
        e.preventDefault();
        const question = document.getElementById('ws-ask-question').value.trim();
        const sourceIds = Array.from(document.getElementById('ws-ask-sources').selectedOptions).map((o) => parseInt(o.value, 10));
        const noteIds = Array.from(document.getElementById('ws-ask-notes').selectedOptions).map((o) => parseInt(o.value, 10));
        if (!question) {
            showError('Please enter a question');
            return;
        }
        try {
            const response = await api.createQuery(state.workspaceId, { question, source_ids: sourceIds, note_ids: noteIds });
            const job = response.data.job;
            const query = response.data.query;
            renderPendingAnswer(query, job);
            await runJobAndRefresh(job.id);
            const refreshed = await api.getQuery(state.workspaceId, query.id);
            renderAnswer(refreshed.data);
            await refreshWorkspace();
            renderConversation();
        } catch (error) {
            showError(error.message || 'Failed to ask');
        }
    }

    function renderPendingAnswer(query, job) {
        const section = document.getElementById('ws-answer');
        if (!section) return;
        section.hidden = false;
        section.innerHTML = `
            <div class="ws-answer-pending">
                <span class="spinner" aria-hidden="true"></span>
                <p>Searching your notebook…</p>
                <p class="ws-hint">Question: ${escapeHtml(query.question)}</p>
            </div>
        `;
    }

    function renderAnswer(query) {
        const section = document.getElementById('ws-answer');
        if (!section) return;
        section.hidden = false;
        const citations = (query.citations || []).map((c) => citationHtml(c)).join('');
        const safeAnswer = escapeHtml(query.answer || '').replace(/\n/g, '<br>');
        section.innerHTML = `
            <h2 class="ws-section-title">Answer</h2>
            <p class="ws-answer-body">${safeAnswer || '<em>No answer was produced.</em>'}</p>
            ${citations ? `<div class="ws-citation-list"><h3>Citations</h3><ul>${citations}</ul></div>` : ''}
            <p class="ws-status ws-status-${query.status}">${escapeHtml(query.status)}</p>
        `;
    }

    function citationHtml(c) {
        const title = escapeHtml(c.title || 'Untitled');
        if (c.source_id) {
            const source = state.sources.find((s) => s.id === c.source_id);
            const url = source ? source.url : '#';
            return `<li><a href="${escapeAttr(url)}" target="_blank" rel="noopener noreferrer">${title}</a> <span class="ws-locator">${escapeHtml(c.locator || '')}</span></li>`;
        }
        if (c.note_id) {
            return `<li><span class="ws-citation-note">${title}</span> <span class="ws-locator">${escapeHtml(c.locator || '')}</span></li>`;
        }
        return `<li>${title}</li>`;
    }

    // Artifact pages -------------------------------------------------------

    async function renderArtifactPage(_, type, title) {
        if (!state.workspaceId) return;
        renderLoading();
        await refreshWorkspace();
        const content = document.getElementById('ws-content');
        const readySources = state.sources.filter((s) => s.status === 'ready');
        const existing = state.artifacts.filter((a) => a.artifact_type === type);
        content.innerHTML = `
            <div class="ws-page">
                <header class="ws-page-header">
                    <div>
                        <h1 class="ws-page-title">${escapeHtml(title)}</h1>
                        <p class="ws-page-sub">Generate from the ready sources you select. Empty selection uses every ready source in this workspace.</p>
                    </div>
                </header>
                <form class="ws-card ws-form" id="ws-artifact-form" novalidate>
                    <div class="ws-form-row">
                        <label for="ws-artifact-title">Title</label>
                        <input id="ws-artifact-title" required maxlength="255" placeholder="${escapeAttr(title)} outline" autocomplete="off">
                    </div>
                    <div class="ws-form-row">
                        <label for="ws-artifact-instructions">Instructions <span class="ws-optional">(optional)</span></label>
                        <textarea id="ws-artifact-instructions" maxlength="2000"
                            placeholder="Audience, tone, or focus. Source text is treated as untrusted data."></textarea>
                    </div>
                    <div class="ws-form-row">
                        <label for="ws-artifact-sources">Use these ready sources <span class="ws-optional">(optional)</span></label>
                        <select id="ws-artifact-sources" multiple size="5">
                            ${readySources.map((s) => `<option value="${s.id}">${escapeHtml(s.title || s.url)}</option>`).join('')}
                        </select>
                    </div>
                    <div class="ws-form-actions">
                        <button class="btn btn-primary" type="submit">Generate</button>
                    </div>
                </form>
                <section class="ws-artifact-history" aria-label="History">
                    <h2 class="ws-section-title">History</h2>
                    <div class="ws-card-list" id="ws-artifact-list"></div>
                </section>
            </div>
        `;
        document.getElementById('ws-artifact-form').addEventListener('submit', (e) => onCreateArtifact(e, type));
        const list = document.getElementById('ws-artifact-list');
        if (existing.length === 0) {
            list.innerHTML = `<div class="ws-state ws-state-empty">
                <h3>No ${escapeHtml(title).toLowerCase()} yet</h3>
                <p>Generate your first one to see structured, source-grounded output here.</p>
            </div>`;
            return;
        }
        list.innerHTML = existing.map((a) => artifactCard(a)).join('');
        list.querySelectorAll('[data-action="view"]').forEach((el) => {
            el.addEventListener('click', () => onViewArtifact(parseInt(el.dataset.id, 10)));
        });
    }

    function artifactCard(a) {
        let preview = '';
        try {
            const parsed = JSON.parse(a.content || '{}');
            if (a.artifact_type === 'slides' && parsed.slides) {
                preview = `${parsed.slides.length} slide(s)`;
            } else if (a.artifact_type === 'mindmap' && parsed.children) {
                preview = `${parsed.children.length} node(s)`;
            } else if (a.artifact_type === 'table' && parsed.rows) {
                preview = `${parsed.rows.length} row(s)`;
            } else if (a.artifact_type === 'quiz' && parsed.questions) {
                preview = `${parsed.questions.length} question(s)`;
            } else if (a.artifact_type === 'summary') {
                preview = (parsed.summary || '').slice(0, 80);
            }
        } catch (err) {
            preview = a.error_message || '';
        }
        return `
            <article class="ws-card ws-artifact-row">
                <div class="ws-artifact-main">
                    <h3>${escapeHtml(a.title)}</h3>
                    <p class="ws-artifact-preview">${escapeHtml(preview)}</p>
                </div>
                <div class="ws-artifact-meta">
                    <span class="ws-status ws-status-${a.status}">${escapeHtml(a.status)}</span>
                    <button class="btn btn-ghost btn-sm" type="button" data-action="view" data-id="${a.id}">View</button>
                </div>
            </article>
        `;
    }

    async function onCreateArtifact(e, type) {
        e.preventDefault();
        const title = document.getElementById('ws-artifact-title').value.trim();
        const instructions = document.getElementById('ws-artifact-instructions').value;
        const sourceIds = Array.from(document.getElementById('ws-artifact-sources').selectedOptions).map((o) => parseInt(o.value, 10));
        if (!title) {
            showError('Please add a title');
            return;
        }
        try {
            const response = await api.createArtifact(state.workspaceId, {
                artifact_type: type,
                title,
                instructions,
                source_ids: sourceIds,
            });
            showSuccess('Generation queued');
            await runJobAndRefresh(response.data.job.id);
        } catch (error) {
            showError(error.message || 'Failed to generate');
        }
    }

    async function onViewArtifact(id) {
        try {
            const response = await api.getArtifact(state.workspaceId, id);
            const a = response.data;
            const parsed = a.content ? JSON.parse(a.content) : null;
            const modal = document.createElement('div');
            modal.className = 'modal open';
            modal.innerHTML = `
                <div class="modal-content ws-modal-wide">
                    <div class="modal-header">
                        <h2 class="modal-title">${escapeHtml(a.title)}</h2>
                        <button class="modal-close" type="button" aria-label="Close">×</button>
                    </div>
                    <div class="modal-body">${renderArtifactContent(a.artifact_type, parsed)}</div>
                </div>
            `;
            document.body.appendChild(modal);
            modal.querySelector('.modal-close').addEventListener('click', () => modal.remove());
            modal.addEventListener('click', (e) => { if (e.target === modal) modal.remove(); });
        } catch (error) {
            showError('Failed to load artifact');
        }
    }

    function renderArtifactContent(type, parsed) {
        if (!parsed) return '<p>No content yet.</p>';
        if (type === 'slides' && parsed.slides) {
            return parsed.slides.map((s) => `
                <section class="ws-artifact-slide">
                    <h3>${escapeHtml(s.title || '')}</h3>
                    <ul>${(s.bullets || []).map((b) => `<li>${escapeHtml(b)}</li>`).join('')}</ul>
                    ${s.speaker_notes ? `<p class="ws-artifact-notes">${escapeHtml(s.speaker_notes)}</p>` : ''}
                </section>
            `).join('');
        }
        if (type === 'mindmap' && parsed.children) {
            return `<h3>${escapeHtml(parsed.root || 'Mind map')}</h3>
                <ul class="ws-mindmap">${parsed.children.map((c) => `
                    <li>
                        <strong>${escapeHtml(c.label || '')}</strong>
                        ${c.detail ? `<p>${escapeHtml(c.detail)}</p>` : ''}
                    </li>`).join('')}</ul>`;
        }
        if (type === 'table' && parsed.rows) {
            return `<table class="ws-table"><thead><tr>${(parsed.columns || []).map((c) => `<th>${escapeHtml(c)}</th>`).join('')}</tr></thead>
                <tbody>${parsed.rows.map((r) => `<tr>${r.map((cell) => `<td>${escapeHtml(cell || '')}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
        }
        if (type === 'quiz' && parsed.questions) {
            return parsed.questions.map((q) => `
                <section class="ws-quiz">
                    <h4>${escapeHtml(q.question || '')}</h4>
                    <ol type="a">${(q.options || []).map((o) => `<li>${escapeHtml(o)}</li>`).join('')}</ol>
                    ${q.explanation ? `<p class="ws-artifact-notes">${escapeHtml(q.explanation)}</p>` : ''}
                </section>
            `).join('');
        }
        if (type === 'summary') {
            return `<p>${escapeHtml(parsed.summary || '').replace(/\n/g, '<br>')}</p>`;
        }
        return `<pre>${escapeHtml(JSON.stringify(parsed, null, 2))}</pre>`;
    }

    // Legacy notes/archived pages proxy to notesModule but scoped to the
    // current workspace's user. They preserve the original behaviour.
    async function renderLegacyNotes() {
        await refreshWorkspace();
        const content = document.getElementById('ws-content');
        try {
            const response = await api.getNotes(1, 20, 'active');
            const items = response.data.items || [];
            content.innerHTML = `
                <div class="ws-page">
                    <header class="ws-page-header">
                        <div>
                            <h1 class="ws-page-title">My Notes</h1>
                            <p class="ws-page-sub">Legacy user-owned notes. New work happens in the workspace Notebook notes tab.</p>
                        </div>
                    </header>
                    ${items.length === 0
                        ? `<div class="ws-state ws-state-empty"><h3>No notes yet</h3><p>Create your first note in the legacy dashboard.</p></div>`
                        : `<div class="ws-card-list">${items.map(legacyNoteHtml).join('')}</div>`}
                </div>
            `;
        } catch (error) {
            renderError('Failed to load legacy notes');
        }
    }

    async function renderLegacyArchived() {
        await refreshWorkspace();
        const content = document.getElementById('ws-content');
        try {
            const response = await api.getNotes(1, 20, 'archived');
            const items = response.data.items || [];
            content.innerHTML = `
                <div class="ws-page">
                    <header class="ws-page-header">
                        <div>
                            <h1 class="ws-page-title">Archived Notes</h1>
                            <p class="ws-page-sub">Legacy archived notes.</p>
                        </div>
                    </header>
                    ${items.length === 0
                        ? `<div class="ws-state ws-state-empty"><h3>No archived notes</h3></div>`
                        : `<div class="ws-card-list">${items.map(legacyNoteHtml).join('')}</div>`}
                </div>
            `;
        } catch (error) {
            renderError('Failed to load archived notes');
        }
    }

    function legacyNoteHtml(n) {
        return `
            <article class="ws-card">
                <h3>${escapeHtml(n.title)}</h3>
                <p>${escapeHtml(n.content)}</p>
                <p class="ws-hint">${escapeHtml(n.status)} · ${escapeHtml(n.created_at)}</p>
            </article>
        `;
    }

    function toggleSidebar() {
        const sidebar = document.getElementById('ws-sidebar');
        const backdrop = document.getElementById('ws-backdrop');
        const open = sidebar.classList.toggle('open');
        backdrop.hidden = !open;
    }

    function closeSidebar() {
        document.getElementById('ws-sidebar').classList.remove('open');
        document.getElementById('ws-backdrop').hidden = true;
    }

    function clearState() {
        stopJobPollers();
        state.workspaceId = null;
        state.workspaceName = '';
        state.sources = [];
        state.notes = [];
        state.queries = [];
        state.artifacts = [];
        state.currentPage = 'overview';
        state.activeQuery = null;
    }

    return { init, clearState, navigate };
})();

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text == null ? '' : String(text);
    return div.innerHTML;
}

function escapeAttr(text) {
    return escapeHtml(text).replace(/"/g, '&quot;');
}

function showError(message) {
    const alert = document.createElement('div');
    alert.className = 'alert alert-error';
    alert.textContent = message;
    document.body.insertBefore(alert, document.body.firstChild);
    setTimeout(() => alert.remove(), 5000);
}

function showSuccess(message) {
    const alert = document.createElement('div');
    alert.className = 'alert alert-success';
    alert.textContent = message;
    document.body.insertBefore(alert, document.body.firstChild);
    setTimeout(() => alert.remove(), 5000);
}
