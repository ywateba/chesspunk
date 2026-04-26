import React, { createContext, useContext, useState } from 'react';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  // Mock user state. In a real app, you might check localStorage or validate a token on load.
  const [user, setUser] = useState(null);

  const login = () => {
    // Mock login as standard user
    setUser({ id: '1', name: 'Grandmaster', role: 'user' });
  };

  const loginAsAdmin = () => {
    // Mock login as admin
    setUser({ id: '99', name: 'System Admin', role: 'admin' });
  };

  const logout = () => {
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, loginAsAdmin, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
