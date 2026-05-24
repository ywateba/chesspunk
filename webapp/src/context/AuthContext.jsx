import React, { createContext, useContext, useState, useEffect } from 'react';
import { Amplify } from 'aws-amplify';
import { getCurrentUser, signIn, signUp, signOut, fetchAuthSession } from 'aws-amplify/auth';

// Configure Amplify with the ENV variables
Amplify.configure({
  Auth: {
    Cognito: {
      userPoolId: import.meta.env.VITE_COGNITO_USER_POOL_ID || 'dummy-pool-id',
      userPoolClientId: import.meta.env.VITE_COGNITO_CLIENT_ID || 'dummy-client-id',
    }
  }
});

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Check session on load
  useEffect(() => {
    checkUser();
  }, []);

  const checkUser = async () => {
    try {
      const currentUser = await getCurrentUser();
      const session = await fetchAuthSession();
      
      // Extract groups from the JWT Access Token
      const groups = session.tokens?.accessToken?.payload['cognito:groups'] || [];
      const role = groups.includes('Admins') ? 'admin' : 'user';
      
      setUser({ ...currentUser, role }); 
    } catch (error) {
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (username, password) => {
    try {
      if (import.meta.env.VITE_COGNITO_USER_POOL_ID) {
        await signIn({ username, password });
        await checkUser();
      } else {
        // Fallback mock if env not set yet
        console.warn("MOCK LOGIN: .env variables missing");
        setUser({ id: '1', name: 'Grandmaster', role: 'user' });
      }
    } catch (error) {
      console.error('Error signing in', error);
      throw error;
    }
  };

  const loginAsAdmin = async () => {
    // Development shortcut mock
    setUser({ id: '99', name: 'System Admin', role: 'admin' });
  };

  const register = async (email, password, name) => {
    try {
      if (import.meta.env.VITE_COGNITO_USER_POOL_ID) {
        const { isSignUpComplete, nextStep } = await signUp({
          username: email,
          password,
          options: {
            userAttributes: {
              email,
              name // Assuming name is a standard Cognito attribute
            }
          }
        });
        return { isSignUpComplete, nextStep };
      } else {
        console.warn("MOCK REGISTER: .env variables missing. Proceeding to verify mock.");
        return { nextStep: { signUpStep: 'CONFIRM_SIGN_UP' } };
      }
    } catch (error) {
      console.error('Error signing up', error);
      throw error;
    }
  };

  const confirmRegistration = async (email, code) => {
    try {
      if (import.meta.env.VITE_COGNITO_USER_POOL_ID) {
        // Need to import confirmSignUp at the top. Wait, I'll need to make sure confirmSignUp is imported!
        // Actually, I can use dynamic import or just standard import. Let's assume it's imported at top.
        const { confirmSignUp } = await import('aws-amplify/auth');
        const { isSignUpComplete, nextStep } = await confirmSignUp({
          username: email,
          confirmationCode: code
        });
        return { isSignUpComplete, nextStep };
      } else {
        console.warn("MOCK VERIFY: .env variables missing.");
        return { isSignUpComplete: true };
      }
    } catch (error) {
      console.error('Error confirming sign up', error);
      throw error;
    }
  };

  const handleSignOut = async () => {
    try {
      if (import.meta.env.VITE_COGNITO_USER_POOL_ID) {
        await signOut();
      }
      setUser(null);
    } catch (error) {
      console.error('Error signing out', error);
    }
  };

  if (loading) {
    return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', color: 'white' }}>Loading Session...</div>;
  }

  return (
    <AuthContext.Provider value={{ user, login, register, confirmRegistration, loginAsAdmin, logout: handleSignOut }}>
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
