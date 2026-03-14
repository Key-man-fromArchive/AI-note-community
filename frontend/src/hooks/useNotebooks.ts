import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api'
import type { NotebooksResponse } from '@/types/note'

export function useNotebooks() {
  return useQuery({
    queryKey: ['notebooks'],
    queryFn: () => apiClient.get<NotebooksResponse>('/notebooks'),
  })
}
