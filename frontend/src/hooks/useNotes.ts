import { useInfiniteQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/lib/api'
import type { Note, NotesResponse } from '@/types/note'

export function useNotes(search?: string) {
  return useInfiniteQuery({
    queryKey: ['notes', search ?? ''],
    queryFn: ({ pageParam = 0 }) => {
      const params = new URLSearchParams({
        offset: String(pageParam),
        limit: '20',
      })
      if (search) params.set('search', search)
      return apiClient.get<NotesResponse>(`/notes?${params.toString()}`)
    },
    initialPageParam: 0,
    getNextPageParam: lastPage => {
      const nextOffset = lastPage.offset + lastPage.limit
      return nextOffset < lastPage.total ? nextOffset : undefined
    },
  })
}

export function useCreateNote() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: { title: string; content: string; notebook: string }) =>
      apiClient.post<Note>('/notes', payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notes'] })
    },
  })
}
