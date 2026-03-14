export interface BackupSnapshot {
  id: number
  snapshot_id: string
  snapshot_type: 'full' | 'incremental'
  status: 'pending' | 'running' | 'completed' | 'failed' | 'uploading' | 'uploaded'
  encrypted: boolean
  total_size_bytes: number
  created_at: string
  completed_at: string | null
  error_message: string | null
}

export interface SchedulerStatus {
  running: boolean
  backup_enabled: boolean
  next_full_at: string | null
  next_incremental_at: string | null
  last_snapshot_at: string | null
}
