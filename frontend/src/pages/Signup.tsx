import { useState, type FormEvent } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { getApiErrorMessage } from '@/lib/api'
import { useSetupStatus } from '@/hooks/useSetup'

function slugify(value: string) {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 50)
}

export default function Signup() {
  const setupStatus = useSetupStatus()
  const { signup, isAuthenticated } = useAuth()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [orgName, setOrgName] = useState('')
  const [orgSlug, setOrgSlug] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  if (isAuthenticated) {
    return <Navigate to="/" replace />
  }

  const workspaceInitialized = setupStatus.data?.initialized ?? false

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setError('')
    setIsLoading(true)
    try {
      await signup({
        name,
        email,
        password,
        org_name: workspaceInitialized ? undefined : orgName,
        org_slug: workspaceInitialized ? undefined : orgSlug,
      })
    } catch (signupError) {
      setError(getApiErrorMessage(signupError, 'Signup failed'))
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="auth-shell">
      <div className="card auth-card stack">
        <div>
          <h1>{workspaceInitialized ? 'Join workspace' : 'Create workspace'}</h1>
          <p className="muted">
            {workspaceInitialized
              ? 'Use the invited email to activate your member account.'
              : 'Start a self-hosted note workspace for your team.'}
          </p>
        </div>
        <form className="stack" onSubmit={handleSubmit}>
          <input className="input" value={name} onChange={e => setName(e.target.value)} placeholder="Your name" />
          <input className="input" value={email} onChange={e => setEmail(e.target.value)} placeholder="Email" />
          <input className="input" value={password} onChange={e => setPassword(e.target.value)} placeholder="Password" type="password" />
          {!workspaceInitialized ? (
            <>
              <input className="input" value={orgName} onChange={e => {
                setOrgName(e.target.value)
                setOrgSlug(slugify(e.target.value))
              }} placeholder="Organization name" />
              <input className="input" value={orgSlug} onChange={e => setOrgSlug(e.target.value)} placeholder="organization-slug" />
            </>
          ) : null}
          {error ? <div className="muted">{error}</div> : null}
          <button
            className="button"
            disabled={isLoading || !email || !password || (!workspaceInitialized && (!orgName || !orgSlug))}
            type="submit"
          >
            {isLoading ? 'Submitting...' : workspaceInitialized ? 'Join workspace' : 'Create workspace'}
          </button>
        </form>
        <div className="muted">
          Already have an account? <Link to="/login">Sign in</Link>
        </div>
      </div>
    </div>
  )
}
