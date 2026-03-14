import { NavLink } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { cn } from '@/lib/utils'

const items = [
  { to: '/', label: 'Notes' },
  { to: '/search', label: 'Search' },
  { to: '/graph', label: 'Graph' },
  { to: '/feedback', label: 'Feedback' },
  { to: '/members', label: 'Members', admin: true },
  { to: '/settings', label: 'Backup & Settings', admin: true },
]

export function Sidebar() {
  const { user, logout } = useAuth()
  const isAdmin = user?.role === 'owner' || user?.role === 'admin'

  return (
    <aside className="sidebar">
      <h1 className="sidebar-title">AI Note Community</h1>
      <p className="sidebar-subtitle">Notes, members, backup, search, graph</p>

      <nav className="nav-list">
        {items
          .filter(item => !item.admin || isAdmin)
          .map(item => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) => cn('nav-link', isActive && 'active')}
            >
              {item.label}
            </NavLink>
          ))}
      </nav>

      <div style={{ marginTop: '24px' }} className="card">
        <div className="stack">
          <div className="feedback-callout">
            <div className="kicker">Community loop</div>
            <div style={{ fontWeight: 700 }}>Feedback is part of the product.</div>
            <div className="muted" style={{ fontSize: '0.9rem' }}>Share friction quickly and route it into the workspace inbox or GitHub.</div>
          </div>
          <div>
            <div style={{ fontWeight: 600 }}>{user?.name || user?.email}</div>
            <div className="muted" style={{ fontSize: '0.9rem' }}>{user?.role}</div>
          </div>
          <button className="button secondary" onClick={logout}>
            Log out
          </button>
        </div>
      </div>
    </aside>
  )
}
