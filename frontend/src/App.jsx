import { useState, useEffect } from 'react';
import Auth from './components/Auth';
import Dashboard from './components/Dashboard';
import { authAPI } from './services/api';

export default function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('token');
      if (token) {
        try {
          const response = await authAPI.me();
          setUser(response.data.user);
        } catch (err) {
          localStorage.removeItem('token');
          localStorage.removeItem('user');
        }
      }
      setLoading(false);
    };

    checkAuth();
  }, []);

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh'
      }}>
        <div className="loading"></div>
      </div>
    );
  }

  return user ? (
    <Dashboard user={user} onLogout={() => setUser(null)} />
  ) : (
    <Auth onLoginSuccess={setUser} />
  );
}