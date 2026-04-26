import React from 'react';
import { NavLink, Outlet } from 'react-router-dom';

export const AdminLayout = () => {
  return (
    <div className="dashboard-container animate-in">
      <aside className="dashboard-sidebar">
        <h3 className="text-gradient" style={{ padding: '0 1rem', marginBottom: '2rem' }}>Control Panel</h3>
        <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <NavLink to="/admin/users" className={({ isActive }) => `dashboard-nav-item ${isActive ? 'active' : ''}`}>
            Users
          </NavLink>
          <NavLink to="/admin/communities" className={({ isActive }) => `dashboard-nav-item ${isActive ? 'active' : ''}`}>
            Communities
          </NavLink>
          <NavLink to="/admin/tournaments" className={({ isActive }) => `dashboard-nav-item ${isActive ? 'active' : ''}`}>
            Tournaments
          </NavLink>
        </nav>
      </aside>
      
      <main className="dashboard-content">
        <Outlet />
      </main>
    </div>
  );
};
