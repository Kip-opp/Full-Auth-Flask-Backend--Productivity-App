import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_URL,
});

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authAPI = {
  signup: (email, password, name) =>
    api.post('/auth/signup', { email, password, name }),
  login: (email, password) =>
    api.post('/auth/login', { email, password }),
  logout: () => api.post('/auth/logout'),
  me: () => api.get('/auth/me'),
};

export const notesAPI = {
  list: (page = 1, perPage = 10, status = null) =>
    api.get('/notes', { params: { page, perPage, status } }),
  get: (id) => api.get(`/notes/${id}`),
  create: (title, content, status = 'active') =>
    api.post('/notes', { title, content, status }),
  update: (id, title, content, status) =>
    api.patch(`/notes/${id}`, { title, content, status }),
  delete: (id) => api.delete(`/notes/${id}`),
};

export default api;