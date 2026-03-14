import { useState } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { getApiErrorMessage } from '@/lib/api'
import { useSetupAI, useSetupAdmin, useSetupComplete, useSetupLanguage, useSetupStatus } from '@/hooks/useSetup'

export default function Setup() {
  const { applySession } = useAuth()
  const { data } = useSetupStatus()
  const setupLanguage = useSetupLanguage()
  const setupAdmin = useSetupAdmin()
  const setupAI = useSetupAI()
  const setupComplete = useSetupComplete()
  const [language, setLanguage] = useState('en')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [orgName, setOrgName] = useState('')
  const [orgSlug, setOrgSlug] = useState('')
  const [openaiKey, setOpenaiKey] = useState('')
  const [error, setError] = useState('')
  const [done, setDone] = useState(false)

  if (data?.initialized || done) {
    return <Navigate to="/" replace />
  }

  const handleSetup = async () => {
    setError('')

    try {
      await setupLanguage.mutateAsync({ language })
      await setupAdmin.mutateAsync({
        email,
        password,
        password_confirm: password,
        name,
        org_name: orgName,
        org_slug: orgSlug,
      })
      await setupAI.mutateAsync({
        providers: openaiKey ? [{ provider: 'openai', api_key: openaiKey }] : [],
        test: false,
      })
      const result = await setupComplete.mutateAsync()
      applySession(result)
      setDone(true)
    } catch (setupError) {
      setError(getApiErrorMessage(setupError, 'Setup failed'))
    }
  }

  return (
    <div className="auth-shell">
      <div className="card auth-card stack">
        <h1>Initial setup</h1>
        <select className="select" value={language} onChange={e => setLanguage(e.target.value)}>
          <option value="en">English</option>
          <option value="ko">Korean</option>
        </select>
        <input className="input" value={name} onChange={e => setName(e.target.value)} placeholder="Admin name" />
        <input className="input" value={email} onChange={e => setEmail(e.target.value)} placeholder="Admin email" />
        <input className="input" value={password} onChange={e => setPassword(e.target.value)} placeholder="Admin password" type="password" />
        <input className="input" value={orgName} onChange={e => setOrgName(e.target.value)} placeholder="Organization name" />
        <input className="input" value={orgSlug} onChange={e => setOrgSlug(e.target.value)} placeholder="organization-slug" />
        <input className="input" value={openaiKey} onChange={e => setOpenaiKey(e.target.value)} placeholder="OpenAI API key (optional)" />
        {error ? <div className="muted">{error}</div> : null}
        <button className="button" onClick={handleSetup} disabled={!email || !password || !orgName || !orgSlug}>
          Finish setup
        </button>
      </div>
    </div>
  )
}
