import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useSearch } from '@/hooks/useSearch'

export default function Search() {
  const [query, setQuery] = useState('')
  const search = useSearch(query)

  return (
    <div className="page">
      <div>
        <h1>Embedding Search</h1>
        <p className="muted">Search across note content.</p>
      </div>
      <div className="card stack">
        <input className="input" value={query} onChange={e => setQuery(e.target.value)} placeholder="Ask a question or search by keyword" />
        <div className="list">
          {(search.data?.results ?? []).map(result => (
            <Link key={result.note_id} className="list-item" to={`/?note=${result.note_id}`}>
              <div style={{ fontWeight: 600 }}>{result.title}</div>
              <div className="muted" style={{ fontSize: '0.9rem' }}>{result.snippet}</div>
              <div className="muted" style={{ fontSize: '0.8rem' }}>score {result.score.toFixed(3)}</div>
            </Link>
          ))}
          {query && !search.isLoading && (search.data?.results.length ?? 0) === 0 ? (
            <div className="muted">No results.</div>
          ) : null}
        </div>
      </div>
    </div>
  )
}
