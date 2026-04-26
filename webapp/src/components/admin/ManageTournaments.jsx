import React from 'react';

export const ManageTournaments = () => {
  const tournaments = [
    { id: 1, name: 'Global Serverless Open', date: '2026-05-15', players: 1024, status: 'upcoming' },
    { id: 2, name: 'Lambda Blitz Masters', date: '2026-04-20', players: 512, status: 'completed' },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h2>Tournament Management</h2>
        <button className="btn-primary" style={{ padding: '0.5rem 1rem', fontSize: '0.875rem' }}>+ New Tournament</button>
      </div>

      <div className="data-table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th>Tournament Name</th>
              <th>Date</th>
              <th>Registered Players</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {tournaments.map(t => (
              <tr key={t.id}>
                <td style={{ fontWeight: 600 }}>{t.name}</td>
                <td>{t.date}</td>
                <td>{t.players}</td>
                <td>
                  <span className={`badge ${t.status === 'upcoming' ? 'badge-active' : ''}`}>
                    {t.status}
                  </span>
                </td>
                <td>
                  <button className="btn-secondary" style={{ padding: '0.25rem 0.75rem', fontSize: '0.75rem' }}>Manage</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
