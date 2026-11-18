export const TOKEN_KEY = 'token';

export const getToken = () => localStorage.getItem(TOKEN_KEY);

export const setToken = (token) => localStorage.setItem(TOKEN_KEY, token);

export const removeToken = () => localStorage.removeItem(TOKEN_KEY);

// Returns the expiry time in ms since epoch, or null if it can't be read.
export const getTokenExpiry = (token) => {
  try {
    const payload = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
    const { exp } = JSON.parse(atob(payload));
    return typeof exp === 'number' ? exp * 1000 : null;
  } catch {
    return null;
  }
};

export const isTokenExpired = (token) => {
  const expiry = getTokenExpiry(token);
  return expiry !== null && expiry <= Date.now();
};

// Returns the stored token only if present and unexpired; clears it otherwise.
export const getValidToken = () => {
  const token = getToken();
  if (!token) return null;
  if (isTokenExpired(token)) {
    removeToken();
    return null;
  }
  return token;
};
