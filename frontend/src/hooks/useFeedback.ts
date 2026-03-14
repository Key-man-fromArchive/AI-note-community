import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/lib/api'
import type { FeedbackConfig, FeedbackItem, FeedbackListResponse } from '@/types/feedback'

interface FeedbackPayload {
  title: string
  category: string
  priority: string
  page: string
  message: string
  email?: string
  create_github_issue: boolean
  screenshot_data_urls?: string[]
  screenshot_names?: string[]
}

export function useFeedbackConfig() {
  return useQuery({
    queryKey: ['feedback-config'],
    queryFn: () => apiClient.get<FeedbackConfig>('/feedback/config'),
  })
}

export function useFeedbackList() {
  return useQuery({
    queryKey: ['feedback-list'],
    queryFn: () => apiClient.get<FeedbackListResponse>('/feedback'),
  })
}

export function useSubmitFeedback() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: FeedbackPayload) => apiClient.post<FeedbackItem>('/feedback', payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['feedback-list'] })
    },
  })
}
