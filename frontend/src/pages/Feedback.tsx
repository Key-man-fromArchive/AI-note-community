import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { apiClient, getApiErrorMessage } from '@/lib/api'
import { useFeedbackConfig, useFeedbackList, useSubmitFeedback } from '@/hooks/useFeedback'
import type { FeedbackItem, FeedbackScreenshot } from '@/types/feedback'

const categories = [
  { value: 'ux', label: 'UI/UX' },
  { value: 'search', label: 'Search' },
  { value: 'notes', label: 'Notes' },
  { value: 'backup', label: 'Backup' },
  { value: 'members', label: 'Members' },
  { value: 'graph', label: 'Graph' },
]

const priorities = [
  { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' },
  { value: 'high', label: 'High' },
]

interface DraftScreenshot {
  name: string
  dataUrl: string
}

function syncLabel(item: FeedbackItem) {
  switch (item.github_sync_status) {
    case 'created':
      return 'GitHub issue created'
    case 'failed':
      return 'GitHub sync failed'
    case 'disabled':
      return 'Saved locally only'
    case 'pending':
      return 'Syncing to GitHub'
    default:
      return 'Saved in workspace inbox'
  }
}

function ScreenshotPreview({
  screenshot,
  fallbackAlt,
}: {
  screenshot: FeedbackScreenshot
  fallbackAlt: string
}) {
  const [src, setSrc] = useState<string | null>(null)

  useEffect(() => {
    let objectUrl: string | null = null
    let cancelled = false

    const load = async () => {
      try {
        const blob = await apiClient.getBlob(screenshot.asset_url)
        if (cancelled) return
        objectUrl = URL.createObjectURL(blob)
        setSrc(objectUrl)
      } catch {
        if (!cancelled) {
          setSrc(null)
        }
      }
    }

    load()

    return () => {
      cancelled = true
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl)
      }
    }
  }, [screenshot.asset_url])

  if (!src) {
    return <div className="screenshot-placeholder">Loading screenshot...</div>
  }

  return (
    <a className="screenshot-link" href={src} rel="noreferrer" target="_blank">
      <img className="feedback-screenshot" src={src} alt={screenshot.original_name ?? fallbackAlt} />
    </a>
  )
}

function ScreenshotGallery({ item }: { item: FeedbackItem }) {
  if (item.screenshots.length === 0) {
    return null
  }

  return (
    <div className="screenshot-grid">
      {item.screenshots.map(screenshot => (
        <ScreenshotPreview
          key={screenshot.asset_name}
          screenshot={screenshot}
          fallbackAlt={item.title}
        />
      ))}
    </div>
  )
}

