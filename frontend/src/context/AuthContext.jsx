import React, { createContext, useContext, useState, useEffect } from 'react';
import {
  loginUser,
  registerCustomer,
  fetchCurrentUser,
  logoutUser,
  getAuthToken,
  setAuthToken
} from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setTokenState] = useState(getAuthToken());
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Auto-verify token on initial load
  useEffect(() => {
    async function initAuth() {
      const storedToken = getAuthToken();
      if (!storedToken) {
        setIsLoading(false);
        return;
      }
      try {
        const currentUser = await fetchCurrentUser();
        setUser(currentUser);
        setTokenState(storedToken);
      } catch (err) {
        console.warn('Session expired or invalid token:', err);
        setAuthToken(null);
        setTokenState(null);
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    }
    initAuth();
  }, []);

  const login = async (email, password) => {
    setError(null);
    try {
      const data = await loginUser(email, password);
      setUser(data.user);
      setTokenState(data.access_token);
      return data.user;
    } catch (err) {
      setError(err.message || 'Login failed.');
      throw err;
    }
  };

  const register = async (name, email, password, confirmPassword) => {
    setError(null);
    try {
      const data = await registerCustomer(name, email, password, confirmPassword);
      setUser(data.user);
      setTokenState(data.access_token);
      return data.user;
    } catch (err) {
      setError(err.message || 'Registration failed.');
      throw err;
    }
  };

  const logout = async () => {
    setError(null);
    await logoutUser();
    setUser(null);
    setTokenState(null);
  };

  const clearError = () => setError(null);

  const value = {
    user,
    token,
    role: user?.role || null,
    isAuthenticated: !!user,
    isLoading,
    error,
    login,
    register,
    logout,
    clearError
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
