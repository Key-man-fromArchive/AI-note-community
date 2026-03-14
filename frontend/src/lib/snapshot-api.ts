import { apiClient } from '@/lib/api'
import type { BackupSnapshot, SchedulerStatus } from '@/types/snapshot'

export function listSnapshots() {
  return apiClient.get<{ snapshots: BackupSnapshot[]; total: number }>('/snapshots?skip=0&limit=20')
}

export function triggerFullSnapshot() {
  return apiClient.post('/snapshots/full')
}

export function triggerIncrementalSnapshot() {
  return apiClient.post('/snapshots/incremental')
}

export function restoreSnapshot(snapshotId: string) {
  return apiClient.post(`/snapshots/${snapshotId}/restore`, {})
}

export function getSchedulerStatus() {
  return apiClient.get<SchedulerStatus>('/snapshots/scheduler/status')
}
