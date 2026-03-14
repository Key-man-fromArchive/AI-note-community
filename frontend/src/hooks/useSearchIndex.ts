import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/lib/api'

interface IndexStatus {
  status: 'idle' | 'indexing' | 'cancelling' | 'cancelled' | 'completed' | 'error'
  total_notes: number
  indexed_notes: number
  pending_notes: number
  stale_notes: number
}

export function useSearchIndex() {
  const queryClient = useQueryClient()
  const query = useQuery({
    queryKey: ['search-index'],
    queryFn: () => apiClient.get<IndexStatus>('/search/index/status'),
    refetchInterval: 5000,
  })

  const trigger = useMutation({
    mutationFn: () => apiClient.post('/search/index', {}),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['search-index'] }),
  })

  return {
    status: query.data?.status ?? 'idle',
    totalNotes: query.data?.total_notes ?? 0,
    indexedNotes: query.data?.indexed_notes ?? 0,
    pendingNotes: query.data?.pending_notes ?? 0,
    staleNotes: query.data?.stale_notes ?? 0,
    isLoading: query.isLoading,
    trigger,
  }
}
