import React from 'react';

export const PlayerTournaments = () => {
  const tournaments = [
    { id: 1, name: 'Global Serverless Open', date: '2026-05-15', status: 'Registered' },
    { id: 2, name: 'Weekly Blitz Arena', date: '2026-04-20', status: 'Placed 4th' },
  ];

  return (
    <div>
      <h2 style={{ marginBottom: '2rem' }}>My Tournaments</h2>

      <div className="data-table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th>Tournament</th>
              <th>Date</th>
              <th>Status / Result</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {tournaments.map(t => (
              <tr key={t.id}>
                <td style={{ fontWeight: 600 }}>{t.name}</td>
                <td>{t.date}</td>
                <td>
                  <span className={`badge ${t.status === 'Registered' ? 'badge-active' : ''}`}>
                    {t.status}
                  </span>
                </td>
                <td>
                  <button className="btn-secondary" style={{ padding: '0.25rem 0.75rem', fontSize: '0.75rem' }}>View Details</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
