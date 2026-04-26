import React from 'react';

export const PlayerOverview = () => {
  return (
    <div>
      <h2 style={{ marginBottom: '2rem' }}>Overview</h2>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem', marginBottom: '3rem' }}>
        <div className="glass-panel" style={{ padding: '1.5rem' }}>
          <h4 style={{ color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>Current Rating</h4>
          <div className="text-gradient" style={{ fontSize: '2.5rem', fontWeight: 800 }}>2450</div>
          <div style={{ color: '#34d399', fontSize: '0.875rem', marginTop: '0.5rem' }}>+15 this week</div>
        </div>
        <div className="glass-panel" style={{ padding: '1.5rem' }}>
          <h4 style={{ color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>Win Rate</h4>
          <div style={{ fontSize: '2.5rem', fontWeight: 800 }}>68%</div>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginTop: '0.5rem' }}>142 Matches</div>
        </div>
        <div className="glass-panel" style={{ padding: '1.5rem' }}>
          <h4 style={{ color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>Tournaments Won</h4>
          <div className="text-gradient" style={{ fontSize: '2.5rem', fontWeight: 800 }}>3</div>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginTop: '0.5rem' }}>Top 5% Globally</div>
        </div>
      </div>

      <div className="glass-panel">
        <h3>Recent Activity</h3>
        <p style={{ margin: 0 }}>You recently joined the <strong>Bullet Chess Elite</strong> community and registered for the <strong>Global Serverless Open</strong>.</p>
      </div>
    </div>
  );
};
