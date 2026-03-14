import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { getSchedulerStatus, listSnapshots, restoreSnapshot, triggerFullSnapshot, triggerIncrementalSnapshot } from '@/lib/snapshot-api'

export function useSnapshots() {
  return useQuery({
    queryKey: ['snapshots'],
    queryFn: listSnapshots,
    refetchInterval: 5000,
  })
}

export function useSchedulerStatus() {
  return useQuery({
    queryKey: ['snapshot-scheduler'],
    queryFn: getSchedulerStatus,
    refetchInterval: 30000,
  })
}

export function useSnapshotActions() {
  const queryClient = useQueryClient()
  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['snapshots'] })
    queryClient.invalidateQueries({ queryKey: ['snapshot-scheduler'] })
  }

  return {
    triggerFull: useMutation({ mutationFn: triggerFullSnapshot, onSuccess: invalidate }),
    triggerIncremental: useMutation({ mutationFn: triggerIncrementalSnapshot, onSuccess: invalidate }),
    restore: useMutation({ mutationFn: restoreSnapshot, onSuccess: invalidate }),
  }
}
