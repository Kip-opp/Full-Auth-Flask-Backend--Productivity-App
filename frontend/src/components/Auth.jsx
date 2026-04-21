import { useState } from 'react';
import { authAPI } from '../services/api';

export default function Auth({ onLoginSuccess }) {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      let response;
      if (isLogin) {
        response = await authAPI.login(email, password);
      } else {
        response = await authAPI.signup(email, password, name);
      }

      localStorage.setItem('token', response.data.data.token);
      localStorage.setItem('user', JSON.stringify(response.data.data.user));
      onLoginSuccess(response.data.data.user);
    } catch (err) {
      setError(err.response?.data?.error?.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container" style={{ maxWidth: '400px', marginTop: '50px' }}>
      <div className="card">
        <h1 className="text-center mb-2">{isLogin ? 'Login' : 'Sign Up'}</h1>

        <form onSubmit={handleSubmit}>
          {!isLogin && (
            <div className="mb-2">
              <label>Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                style={{ width: '100%', marginTop: '4px' }}
              />
            </div>
          )}

          <div className="mb-2">
            <label>Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              style={{ width: '100%', marginTop: '4px' }}
            />
          </div>

          <div className="mb-2">
            <label>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              style={{ width: '100%', marginTop: '4px' }}
            />
          </div>

          {error && <div className="error">{error}</div>}

          <button
            type="submit"
            disabled={loading}
            className="btn-primary"
            style={{ width: '100%', marginTop: '16px' }}
          >
            {loading ? 'Loading...' : isLogin ? 'Login' : 'Sign Up'}
          </button>
        </form>

        <p className="text-center" style={{ marginTop: '16px' }}>
          {isLogin ? "Don't have an account? " : 'Already have an account? '}
          <button
            onClick={() => {
              setIsLogin(!isLogin);
              setError('');
            }}
            style={{ background: 'none', color: '#4CAF50', padding: 0, textDecoration: 'underline' }}
          >
            {isLogin ? 'Sign Up' : 'Login'}
          </button>
        </p>
      </div>
    </div>
  );
}