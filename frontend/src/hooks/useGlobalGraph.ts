import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api'

export interface GraphNode {
  id: number
  label: string
  notebook: string | null
  size: number
}

export interface GraphLink {
  source: number
  target: number
  weight: number
}

interface GraphData {
  nodes: GraphNode[]
  links: GraphLink[]
  total_notes: number
  indexed_notes: number
}

export function useGlobalGraph(limit = 200) {
  return useQuery({
    queryKey: ['graph', limit],
    queryFn: () =>
      apiClient.get<GraphData>(`/graph?limit=${limit}&similarity_threshold=0.75&neighbors_per_note=5&max_edges=0&include_analysis=false`),
  })
}
