import { useState } from 'react'
import { useNsxImport, useNsxImportStatus, useSynologyPull, useSynologySyncStatus } from '@/hooks/useSynology'
import { getApiErrorMessage } from '@/lib/api'
import { useSearchIndex } from '@/hooks/useSearchIndex'
import { useSchedulerStatus, useSnapshotActions, useSnapshots } from '@/hooks/useSnapshots'

export default function Settings() {
  const [selectedArchive, setSelectedArchive] = useState<File | null>(null)
  const index = useSearchIndex()
  const snapshots = useSnapshots()
  const scheduler = useSchedulerStatus()
  const actions = useSnapshotActions()
  const nsxStatus = useNsxImportStatus()
  const nsxImport = useNsxImport()
  const synologyStatus = useSynologySyncStatus()
  const synologyPull = useSynologyPull()

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

        <section className="card stack">
          <h2>NSX import</h2>
          <div className="muted">Status: {nsxStatus.data?.status ?? 'idle'}</div>
          <div className="muted">Last archive: {nsxStatus.data?.filename ?? 'n/a'}</div>
          <div className="muted">
            Imported notes: {nsxStatus.data?.notes_added ?? 0} new / {nsxStatus.data?.notes_updated ?? 0} updated
          </div>
          <div className="muted">Extracted images: {nsxStatus.data?.images_extracted ?? 0}</div>
          <input
            className="input"
            type="file"
            accept=".nsx,.zip,application/zip"
            onChange={event => setSelectedArchive(event.target.files?.[0] ?? null)}
          />
          <button
            className="button"
            disabled={!selectedArchive || nsxImport.isPending}
            onClick={() => {
              if (!selectedArchive) return
              nsxImport.mutate(selectedArchive)
            }}
          >
            {nsxImport.isPending ? 'Importing...' : 'Import NSX archive'}
          </button>
          {nsxImport.error ? (
            <div className="muted">{getApiErrorMessage(nsxImport.error, 'NSX import failed')}</div>
          ) : null}
          {nsxStatus.data?.errors?.length ? (
            <div className="muted">Latest import errors: {nsxStatus.data.errors.join(' | ')}</div>
          ) : null}
        </section>
      </div>

      <section className="card stack">
        <h2>Synology pull-only sync</h2>
        <p className="muted">
          Pull notes from Synology Note Station into AI Note Community without writing back to the NAS.
        </p>
        <div className="muted">Configured: {synologyStatus.data?.configured ? 'yes' : 'no'}</div>
        <div className="muted">Status: {synologyStatus.data?.status ?? 'idle'}</div>
        <div className="muted">Last synced: {synologyStatus.data?.last_synced_at ?? 'n/a'}</div>
        <div className="muted">
          Result: +{synologyStatus.data?.added ?? 0} added / {synologyStatus.data?.updated ?? 0} updated /{' '}
          {synologyStatus.data?.conflicts ?? 0} conflicts / {synologyStatus.data?.remote_missing ?? 0} remote missing
        </div>
        <button
          className="button"
          disabled={synologyPull.isPending || !synologyStatus.data?.configured}
          onClick={() => synologyPull.mutate()}
        >
          {synologyPull.isPending ? 'Pulling...' : 'Run pull sync'}
        </button>
        {!synologyStatus.data?.configured ? (
          <div className="muted">Set `SYNOLOGY_URL`, `SYNOLOGY_USER`, and `SYNOLOGY_PASSWORD` in `.env` first.</div>
        ) : null}
        {synologyPull.error ? (
          <div className="muted">{getApiErrorMessage(synologyPull.error, 'Synology pull failed')}</div>
        ) : null}
      </section>

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
