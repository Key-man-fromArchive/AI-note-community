export interface NsxImportStatus {
  status: string
  filename: string | null
  notes_processed: number
  notes_added: number
  notes_updated: number
  images_extracted: number
  errors: string[]
  last_import_at: string | null
}

export interface SynologySyncStatus {
  status: string
  configured: boolean
  last_synced_at: string | null
  added: number
  updated: number
  skipped: number
  remote_missing: number
  conflicts: number
  error: string | null
}
