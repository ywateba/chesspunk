import React from 'react';

export const PlayerMatches = () => {
  const matches = [
    { id: 1, opponent: 'Hikaru N.', result: 'Won', date: 'Today, 14:30', change: '+12' },
    { id: 2, opponent: 'Magnus C.', result: 'Lost', date: 'Yesterday', change: '-8' },
    { id: 3, opponent: 'Daniel N.', result: 'Draw', date: '2026-04-24', change: '+0' },
  ];

  return (
    <div>
      <h2 style={{ marginBottom: '2rem' }}>Match History</h2>

      <div className="data-table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th>Opponent</th>
              <th>Result</th>
              <th>Date</th>
              <th>Rating Change</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {matches.map(m => (
              <tr key={m.id}>
                <td style={{ fontWeight: 600 }}>{m.opponent}</td>
                <td>
                  <span className={`badge ${m.result === 'Won' ? 'badge-active' : m.result === 'Lost' ? 'badge-banned' : ''}`} style={m.result === 'Draw' ? { background: 'rgba(255,255,255,0.1)', color: 'white' } : {}}>
                    {m.result}
                  </span>
                </td>
                <td>{m.date}</td>
                <td style={{ color: m.change.startsWith('+') && m.change !== '+0' ? '#34d399' : m.change.startsWith('-') ? '#f87171' : 'var(--text-secondary)' }}>
                  {m.change}
                </td>
                <td>
                  <button className="btn-secondary" style={{ padding: '0.25rem 0.75rem', fontSize: '0.75rem' }}>Analyze Game</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