export default function Feedback() {
  const { user } = useAuth()
  const feedbackConfig = useFeedbackConfig()
  const feedbackList = useFeedbackList()
  const submitFeedback = useSubmitFeedback()
  const [title, setTitle] = useState('')
  const [category, setCategory] = useState('ux')
  const [priority, setPriority] = useState('medium')
  const [page, setPage] = useState('/feedback')
  const [message, setMessage] = useState('')
  const [email, setEmail] = useState(user?.email ?? '')
  const [sendToGitHub, setSendToGitHub] = useState(true)
  const [draftScreenshots, setDraftScreenshots] = useState<DraftScreenshot[]>([])
  const [error, setError] = useState('')
  const [submitted, setSubmitted] = useState<FeedbackItem | null>(null)

  const githubEnabled = feedbackConfig.data?.github_enabled ?? false
  const recentItems = feedbackList.data?.items ?? []
  const workspaceScope = feedbackList.data?.view_scope === 'workspace'

  const submissionHint = useMemo(() => {
    if (githubEnabled) {
      return `GitHub issue sync is connected to ${feedbackConfig.data?.github_repo}.`
    }
    return 'Feedback is still stored locally even when GitHub sync is not configured.'
  }, [feedbackConfig.data?.github_repo, githubEnabled])

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setError('')

    try {
      const result = await submitFeedback.mutateAsync({
        title,
        category,
        priority,
        page,
        message,
        email: email || undefined,
        create_github_issue: sendToGitHub,
        screenshot_data_urls: draftScreenshots.map(item => item.dataUrl),
        screenshot_names: draftScreenshots.map(item => item.name),
      })
      setSubmitted(result)
      setTitle('')
      setMessage('')
      setPage('/feedback')
      setDraftScreenshots([])
    } catch (submitError) {
      setError(getApiErrorMessage(submitError, 'Feedback submission failed'))
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Feedback Hub</h1>
          <p className="muted">Community version quality improves fastest when users can report friction immediately.</p>
        </div>
        <div className="card">
          <div className="kicker">Routing</div>
          <div style={{ fontWeight: 700 }}>{githubEnabled ? 'GitHub connected' : 'Workspace inbox only'}</div>
          <div className="muted" style={{ fontSize: '0.9rem' }}>{submissionHint}</div>
        </div>
      </div>

      <div className="hero-grid">
        <section className="card hero-accent stack">
          <div className="kicker">Why this matters</div>
          <h2 style={{ margin: 0 }}>Feedback should feel immediate, visible, and actionable.</h2>
          <p className="muted" style={{ margin: 0 }}>
            Use this page to report UX friction, missing actions, confusing results, or anything that blocks trust in the community edition.
          </p>
          <div className="detail-grid">
            <div className="detail-card">
              <div className="kicker">Best reports</div>
              <div>Tell us what page you were on, what you expected, and what felt confusing.</div>
            </div>
            <div className="detail-card">
              <div className="kicker">Fastest path</div>
              <div>When GitHub sync is enabled, feedback can become an issue without copy-paste.</div>
            </div>
          </div>
        </section>

        <section className="card stack">
          <div>
            <div className="kicker">Visibility</div>
            <h2 style={{ margin: '4px 0 0' }}>{workspaceScope ? 'Workspace inbox' : 'My submissions'}</h2>
          </div>
          <div className="detail-grid">
            <div className="detail-card">
              <div className="kicker">Submissions</div>
              <div style={{ fontSize: '1.6rem', fontWeight: 700 }}>{feedbackList.data?.total ?? 0}</div>
            </div>
            <div className="detail-card">
              <div className="kicker">GitHub labels</div>
              <div className="badge-row">
                {(feedbackConfig.data?.default_labels ?? []).map(label => (
                  <span key={label} className="badge subtle">{label}</span>
                ))}
              </div>
            </div>
          </div>
        </section>
      </div>

      <div className="grid two-wide">
        <section className="card stack">
          <div>
            <h2 style={{ marginBottom: 4 }}>Send feedback</h2>
            <p className="muted" style={{ margin: 0 }}>Keep it concrete. The clearer the report, the better the fix.</p>
          </div>
          {submitted ? (
            <div className="banner success">
              <div style={{ fontWeight: 700 }}>{submitted.feedback_id} received</div>
              <div>{syncLabel(submitted)}</div>
              {submitted.screenshots.length > 0 ? <div>{submitted.screenshots.length} screenshot(s) attached</div> : null}
              {submitted.github_issue_url ? (
                <a href={submitted.github_issue_url} target="_blank" rel="noreferrer">
                  Open GitHub issue #{submitted.github_issue_number}
                </a>
              ) : null}
            </div>
          ) : null}
          {error ? <div className="banner error">{error}</div> : null}
          <form className="stack" onSubmit={handleSubmit}>
            <label className="form-label">
              <span>Short title</span>
              <input className="input" value={title} onChange={event => setTitle(event.target.value)} placeholder="Search results need clearer reasoning" />
            </label>
            <div className="detail-grid">
              <label className="form-label">
                <span>Category</span>
                <select className="select" value={category} onChange={event => setCategory(event.target.value)}>
                  {categories.map(option => (
                    <option key={option.value} value={option.value}>{option.label}</option>
                  ))}
                </select>
              </label>
              <label className="form-label">
                <span>Priority</span>
                <select className="select" value={priority} onChange={event => setPriority(event.target.value)}>
                  {priorities.map(option => (
                    <option key={option.value} value={option.value}>{option.label}</option>
                  ))}
                </select>
              </label>
            </div>
            <label className="form-label">
              <span>Page or route</span>
              <input className="input" value={page} onChange={event => setPage(event.target.value)} placeholder="/search" />
            </label>
            <label className="form-label">
              <span>What happened?</span>
              <textarea
                className="textarea textarea-large"
                value={message}
                onChange={event => setMessage(event.target.value)}
                placeholder="Explain what you expected, what felt unclear, and what would make the experience better."
              />
            </label>
            <label className="form-label">
              <span>Follow-up email</span>
              <input className="input" value={email} onChange={event => setEmail(event.target.value)} placeholder="you@example.com" />
            </label>
            <label className="form-label">
              <span>Screenshots</span>
              <input
                accept="image/png,image/jpeg,image/webp"
                className="input"
                multiple
                type="file"
                onChange={async event => {
                  const files = Array.from(event.target.files ?? [])
                  if (files.length === 0) {
                    return
                  }
                  if (draftScreenshots.length + files.length > 3) {
                    setError('You can attach up to 3 screenshots')
                    event.target.value = ''
                    return
                  }
                  if (files.some(file => file.size > 4 * 1024 * 1024)) {
                    setError('Each screenshot must be 4 MB or smaller')
                    event.target.value = ''
                    return
                  }

                  setError('')
                  const loaded = await Promise.all(
                    files.map(
                      file =>
                        new Promise<DraftScreenshot>((resolve, reject) => {
                          const reader = new FileReader()
                          reader.onload = () => resolve({ name: file.name, dataUrl: String(reader.result) })
                          reader.onerror = () => reject(new Error('file_read_failed'))
                          reader.readAsDataURL(file)
                        }),
                    ),
                  )
                  setDraftScreenshots(current => [...current, ...loaded].slice(0, 3))
                  event.target.value = ''
                }}
              />
            </label>
            <div className="muted" style={{ fontSize: '0.9rem' }}>
              {draftScreenshots.length} / 3 attached
            </div>
            {draftScreenshots.length > 0 ? (
              <div className="screenshot-grid">
                {draftScreenshots.map((screenshot, index) => (
                  <div key={`${screenshot.name}-${index}`} className="stack" style={{ gap: 8 }}>
                    <img className="feedback-screenshot draft" src={screenshot.dataUrl} alt={screenshot.name} />
                    <div className="muted" style={{ fontSize: '0.9rem' }}>{screenshot.name}</div>
                    <button
                      className="button secondary"
                      onClick={() => {
                        setDraftScreenshots(current => current.filter((_, currentIndex) => currentIndex !== index))
                      }}
                      type="button"
                    >
                      Remove screenshot
                    </button>
                  </div>
                ))}
              </div>
            ) : null}
            <label className="checkbox-row">
              <input
                checked={sendToGitHub}
                disabled={!githubEnabled}
                onChange={event => setSendToGitHub(event.target.checked)}
                type="checkbox"
              />
              <span>{githubEnabled ? 'Also create a GitHub issue immediately' : 'GitHub sync is currently unavailable'}</span>
            </label>
            <button
              className="button"
              disabled={submitFeedback.isPending || title.trim().length < 4 || message.trim().length < 12}
              type="submit"
            >
              {submitFeedback.isPending ? 'Sending feedback...' : 'Submit feedback'}
            </button>
          </form>
        </section>

        <section className="card stack">
          <div>
            <h2 style={{ marginBottom: 4 }}>Recent submissions</h2>
            <p className="muted" style={{ margin: 0 }}>
              {workspaceScope
                ? 'Owners and admins can review the full workspace inbox here.'
                : 'You can track what you already submitted without leaving the app.'}
            </p>
          </div>

          {feedbackList.isLoading ? <div className="banner info">Loading recent feedback…</div> : null}

          {!feedbackList.isLoading && recentItems.length === 0 ? (
            <div className="empty-state">
              <div style={{ fontWeight: 700 }}>No feedback yet</div>
              <div className="muted">The first submission sets the tone for the community roadmap.</div>
            </div>
          ) : null}

          <div className="list">
            {recentItems.map(item => (
              <article key={item.feedback_id} className="list-item feedback-item">
                <div className="row" style={{ justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div className="stack" style={{ gap: 6 }}>
                    <div style={{ fontWeight: 700 }}>{item.title}</div>
                    <div className="muted" style={{ fontSize: '0.9rem' }}>{item.message}</div>
                  </div>
                  <span className="badge">{item.feedback_id}</span>
                </div>
                <div className="badge-row">
                  <span className="badge subtle">{item.category}</span>
                  <span className="badge subtle">{item.priority}</span>
                  <span className="badge subtle">{item.page}</span>
                  {item.screenshots.length > 0 ? <span className="badge subtle">{item.screenshots.length} screenshots</span> : null}
                </div>
                <ScreenshotGallery item={item} />
                <div className="muted" style={{ fontSize: '0.9rem' }}>{syncLabel(item)}</div>
                {item.github_issue_url ? (
                  <a href={item.github_issue_url} target="_blank" rel="noreferrer">
                    Open GitHub issue #{item.github_issue_number}
                  </a>
                ) : null}
                {item.github_error ? (
                  <div className="banner warning">{item.github_error}</div>
                ) : null}
              </article>
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}
