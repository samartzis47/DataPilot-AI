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

  return <div className="analysis-layout"><section className="panel"><SectionHeading eyebrow="Async processing" title="Dataset analysis" detail="Run a persisted profile through the Celery worker." action={<button className="button button-primary" type="button" onClick={() => void runAnalysis()} disabled={starting}>{starting ? 'Processing...' : 'Run dataset analysis'}</button>} />{error && <StatusMessage title="Analysis request failed" detail={error} tone="error" />}{job && <JobCard job={job} />}</section><section className="panel"><SectionHeading eyebrow="History" title="Analysis jobs" detail="Newest jobs appear first." />{loading ? <LoadingState label="Loading job history..." /> : history.length ? <div className="history-list">{history.map((item) => <JobCard key={item.id} job={item} compact />)}</div> : <EmptyState title="No analysis jobs" detail="Run an analysis to create a persisted snapshot." />}</section></div>
}
function JobCard({ job, compact = false }: { job: ProcessingJob; compact?: boolean }) { return <div className={`job-card ${compact ? 'is-compact' : ''}`}><div className="job-header"><div><span className="job-id">JOB-{String(job.id).padStart(4, '0')}</span><h3>{job.status === 'succeeded' ? 'Analysis complete' : job.status === 'failed' ? 'Analysis failed' : 'Analysis in progress'}</h3></div><Badge value={job.status} tone={job.status} /></div><div className="job-details"><span>Created <strong>{formatDate(job.created_at)}</strong></span><span>Started <strong>{formatDate(job.started_at)}</strong></span><span>Finished <strong>{formatDate(job.finished_at)}</strong></span><span>Attempts <strong>{job.attempt_count}</strong></span>{job.analysis_id && <span>Analysis ID <strong>{job.analysis_id}</strong></span>}</div>{job.error_message && <StatusMessage title="Worker message" detail={job.error_message} tone="error" />}</div>}
