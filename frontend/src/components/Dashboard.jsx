import { useState, useEffect } from 'react';
import { authAPI } from '../services/api';
import NotesList from './NotesList';

export default function Dashboard({ user, onLogout }) {
  const [stats, setStats] = useState({ total: 0, active: 0, archived: 0 });

  const handleLogout = async () => {
    try {
      await authAPI.logout();
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      onLogout();
    } catch (err) {
      console.error('Logout error:', err);
    }
  };

  return (
    <div>
      <nav style={{
        background: '#333',
        color: 'white',
        padding: '16px 20px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <h1 style={{ fontSize: '24px', margin: 0 }}>📝 Notes App</h1>
        <div className="flex items-center gap-2">
          <span>Welcome, {user.name || user.email}</span>
          <button className="btn-secondary" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </nav>

      <NotesList />
    </div>
  );
}