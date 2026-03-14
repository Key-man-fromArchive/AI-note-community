import { useState, type FormEvent } from 'react'
import { Navigate, Link } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { getApiErrorMessage } from '@/lib/api'
import { useSetupStatus } from '@/hooks/useSetup'

export default function Login() {
  const setupStatus = useSetupStatus()
  const { login, isAuthenticated } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  if (isAuthenticated) {
    return <Navigate to="/" replace />
  }

  if (setupStatus.data && !setupStatus.data.initialized) {
    return <Navigate to="/setup" replace />
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setError('')
    setIsLoading(true)
    try {
      await login(email, password)
    } catch (loginError) {
      setError(getApiErrorMessage(loginError, 'Login failed'))
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="auth-shell">
      <div className="card auth-card stack">
        <div>
          <h1>AI Note Community</h1>
          <p className="muted">Sign in to your workspace.</p>
        </div>
        <form className="stack" onSubmit={handleSubmit}>
          <input className="input" value={email} onChange={e => setEmail(e.target.value)} placeholder="Email" />
          <input className="input" value={password} onChange={e => setPassword(e.target.value)} placeholder="Password" type="password" />
          {error ? <div className="muted">{error}</div> : null}
          <button className="button" disabled={isLoading || !email || !password} type="submit">
            {isLoading ? 'Signing in...' : 'Sign in'}
          </button>
        </form>
        <div className="muted">
          Need a workspace? <Link to="/signup">Create one</Link>
        </div>
      </div>
    </div>
  )
}
