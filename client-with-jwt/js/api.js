/**
 * API Service
 * Handles all HTTP requests to the backend
 */

// Change this to your production backend URL when deploying
const API_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
    ? 'http://localhost:5000/api' 
    : 'https://your-production-api-url.com/api';

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
}

// Create global API instance
const api = new APIService();
