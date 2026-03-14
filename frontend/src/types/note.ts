export interface NoteListItem {
  note_id: string
  title: string
  snippet?: string
  notebook: string | null
  created_at: string | null
  updated_at: string | null
  tags: string[]
}

export interface Note {
  note_id: string
  title: string
  content: string
  notebook: string | null
  created_at: string | null
  updated_at: string | null
  tags: string[]
}

export interface NotesResponse {
  items: NoteListItem[]
  total: number
  offset: number
  limit: number
}

export interface Notebook {
  id: number
  name: string
  description: string | null
  category: string | null
  note_count: number
}

export interface NotebooksResponse {
  items: Notebook[]
  total: number
}
