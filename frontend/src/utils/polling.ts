import type { ProcessingJob } from '../types/api'

export async function pollAnalysisJob(
  fetchJob: () => Promise<ProcessingJob>,
  options: { intervalMs?: number; signal?: AbortSignal } = {},
): Promise<ProcessingJob> {
  const intervalMs = options.intervalMs ?? 1500
  let job = await fetchJob()
  while (job.status === 'queued' || job.status === 'running' || job.status === 'retrying') {
    await new Promise<void>((resolve, reject) => {
      const timeout = window.setTimeout(resolve, intervalMs)
      options.signal?.addEventListener('abort', () => {
        window.clearTimeout(timeout)
        reject(new DOMException('Polling aborted', 'AbortError'))
      }, { once: true })
    })
    if (options.signal?.aborted) throw new DOMException('Polling aborted', 'AbortError')
    job = await fetchJob()
  }
  return job
}
