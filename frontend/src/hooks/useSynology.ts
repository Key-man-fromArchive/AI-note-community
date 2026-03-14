import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/lib/api'
import type { NsxImportStatus, SynologySyncStatus } from '@/types/synology'

export function useNsxImportStatus() {
  return useQuery({
    queryKey: ['nsx-status'],
    queryFn: () => apiClient.get<NsxImportStatus>('/nsx/status'),
  })
}

export function useSynologySyncStatus() {
  return useQuery({
    queryKey: ['synology-status'],
    queryFn: () => apiClient.get<SynologySyncStatus>('/synology/status'),
  })
}

export function useNsxImport() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData()
      formData.append('archive', file)
      return apiClient.postForm<NsxImportStatus>('/nsx/import', formData)
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['nsx-status'] })
      await queryClient.invalidateQueries({ queryKey: ['notes'] })
      await queryClient.invalidateQueries({ queryKey: ['notebooks'] })
      await queryClient.invalidateQueries({ queryKey: ['search-index'] })
      await queryClient.invalidateQueries({ queryKey: ['graph'] })
    },
  })
}

export function useSynologyPull() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => apiClient.post<SynologySyncStatus>('/synology/pull', {}),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['synology-status'] })
      await queryClient.invalidateQueries({ queryKey: ['notes'] })
      await queryClient.invalidateQueries({ queryKey: ['notebooks'] })
      await queryClient.invalidateQueries({ queryKey: ['search-index'] })
      await queryClient.invalidateQueries({ queryKey: ['graph'] })
    },
  })
}
