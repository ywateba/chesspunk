import React from 'react';

export const ManageCommunities = () => {
  const communities = [
    { id: 1, name: 'Bullet Chess Elite', members: 1250, owner: 'Hikaru N.', status: 'approved' },
    { id: 2, name: 'Chess960 Masters', members: 430, owner: 'Magnus C.', status: 'approved' },
    { id: 3, name: 'Engine Cheaters', members: 12, owner: 'Unknown', status: 'pending_review' },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h2>Community Management</h2>
      </div>

      <div className="data-table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th>Community Name</th>
              <th>Owner</th>
              <th>Members</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {communities.map(comm => (
              <tr key={comm.id}>
                <td style={{ fontWeight: 600 }}>{comm.name}</td>
                <td>{comm.owner}</td>
                <td>{comm.members}</td>
                <td>
                  <span className={`badge ${comm.status === 'approved' ? 'badge-active' : 'badge-banned'}`}>
                    {comm.status.replace('_', ' ')}
                  </span>
                </td>
                <td>
                  <button className="btn-secondary" style={{ padding: '0.25rem 0.75rem', fontSize: '0.75rem' }}>Review</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
