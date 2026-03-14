import { useSearchIndex } from '@/hooks/useSearchIndex'
import { useSchedulerStatus, useSnapshotActions, useSnapshots } from '@/hooks/useSnapshots'

export default function Settings() {
  const index = useSearchIndex()
  const snapshots = useSnapshots()
  const scheduler = useSchedulerStatus()
  const actions = useSnapshotActions()

  return (
    <div className="page">
      <div>
        <h1>Backup & Settings</h1>
        <p className="muted">Manage search indexing and snapshot backup history.</p>
      </div>

      <div className="grid two">
        <section className="card stack">
          <h2>Embedding index</h2>
          <div className="muted">Status: {index.status}</div>
          <div className="muted">Indexed: {index.indexedNotes} / {index.totalNotes}</div>
          <div className="muted">Pending: {index.pendingNotes}</div>
          <div className="muted">Stale: {index.staleNotes}</div>
          <button className="button" onClick={() => index.trigger.mutate()}>
            Run indexing
          </button>
        </section>

        <section className="card stack">
          <h2>Snapshot scheduler</h2>
          <div className="muted">Enabled: {scheduler.data?.backup_enabled ? 'yes' : 'no'}</div>
          <div className="muted">Next full: {scheduler.data?.next_full_at ?? 'n/a'}</div>
          <div className="muted">Next incremental: {scheduler.data?.next_incremental_at ?? 'n/a'}</div>
          <div className="row">
            <button className="button" onClick={() => actions.triggerFull.mutate()}>
              Run full backup
            </button>
            <button className="button secondary" onClick={() => actions.triggerIncremental.mutate()}>
              Run incremental
            </button>
          </div>
        </section>
      </div>

      <section className="card stack">
        <h2>Snapshot history</h2>
        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Type</th>
              <th>Status</th>
              <th>Created</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {(snapshots.data?.snapshots ?? []).map(snapshot => (
              <tr key={snapshot.snapshot_id}>
                <td>{snapshot.snapshot_id.slice(0, 12)}</td>
                <td>{snapshot.snapshot_type}</td>
                <td>{snapshot.status}</td>
                <td>{snapshot.created_at}</td>
                <td>
                  <button
                    className="button secondary"
                    disabled={snapshot.status !== 'completed'}
                    onClick={() => actions.restore.mutate(snapshot.snapshot_id)}
                  >
                    Restore
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  )
}
