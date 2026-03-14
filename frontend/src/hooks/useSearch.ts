import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api'

export interface SearchResult {
  note_id: string
  title: string
  snippet: string
  score: number
}

interface SearchResponse {
  results: SearchResult[]
  total: number
}

export function useSearch(query: string) {
  return useQuery({
    queryKey: ['search', query],
    queryFn: () => apiClient.get<SearchResponse>(`/search?q=${encodeURIComponent(query)}&type=search&limit=20&offset=0`),
    enabled: query.trim().length > 0,
  })
}
