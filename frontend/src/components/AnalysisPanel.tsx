import { useEffect, useRef, useState } from 'react'
import { api } from '../api/client'
import { pollAnalysisJob } from '../utils/polling'
import { formatDate } from '../utils/format'
import { parseApiError } from '../utils/errors'
import type { ProcessingJob } from '../types/api'
import { Badge, EmptyState, LoadingState, SectionHeading, StatusMessage } from './Common'

export function AnalysisPanel({ datasetId }: { datasetId: number }) {
  const [job, setJob] = useState<ProcessingJob | null>(null)
  const [history, setHistory] = useState<ProcessingJob[]>([])
  const [loading, setLoading] = useState(true)
  const [starting, setStarting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  async function loadHistory() { setLoading(true); try { setHistory(await api.listAnalysisJobs(datasetId)); setError(null) } catch (caught) { setError(parseApiError(caught)) } finally { setLoading(false) } }
  useEffect(() => { abortRef.current?.abort(); void loadHistory(); return () => abortRef.current?.abort() }, [datasetId])

  async function runAnalysis() {
    setStarting(true); setError(null); abortRef.current?.abort(); const controller = new AbortController(); abortRef.current = controller
    try { const created = await api.createAnalysisJob(datasetId); setJob(created); const finished = await pollAnalysisJob(() => api.getAnalysisJob(datasetId, created.id), { signal: controller.signal }); setJob(finished); await loadHistory() } catch (caught) { if (caught instanceof DOMException && caught.name === 'AbortError') return; setError(parseApiError(caught)) } finally { setStarting(false) }
  }

  return (
    <div className="analysis-layout">
      <section className="panel">
        <SectionHeading title="Dataset analysis" detail="Save a snapshot of this dataset's profile and quality checks." />
        <div className="analysis-action">
          <button className="button button-primary" type="button" onClick={() => void runAnalysis()} disabled={starting} aria-busy={starting}>
            {starting && <span className="spinner" aria-hidden="true" />}
            {starting ? 'Processing...' : 'Run dataset analysis'}
          </button>
          <p className="job-context">Use a saved analysis to generate insight reports.</p>
        </div>
        {error && <StatusMessage title="Analysis request failed" detail={error} tone="error" />}
        <div aria-live="polite">
          {job && <JobCard job={job} />}
        </div>
      </section>
      <section className="panel" aria-busy={loading}>
        <SectionHeading title="Analysis history" detail="Recent runs and their status, newest first." />
        {loading ? <LoadingState label="Loading job history..." /> : history.length ? (
          <ul className="history-list">
            {history.map((item) => <li key={item.id}><JobCard job={item} compact /></li>)}
          </ul>
        ) : <EmptyState title="No analysis jobs yet" detail="Run your first analysis to save a snapshot and track its progress here." />}
      </section>
    </div>
  )
}

const jobTitles: Record<ProcessingJob['status'], string> = {
  queued: 'Waiting to start',
  running: 'Analysis running',
  retrying: 'Retrying analysis',
  succeeded: 'Analysis complete',
  failed: 'Analysis failed',
}

const jobDescriptions: Record<ProcessingJob['status'], string> = {
  queued: 'Waiting for processing to begin.',
  running: 'Checking the dataset and creating an analysis snapshot.',
  retrying: 'Another attempt is scheduled automatically.',
  succeeded: 'The analysis snapshot is saved and ready for insight generation.',
  failed: 'The analysis could not finish. You can start another run.',
}

function JobCard({ job, compact = false }: { job: ProcessingJob; compact?: boolean }) {
  return (
    <article className={`job-card ${compact ? 'is-compact' : ''}`} aria-label={`Analysis job ${job.id}`}>
      <div className="job-header">
        <div>
          <span className="job-id">Job #{String(job.id).padStart(4, '0')}</span>
          <h3>{jobTitles[job.status]}</h3>
        </div>
        <Badge value={job.status} tone={job.status} />
      </div>
      {!compact && <p className="job-status-note">{jobDescriptions[job.status]}</p>}
      <dl className="job-details">
        <div><dt>Created</dt><dd><JobDate value={job.created_at} /></dd></div>
        <div><dt>Started</dt><dd><JobDate value={job.started_at} /></dd></div>
        <div><dt>Finished</dt><dd><JobDate value={job.finished_at} /></dd></div>
        <div><dt>Attempts</dt><dd>{job.attempt_count}</dd></div>
        {job.analysis_id && <div><dt>Saved analysis</dt><dd>#{job.analysis_id}</dd></div>}
      </dl>
      {job.error_message && <StatusMessage title={job.status === 'failed' ? 'Analysis error' : 'Processing update'} detail={job.error_message} tone={job.status === 'failed' ? 'error' : 'neutral'} />}
    </article>
  )
}

function JobDate({ value }: { value: string | null }) {
  return value ? <time dateTime={value}>{formatDate(value)}</time> : <>Not recorded</>
}
