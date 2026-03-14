import { useMutation, useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api'

export function useSetupStatus() {
  return useQuery({
    queryKey: ['setup-status'],
    queryFn: () => apiClient.get<{ initialized: boolean }>('/setup/status'),
    retry: false,
  })
}

export function useSetupLanguage() {
  return useMutation({
    mutationFn: (data: { language: string }) => apiClient.post('/setup/language', data),
  })
}

export function useSetupAdmin() {
  return useMutation({
    mutationFn: (data: {
      email: string
      password: string
      password_confirm: string
      name: string
      org_name: string
      org_slug: string
    }) => apiClient.post('/setup/admin', data),
  })
}

export function useSetupAI() {
  return useMutation({
    mutationFn: (data: { providers: Array<{ provider: string; api_key: string }>; test: boolean }) =>
      apiClient.post('/setup/ai', data),
  })
}

export function useSetupComplete() {
  return useMutation({
    mutationFn: () => apiClient.post<{
      access_token: string
      refresh_token: string
      user_id: number
      email: string
      name: string
      org_id: number
      org_slug: string
      role: string
    }>('/setup/complete', {}),
  })
}
