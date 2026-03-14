export interface FeedbackScreenshot {
  asset_name: string
  asset_url: string
  content_type: string
  original_name: string | null
}

export interface FeedbackItem {
  id: number
  feedback_id: string
  title: string
  category: string
  priority: string
  page: string
  message: string
  contact_email: string | null
  submitted_by_user_id: number
  submitted_by_email: string
  submitted_by_name: string
  submitted_by_role: string
  status: string
  created_at: string
  github_sync_status: 'pending' | 'created' | 'failed' | 'disabled' | 'not_requested'
  github_issue_number: number | null
  github_issue_url: string | null
  github_error: string | null
  screenshots: FeedbackScreenshot[]
}

export interface FeedbackConfig {
  github_enabled: boolean
  github_repo: string | null
  default_labels: string[]
}

export interface FeedbackListResponse {
  items: FeedbackItem[]
  total: number
  view_scope: 'workspace' | 'mine'
}
