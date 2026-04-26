import { Routes, Route, Link } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import { ProtectedRoute } from './components/ProtectedRoute'
import { Login } from './components/Login'
import { AdminLayout } from './components/admin/AdminLayout'
import { ManageUsers } from './components/admin/ManageUsers'
import { ManageCommunities } from './components/admin/ManageCommunities'
import { ManageTournaments } from './components/admin/ManageTournaments'
import { PlayerLayout } from './components/player/PlayerLayout'
import { PlayerOverview } from './components/player/PlayerOverview'
import { PlayerCommunities } from './components/player/PlayerCommunities'
import { PlayerTournaments } from './components/player/PlayerTournaments'
import { PlayerMatches } from './components/player/PlayerMatches'
import { Navigate } from 'react-router-dom'

function Navbar() {
  const { user, logout } = useAuth();

  return (
    <nav className="glass-panel" style={{ 
      position: 'fixed', top: 0, width: '100%', zIndex: 100, 
      borderRadius: 0, borderTop: 0, borderLeft: 0, borderRight: 0, 
      padding: '1rem 2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' 
    }}>
      <h2 className="text-gradient" style={{ margin: 0, fontSize: '1.5rem', letterSpacing: '-0.5px' }}>Chesspunk</h2>
      <div style={{ display: 'flex', gap: '2rem', alignItems: 'center' }}>
        <Link to="/" style={{ color: 'var(--text-primary)', textDecoration: 'none', fontWeight: 600 }}>Home</Link>
        <Link to="/competitions" style={{ color: 'var(--text-primary)', textDecoration: 'none', fontWeight: 600 }}>Tournaments</Link>
        {user && (
          <Link to="/dashboard" style={{ color: 'var(--text-primary)', textDecoration: 'none', fontWeight: 600 }}>Dashboard</Link>
        )}
        {user?.role === 'admin' && (
          <Link to="/admin" style={{ color: 'var(--accent-primary)', textDecoration: 'none', fontWeight: 600 }}>Admin Panel</Link>
        )}
      </div>
      <div>
        {user ? (
          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
            <span style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>{user.name}</span>
            <button className="btn-secondary" onClick={logout}>Sign Out</button>
          </div>
        ) : (
          <Link to="/login" className="btn-secondary" style={{ textDecoration: 'none' }}>Sign In</Link>
        )}
      </div>
    </nav>
  )
}

function Home() {
  return (
    <div className="container page-wrapper animate-in">
      <div style={{ textAlign: 'center', padding: '6rem 0' }}>
        <h1 className="text-gradient" style={{ marginBottom: '1.5rem' }}>Master The Board.</h1>
        <p style={{ maxWidth: '600px', margin: '0 auto 3rem auto' }}>
          Connect with Grandmasters, join elite competitions, and secure your place on the global serverless leaderboard natively driven by Lambda architectures.
        </p>
        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
          <button className="btn-primary">Join a Tournament</button>
          <button className="btn-secondary">Explore Community</button>
        </div>
      </div>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '2rem', marginTop: '4rem' }}>
        <div className="glass-panel">
          <h3 className="text-gradient">Serverless Scaling</h3>
          <p>Powered completely natively via AWS API Gateway and Lambda functions guaranteeing limitless horizontal scalability.</p>
        </div>
        <div className="glass-panel">
          <h3 className="text-gradient">Cognito Guarded</h3>
          <p>Secure identity token layers enforcing strict cryptographic user management protocols across all competitive features.</p>
        </div>
      </div>
    </div>
  )
}

function Competitions() {
  return (
    <div className="container page-wrapper animate-in">
      <h2 style={{ marginBottom: '2rem', fontSize: '2.5rem' }}>Active Competitions</h2>
      <div className="glass-panel" style={{ borderLeft: '4px solid var(--accent-primary)' }}>
        <h3 style={{ marginBottom: '0.5rem' }}>Grandmaster Elite S4</h3>
        <p style={{ margin: 0 }}>API Data mapping will be pulled directly via API Gateway CloudFront Distributions natively...</p>
      </div>
    </div>
  )
}

function App() {
  return (
    <div className="app">
      <Navbar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/competitions" element={<Competitions />} />
        <Route path="/login" element={<Login />} />
        <Route path="/dashboard" element={
          <ProtectedRoute>
            <PlayerLayout />
          </ProtectedRoute>
        }>
          <Route index element={<Navigate to="overview" replace />} />
          <Route path="overview" element={<PlayerOverview />} />
          <Route path="matches" element={<PlayerMatches />} />
          <Route path="tournaments" element={<PlayerTournaments />} />
          <Route path="communities" element={<PlayerCommunities />} />
        </Route>
        <Route path="/admin" element={
          <ProtectedRoute requireAdmin={true}>
            <AdminLayout />
          </ProtectedRoute>
        }>
          <Route index element={<Navigate to="users" replace />} />
          <Route path="users" element={<ManageUsers />} />
          <Route path="communities" element={<ManageCommunities />} />
          <Route path="tournaments" element={<ManageTournaments />} />
        </Route>
      </Routes>
    </div>
  )
}

export default App
