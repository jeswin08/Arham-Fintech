import { CheckCircle2, LoaderCircle, Play, Radio, XCircle } from 'lucide-react'

const statusCopy = {
  pending: 'Queued for processing',
  running: 'Pulling from BSE source',
  completed: 'Data pull completed',
  failed: 'Data pull failed',
}

export function IngestionPanel({ job, isPulling, onStart, connectionStatus, actionMessage }) {
  const currentStatus = job?.status
  const StatusIcon = currentStatus === 'completed'
    ? CheckCircle2
    : currentStatus === 'failed'
      ? XCircle
      : LoaderCircle

  return (
    <section className="ingestion-card">
      <div className="ingestion-copy">
        <div className="live-pill"><Radio size={13} /> Data operations</div>
        <h2>Keep your market view current.</h2>
        <p>Start a new exchange pull. Processing continues in the background so your dashboard stays available.</p>
        {currentStatus && (
          <div className={`job-status ${currentStatus}`}>
            <StatusIcon size={16} className={currentStatus === 'running' ? 'spin' : ''} />
            <span>{statusCopy[currentStatus]}</span>
            {job.total_records > 0 && <strong>{job.total_records.toLocaleString('en-IN')} new records</strong>}
          </div>
        )}
        {actionMessage && <p className={`action-message ${actionMessage.type}`}>{actionMessage.text}</p>}
      </div>
      <div className="ingestion-action">
        <button className="primary-button" type="button" onClick={onStart} disabled={isPulling}>
          {isPulling ? <LoaderCircle className="spin" size={17} /> : <Play size={16} fill="currentColor" />}
          {isPulling ? 'Starting...' : 'Start data pull'}
        </button>
        <span className={`connection-note ${connectionStatus}`}>
          <span className="connection-dot" />
          SSE {connectionStatus === 'live'
            ? 'connected'
            : connectionStatus === 'reconnecting'
              ? 'reconnecting'
              : 'unavailable'}
        </span>
      </div>
    </section>
  )
}
