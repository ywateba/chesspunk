import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export const Login = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [needsVerification, setNeedsVerification] = useState(false);
  
  // Form State
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [code, setCode] = useState('');
  const [error, setError] = useState('');

  const { login, register, confirmRegistration, loginAsAdmin } = useAuth();
  const navigate = useNavigate();

  const handleAuth = async (e) => {
    e.preventDefault();
    setError('');

    try {
      if (needsVerification) {
        await confirmRegistration(email, code);
        // After confirmation, automatically log them in
        await login(email, password);
        navigate('/dashboard');
        return;
      }

      if (isLogin) {
        await login(email, password);
        navigate('/dashboard');
      } else {
        const { nextStep } = await register(email, password, name);
        if (nextStep?.signUpStep === 'CONFIRM_SIGN_UP') {
          setNeedsVerification(true);
        } else {
          // If auto confirmed or no verification needed
          await login(email, password);
          navigate('/dashboard');
        }
      }
    } catch (err) {
      setError(err.message || 'Authentication failed. Please try again.');
    }
  };

  const handleSocialAuth = (provider) => {
    // Mock social auth call
    console.log(`Authenticating with ${provider}`);
    if (provider === 'Google') {
      loginAsAdmin();
    } else {
      // If mock environment is active, this will mock login
      login('mock', 'mock').catch(() => {});
    }
    navigate('/dashboard');
  };

  return (
    <div className="container page-wrapper animate-in" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '80vh' }}>
      <div className="glass-panel" style={{ width: '100%', maxWidth: '440px', padding: '3rem 2rem' }}>
        
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <h2 className="text-gradient" style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>
            {needsVerification ? 'Verify Email' : isLogin ? 'Welcome Back' : 'Create Account'}
          </h2>
          <p style={{ margin: 0, fontSize: '0.9rem' }}>
            {needsVerification 
              ? 'Enter the 6-digit code sent to your email.' 
              : isLogin 
                ? 'Enter your credentials to access your account' 
                : 'Join the elite chesspunk community'}
          </p>
        </div>

        {error && (
          <div style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid #ef4444', color: '#f87171', padding: '0.75rem', borderRadius: '8px', marginBottom: '1.5rem', fontSize: '0.875rem' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleAuth}>
          {needsVerification ? (
            <div className="form-group">
              <label>Confirmation Code</label>
              <input type="text" className="input-field" placeholder="123456" value={code} onChange={(e) => setCode(e.target.value)} required />
            </div>
          ) : (
            <>
              {!isLogin && (
                <div className="form-group">
                  <label>Full Name</label>
                  <input type="text" className="input-field" placeholder="Grandmaster Name" value={name} onChange={(e) => setName(e.target.value)} required />
                </div>
              )}
              
              <div className="form-group">
                <label>Email Address</label>
                <input type="email" className="input-field" placeholder="you@example.com" value={email} onChange={(e) => setEmail(e.target.value)} required />
              </div>
              
              <div className="form-group">
                <label>Password</label>
                <input type="password" className="input-field" placeholder="••••••••" value={password} onChange={(e) => setPassword(e.target.value)} required />
              </div>
            </>
          )}

          <button type="submit" className="btn-primary" style={{ width: '100%', marginTop: '1rem' }}>
            {needsVerification ? 'Verify Account' : isLogin ? 'Sign In' : 'Register'}
          </button>
        </form>

        {!needsVerification && (
          <>
            <div className="divider">OR</div>

            <div className="social-logins">
              <button className="btn-social" onClick={() => handleSocialAuth('Google')}>
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                  <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                  <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                  <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
                </svg>
                Continue with Google
              </button>

              <button className="btn-social" onClick={() => handleSocialAuth('Facebook')}>
                <svg viewBox="0 0 24 24" fill="#1877F2" xmlns="http://www.w3.org/2000/svg">
                  <path d="M24 12.07C24 5.41 18.63 0 12 0S0 5.4 0 12.07C0 18.1 4.39 23.1 10.13 24v-8.44H7.08v-3.49h3.04V9.41c0-3.02 1.8-4.7 4.54-4.7 1.31 0 2.68.24 2.68.24v2.97h-1.5c-1.5 0-1.96.93-1.96 1.89v2.26h3.32l-.53 3.5h-2.8V24C19.62 23.1 24 18.1 24 12.07z"/>
                </svg>
                Continue with Facebook
              </button>

              <button className="btn-social" onClick={() => handleSocialAuth('LinkedIn')}>
                <svg viewBox="0 0 24 24" fill="#0A66C2" xmlns="http://www.w3.org/2000/svg">
                  <path d="M20.45 20.45h-3.56v-5.57c0-1.33-.02-3.04-1.85-3.04-1.85 0-2.14 1.45-2.14 2.94v5.67H9.35V9h3.41v1.56h.05c.48-.9 1.63-1.85 3.37-1.85 3.6 0 4.27 2.37 4.27 5.45v6.29zM5.34 7.43a2.06 2.06 0 110-4.13 2.06 2.06 0 010 4.13zM7.12 20.45H3.56V9h3.56v11.45zM22.22 0H1.77C.79 0 0 .77 0 1.73v20.54C0 23.23.79 24 1.77 24h20.45c.98 0 1.78-.77 1.78-1.73V1.73C24 .77 23.2 0 22.22 0z"/>
                </svg>
                Continue with LinkedIn
              </button>
            </div>

            <div style={{ textAlign: 'center', marginTop: '2rem', fontSize: '0.875rem' }}>
              <span style={{ color: 'var(--text-secondary)' }}>
                {isLogin ? "Don't have an account? " : "Already have an account? "}
              </span>
              <button 
                type="button"
                onClick={() => setIsLogin(!isLogin)}
                style={{ 
                  background: 'none', border: 'none', color: 'var(--accent-primary)', 
                  fontWeight: 600, cursor: 'pointer', padding: 0 
                }}
              >
                {isLogin ? 'Register now' : 'Sign In'}
              </button>
            </div>
          </>
        )}

      </div>
    </div>
  );
};
