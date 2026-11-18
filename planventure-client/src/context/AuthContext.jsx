import { createContext, useContext, useState, useEffect, useCallback, useMemo } from 'react';
import {
  TOKEN_KEY,
  getValidToken,
  getTokenExpiry,
  setToken as saveToken,
  removeToken,
} from '../utils/token';

const AuthContext = createContext(null);

// setTimeout overflows (and fires immediately) beyond ~24.8 days
const MAX_TIMEOUT_MS = 2 ** 31 - 1;

export const AuthProvider = ({ children }) => {
  // Read synchronously so protected routes never render with a stale auth state
  const [token, setToken] = useState(getValidToken);
  const isAuthenticated = !!token;

  const login = useCallback((authData) => {
    saveToken(authData.token);
    setToken(authData.token);
  }, []);

  const logout = useCallback(() => {
    removeToken();
    setToken(null);
  }, []);

  // Log out automatically when the token expires
  useEffect(() => {
    if (!token) return;
    const expiry = getTokenExpiry(token);
    if (expiry === null) return;
    const timer = setTimeout(
      logout,
      Math.min(Math.max(expiry - Date.now(), 0), MAX_TIMEOUT_MS)
    );
    return () => clearTimeout(timer);
  }, [token, logout]);

  // Keep multiple tabs in sync (login/logout in another tab)
  useEffect(() => {
    const handleStorage = (e) => {
      if (e.key === null || e.key === TOKEN_KEY) {
        setToken(getValidToken());
      }
    };
    window.addEventListener('storage', handleStorage);
    return () => window.removeEventListener('storage', handleStorage);
  }, []);

  const value = useMemo(
    () => ({ isAuthenticated, token, login, logout }),
    [isAuthenticated, token, login, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};