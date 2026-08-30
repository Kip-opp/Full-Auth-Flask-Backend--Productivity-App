/**
 * API Service
 * Handles all HTTP requests to the backend
 */

// On Vercel the API is served from the same origin under /api, so
// `${window.location.origin}/api` is used in production. Locally the
// backend runs on http://localhost:5000.
const API_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:5000/api'
    : `${window.location.origin}/api`;

class APIService {
    constructor() {
        this.token = localStorage.getItem('token');
    }

    setToken(token) {
        this.token = token;
        localStorage.setItem('token', token);
    }

    clearToken() {
        this.token = null;
        localStorage.removeItem('token');
    }

    getHeaders() {
        const headers = {
            'Content-Type': 'application/json',
        };
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }
        return headers;
    }

    async request(endpoint, options = {}) {
        const url = `${API_URL}${endpoint}`;
        const config = {
            headers: this.getHeaders(),
            ...options,
        };

        try {
            const response = await fetch(url, config);
            const data = await response.json();

            if (!response.ok) {
                const err = new Error(data.error?.message || 'Request failed');
                err.details = data.error?.details || null;
                throw err;
            }

            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    // Auth endpoints
    async signup(username, email, password) {
        return this.request('/auth/signup', {
            method: 'POST',
            body: JSON.stringify({ username, email, password }),
        });
    }

    async login(email, password) {
        return this.request('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password }),
        });
    }

    async loginWithGoogle(idToken) {
        return this.request('/auth/google', {
            method: 'POST',
            body: JSON.stringify({ id_token: idToken }),
        });
    }

    async googleConfig() {
        return this.request('/auth/google/config', { method: 'GET' });
    }

    async logout() {
        return this.request('/auth/logout', {
            method: 'POST',
        });
    }

    async getMe() {
        return this.request('/auth/me', {
            method: 'GET',
        });
    }

    // Notes endpoints
    async getNotes(page = 1, perPage = 10, status = null) {
        let endpoint = `/notes?page=${page}&per_page=${perPage}`;
        if (status) {
            endpoint += `&status=${status}`;
        }
        return this.request(endpoint, {
            method: 'GET',
        });
    }

    async getNote(id) {
        return this.request(`/notes/${id}`, {
            method: 'GET',
        });
    }

    async createNote(title, content, status = 'active') {
        return this.request('/notes', {
            method: 'POST',
            body: JSON.stringify({ title, content, status }),
        });
    }

    async updateNote(id, title, content, status) {
        const data = {};
        if (title !== undefined) data.title = title;
        if (content !== undefined) data.content = content;
        if (status !== undefined) data.status = status;

        return this.request(`/notes/${id}`, {
            method: 'PATCH',
            body: JSON.stringify(data),
        });
    }

    async deleteNote(id) {
        return this.request(`/notes/${id}`, {
            method: 'DELETE',
        });
    }

    // V1 workspace endpoints ----------------------------------------------------

    _v1(path, options) {
        return this.request(`/v1${path}`, options);
    }

    async listWorkspaces() {
        return this._v1('/workspaces', { method: 'GET' });
    }

    async createWorkspace(name, description = '') {
        return this._v1('/workspaces', {
            method: 'POST',
            body: JSON.stringify({ name, description }),
        });
    }

    async getWorkspace(id) {
        return this._v1(`/workspaces/${id}`, { method: 'GET' });
    }

    async updateWorkspace(id, data) {
        return this._v1(`/workspaces/${id}`, {
            method: 'PATCH',
            body: JSON.stringify(data),
        });
    }

    async deleteWorkspace(id) {
        return this._v1(`/workspaces/${id}`, { method: 'DELETE' });
    }

    async listSources(workspaceId) {
        return this._v1(`/workspaces/${workspaceId}/sources`, { method: 'GET' });
    }

    async createSource(workspaceId, url, title = '') {
        return this._v1(`/workspaces/${workspaceId}/sources`, {
            method: 'POST',
            body: JSON.stringify({ url, title }),
        });
    }

    async deleteSource(workspaceId, sourceId) {
        return this._v1(`/workspaces/${workspaceId}/sources/${sourceId}`, {
            method: 'DELETE',
        });
    }

    async resyncSource(workspaceId, sourceId) {
        return this._v1(`/workspaces/${workspaceId}/sources/${sourceId}/sync`, {
            method: 'POST',
        });
    }

    async listArtifacts(workspaceId) {
        return this._v1(`/workspaces/${workspaceId}/artifacts`, { method: 'GET' });
    }

    async createArtifact(workspaceId, payload) {
        return this._v1(`/workspaces/${workspaceId}/artifacts`, {
            method: 'POST',
            body: JSON.stringify(payload),
        });
    }

    async getArtifact(workspaceId, artifactId) {
        return this._v1(`/workspaces/${workspaceId}/artifacts/${artifactId}`, {
            method: 'GET',
        });
    }

    async getJob(jobId) {
        return this._v1(`/jobs/${jobId}`, { method: 'GET' });
    }

    async runJob(jobId) {
        return this._v1(`/jobs/${jobId}/run`, { method: 'POST' });
    }

    async listNotes(workspaceId, includeArchived = false) {
        const qs = includeArchived ? '?include_archived=true' : '';
        return this._v1(`/workspaces/${workspaceId}/notes${qs}`, { method: 'GET' });
    }

    async createNote(workspaceId, title, content) {
        return this._v1(`/workspaces/${workspaceId}/notes`, {
            method: 'POST',
            body: JSON.stringify({ title, content, status: 'active' }),
        });
    }

    async updateNote(workspaceId, noteId, data) {
        return this._v1(`/workspaces/${workspaceId}/notes/${noteId}`, {
            method: 'PATCH',
            body: JSON.stringify(data),
        });
    }

    async deleteNote(workspaceId, noteId) {
        return this._v1(`/workspaces/${workspaceId}/notes/${noteId}`, {
            method: 'DELETE',
        });
    }

    async listQueries(workspaceId) {
        return this._v1(`/workspaces/${workspaceId}/queries`, { method: 'GET' });
    }

    async createQuery(workspaceId, payload) {
        return this._v1(`/workspaces/${workspaceId}/queries`, {
            method: 'POST',
            body: JSON.stringify(payload),
        });
    }

    async getQuery(workspaceId, queryId) {
        return this._v1(`/workspaces/${workspaceId}/queries/${queryId}`, {
            method: 'GET',
        });
    }
}

// Create global API instance
const api = new APIService();
