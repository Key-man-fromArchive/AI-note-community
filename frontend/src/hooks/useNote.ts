import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/lib/api'
import type { Note } from '@/types/note'

export function useNote(noteId: string | null) {
  return useQuery({
    queryKey: ['note', noteId],
    queryFn: () => apiClient.get<Note>(`/notes/${noteId}`),
    enabled: !!noteId,
  })
}

export function useSaveNote() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ noteId, title, content }: { noteId: string; title: string; content: string }) =>
      apiClient.put<Note>(`/notes/${noteId}`, { title, content }),
    onSuccess: data => {
      queryClient.invalidateQueries({ queryKey: ['notes'] })
      queryClient.setQueryData(['note', data.note_id], data)
    },
  })
}
