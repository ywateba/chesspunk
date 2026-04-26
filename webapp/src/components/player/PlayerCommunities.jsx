import React from 'react';

export const PlayerCommunities = () => {
  const communities = [
    { id: 1, name: 'Bullet Chess Elite', role: 'Member', members: 1250 },
    { id: 2, name: 'Scandinavian Defense Fans', role: 'Admin', members: 85 },
  ];

  return (
    <div>
      <h2 style={{ marginBottom: '2rem' }}>My Communities</h2>

      <div className="data-table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th>Community Name</th>
              <th>My Role</th>
              <th>Total Members</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {communities.map(c => (
              <tr key={c.id}>
                <td style={{ fontWeight: 600 }}>{c.name}</td>
                <td>
                  <span className={`badge ${c.role === 'Admin' ? 'badge-admin' : 'badge-active'}`}>
                    {c.role}
                  </span>
                </td>
                <td>{c.members}</td>
                <td>
                  <button className="btn-secondary" style={{ padding: '0.25rem 0.75rem', fontSize: '0.75rem' }}>Enter Lobby</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
