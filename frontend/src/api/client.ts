import { extractApiError } from '../utils/errors'
import type {
  CleanedDataset,
  CleaningRequest,
  Dataset,
  DatasetInsight,
  DatasetProfile,
  ProcessingJob,
} from '../types/api'

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) || '/api'

function apiUrl(path: string): string {
  return `${API_BASE_URL.replace(/\/$/, '')}${path}`
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(apiUrl(path), init)
  if (!response.ok) throw new Error(await extractApiError(response))
  return response.json() as Promise<T>
}

export const api = {
  health: () => request<{ status: string; service: string }>('/health'),
  listDatasets: () => request<Dataset[]>('/datasets'),
  uploadDataset: (file: File) => {
    const body = new FormData()
    body.append('file', file)
    return request<Dataset>('/datasets/upload', { method: 'POST', body })
  },
  getProfile: (datasetId: number) => request<DatasetProfile>(`/datasets/${datasetId}/profile`),
  createAnalysisJob: (datasetId: number) => request<ProcessingJob>(`/datasets/${datasetId}/analysis-jobs`, { method: 'POST' }),
  getAnalysisJob: (datasetId: number, jobId: number) => request<ProcessingJob>(`/datasets/${datasetId}/analysis-jobs/${jobId}`),
  listAnalysisJobs: (datasetId: number) => request<ProcessingJob[]>(`/datasets/${datasetId}/analysis-jobs`),
  createCleaning: (datasetId: number, body: CleaningRequest) => request<CleanedDataset>(`/datasets/${datasetId}/cleanings`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }),
  listCleanings: (datasetId: number) => request<CleanedDataset[]>(`/datasets/${datasetId}/cleanings`),
  downloadCleaningUrl: (datasetId: number, cleaningId: number) => apiUrl(`/datasets/${datasetId}/cleanings/${cleaningId}/download`),
  createInsight: (datasetId: number, provider: 'rules' | 'openai') => request<DatasetInsight>(`/datasets/${datasetId}/insights`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ provider }),
  }),
  listInsights: (datasetId: number) => request<DatasetInsight[]>(`/datasets/${datasetId}/insights`),
}
