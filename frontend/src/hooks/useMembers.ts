import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/lib/api'

export interface Member {
  id: number
  email: string
  name: string
  role: string
  accepted_at: string | null
  is_pending: boolean
}

interface MemberListResponse {
  members: Member[]
  total: number
}

export function useMembers() {
  const queryClient = useQueryClient()
  const query = useQuery({
    queryKey: ['members'],
    queryFn: () => apiClient.get<MemberListResponse>('/members'),
  })

  const invite = useMutation({
    mutationFn: (payload: { email: string; role: string }) => apiClient.post('/members/invite', payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['members'] }),
  })

  const updateRole = useMutation({
    mutationFn: (payload: { memberId: number; role: string }) =>
      apiClient.put(`/members/${payload.memberId}/role`, { role: payload.role }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['members'] }),
  })

  const remove = useMutation({
    mutationFn: (memberId: number) => apiClient.delete(`/members/${memberId}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['members'] }),
  })

  return {
    members: query.data?.members ?? [],
    total: query.data?.total ?? 0,
    isLoading: query.isLoading,
    invite,
    updateRole,
    remove,
  }
}
