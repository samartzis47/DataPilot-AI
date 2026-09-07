import { describe, expect, it, vi } from 'vitest'
import { extractApiError } from './errors'
import { pollAnalysisJob } from './polling'
import { validateCsvFile } from './validation'
import type { ProcessingJob } from '../types/api'

describe('frontend utilities', () => {
  it('validates CSV files', () => {
    expect(validateCsvFile(new File(['a,b'], 'data.csv', { type: 'text/csv' }))).toBeNull()
    expect(validateCsvFile(new File(['x'], 'notes.txt', { type: 'text/plain' }))).toBe('Only CSV files can be uploaded.')
  })

  it('parses FastAPI detail errors', async () => {
    const response = new Response(JSON.stringify({ detail: 'Dataset not found' }), { status: 404, statusText: 'Not Found' })
    await expect(extractApiError(response)).resolves.toBe('Dataset not found')
  })

  it('polls an analysis job until it succeeds', async () => {
    vi.useFakeTimers()
    const queued: ProcessingJob = { id: 1, dataset_id: 2, analysis_id: null, job_type: 'dataset_profile', status: 'queued', task_id: 'task', attempt_count: 0, error_message: null, created_at: '', started_at: null, finished_at: null }
    const succeeded: ProcessingJob = { ...queued, status: 'succeeded', analysis_id: 9 }
    const fetchJob = vi.fn().mockResolvedValueOnce(queued).mockResolvedValueOnce(succeeded)
    const promise = pollAnalysisJob(fetchJob, { intervalMs: 10 })
    await vi.advanceTimersByTimeAsync(10)
    await expect(promise).resolves.toMatchObject({ status: 'succeeded', analysis_id: 9 })
    expect(fetchJob).toHaveBeenCalledTimes(2)
    vi.useRealTimers()
  })
})
