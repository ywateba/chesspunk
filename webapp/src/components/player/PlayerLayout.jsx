import React from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

export const PlayerLayout = () => {
  const { user } = useAuth();
  return (
    <div className="dashboard-container animate-in">
      <aside className="dashboard-sidebar">
        <div style={{ padding: '0 1rem', marginBottom: '2rem' }}>
          <h3 className="text-gradient" style={{ marginBottom: '0.25rem' }}>{user?.name}</h3>
          <p style={{ margin: 0, fontSize: '0.875rem' }}>Rating: 2450 | Elite Tier</p>
        </div>
        <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <NavLink to="/dashboard/overview" className={({ isActive }) => `dashboard-nav-item ${isActive ? 'active' : ''}`}>
            Overview
          </NavLink>
          <NavLink to="/dashboard/matches" className={({ isActive }) => `dashboard-nav-item ${isActive ? 'active' : ''}`}>
            Matches & Results
          </NavLink>
          <NavLink to="/dashboard/tournaments" className={({ isActive }) => `dashboard-nav-item ${isActive ? 'active' : ''}`}>
            My Tournaments
          </NavLink>
          <NavLink to="/dashboard/communities" className={({ isActive }) => `dashboard-nav-item ${isActive ? 'active' : ''}`}>
            My Communities
          </NavLink>
        </nav>
      </aside>
      
      <main className="dashboard-content">
        <Outlet />
      </main>
    </div>
  );
};
