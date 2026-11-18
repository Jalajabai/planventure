import { getValidToken, removeToken } from '../utils/token';

const BASE_URL = 'http://localhost:5000';

const getAuthHeaders = () => {
  const token = getValidToken();
  return {
    'Content-Type': 'application/json',
    'Authorization': token ? `Bearer ${token}` : '',
  };
};

const handleResponse = async (response, { redirectOnUnauthorized = true } = {}) => {
  // Login/register return 401 for bad credentials, which is not an expired session
  if (response.status === 401 && redirectOnUnauthorized) {
    removeToken();
    window.location.href = '/login';
    throw new Error('Session expired. Please login again.');
  }

  if (response.status === 404) {
    throw new Error('Trip not found');
  }

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || data.message || 'Request failed');
  }

  return data;
};

export const api = {
  get: async (endpoint) => {
    const response = await fetch(`${BASE_URL}${endpoint}`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(response);
  },
  
  post: async (endpoint, data, options) => {
    const response = await fetch(`${BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(data),
    });
    return handleResponse(response, options);
  },

  put: async (endpoint, data) => {
    const response = await fetch(`${BASE_URL}${endpoint}`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(data),
    });
    return handleResponse(response);
  },

  auth: {
    login: async ({ email, password }) => {
      return api.post('/auth/login', { email, password }, { redirectOnUnauthorized: false });
    },

    register: async ({ email, password }) => {
      return api.post('/auth/register', { email, password }, { redirectOnUnauthorized: false });
    }
  }
};

export default api;