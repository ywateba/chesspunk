import React from 'react';

export const ManageUsers = () => {
  const users = [
    { id: 1, name: 'Magnus C.', email: 'magnus@chess.com', role: 'admin', status: 'active' },
    { id: 2, name: 'Hikaru N.', email: 'hikaru@stream.com', role: 'user', status: 'active' },
    { id: 3, name: 'Hans N.', email: 'hans@drama.com', role: 'user', status: 'banned' },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h2>User Management</h2>
        <button className="btn-primary" style={{ padding: '0.5rem 1rem', fontSize: '0.875rem' }}>Invite User</button>
      </div>

      <div className="data-table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Role</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map(user => (
              <tr key={user.id}>
                <td style={{ fontWeight: 600 }}>{user.name}</td>
                <td>{user.email}</td>
                <td>
                  <span className={`badge ${user.role === 'admin' ? 'badge-admin' : ''}`}>
                    {user.role}
                  </span>
                </td>
                <td>
                  <span className={`badge ${user.status === 'active' ? 'badge-active' : 'badge-banned'}`}>
                    {user.status}
                  </span>
                </td>
                <td>
                  <button className="btn-secondary" style={{ padding: '0.25rem 0.75rem', fontSize: '0.75rem' }}>Edit</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
