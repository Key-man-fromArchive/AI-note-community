import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useCreateNote, useNotes } from '@/hooks/useNotes'
import { useNote, useSaveNote } from '@/hooks/useNote'
import { useNotebooks } from '@/hooks/useNotebooks'

export default function Notes() {
  const [searchParams, setSearchParams] = useSearchParams()
  const selectedId = searchParams.get('note')
  const [query, setQuery] = useState('')
  const notesQuery = useNotes(query)
  const createNote = useCreateNote()
  const saveNote = useSaveNote()
  const notebooks = useNotebooks()
  const noteQuery = useNote(selectedId)
  const [draftTitle, setDraftTitle] = useState('')
  const [draftContent, setDraftContent] = useState('')

  const notes = useMemo(
    () => notesQuery.data?.pages.flatMap(page => page.items) ?? [],
    [notesQuery.data],
  )

  const activeNotebook = notebooks.data?.items[0]?.name ?? 'General'

  const activeNote = noteQuery.data
  const noteKey = activeNote?.note_id ?? ''

  useEffect(() => {
    if (!activeNote || saveNote.isPending) return
    setDraftTitle(activeNote.title)
    setDraftContent(activeNote.content)
  }, [activeNote, saveNote.isPending])

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Notes</h1>
          <p className="muted">Simple community workspace for writing and editing notes.</p>
        </div>
        <button
          className="button"
          onClick={async () => {
            const note = await createNote.mutateAsync({
              title: 'Untitled note',
              content: '',
              notebook: activeNotebook,
            })
            setSearchParams({ note: note.note_id })
          }}
        >
          New note
        </button>
      </div>

      <div className="grid two">
        <section className="card stack">
          <input className="input" value={query} onChange={e => setQuery(e.target.value)} placeholder="Search notes by title or content" />
          <div className="list">
            {notes.map(note => (
              <button
                key={note.note_id}
                className={`list-item ${selectedId === note.note_id ? 'active' : ''}`}
                onClick={() => setSearchParams({ note: note.note_id })}
              >
                <div style={{ fontWeight: 600 }}>{note.title || 'Untitled note'}</div>
                <div className="muted" style={{ fontSize: '0.9rem' }}>{note.notebook || 'No notebook'}</div>
              </button>
            ))}
          </div>
          {notesQuery.hasNextPage ? (
            <button className="button secondary" onClick={() => notesQuery.fetchNextPage()}>
              Load more
            </button>
          ) : null}
        </section>

        <section className="card stack">
          {selectedId && activeNote ? (
            <>
              <input className="input" value={draftTitle} onChange={e => setDraftTitle(e.target.value)} placeholder="Note title" />
              <textarea className="textarea" value={draftContent} onChange={e => setDraftContent(e.target.value)} />
              <div className="row">
                <button
                  className="button"
                  onClick={() => saveNote.mutate({ noteId: noteKey, title: draftTitle, content: draftContent })}
                >
                  Save
                </button>
                <span className="muted">{saveNote.isPending ? 'Saving...' : activeNote.updated_at ?? 'Not saved yet'}</span>
              </div>
            </>
          ) : (
            <div className="muted">Select a note to edit.</div>
          )}
        </section>
      </div>
    </div>
  )
}
