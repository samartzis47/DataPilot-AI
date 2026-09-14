import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { api } from '../api/client'
import type { CleanedDataset, CleaningRequest } from '../types/api'
import { CleaningPanel } from './CleaningPanel'

vi.mock('../api/client', async (importOriginal) => {
  const original = await importOriginal<typeof import('../api/client')>()
  return { ...original, api: { ...original.api, listCleanings: vi.fn(), createCleaning: vi.fn() } }
})

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

const strategies: CleaningRequest[] = [
  { remove_duplicate_rows: true, numeric_missing_strategy: 'median', text_missing_strategy: 'mode', numeric_outlier_strategy: 'clip_iqr' },
  { remove_duplicate_rows: false, numeric_missing_strategy: 'mean', text_missing_strategy: 'keep', numeric_outlier_strategy: 'remove' },
]

describe('CleaningPanel', () => {
  it.each(strategies)('preserves the $numeric_missing_strategy / $text_missing_strategy / $numeric_outlier_strategy cleaning request and download', async (request) => {
    const cleaned: CleanedDataset = {
      id: 9,
      dataset_id: 42,
      original_filename: 'sales_cleaned.csv',
      stored_filename: 'saved-cleaned-sales.csv',
      cleaning_config: request,
      summary: { removed_rows: 2 },
      original_row_count: 10,
      cleaned_row_count: 8,
      created_at: '2026-09-14T10:00:00Z',
    }
    vi.mocked(api.listCleanings).mockResolvedValue([])
    vi.mocked(api.createCleaning).mockResolvedValue(cleaned)

    render(<CleaningPanel datasetId={42} />)
    await screen.findByText('No cleaned copies yet')
    if (request.remove_duplicate_rows) fireEvent.click(screen.getByRole('checkbox', { name: /Remove duplicate rows/ }))
    fireEvent.change(screen.getByRole('combobox', { name: /Numeric missing values/ }), { target: { value: request.numeric_missing_strategy } })
    fireEvent.change(screen.getByRole('combobox', { name: /Text missing values/ }), { target: { value: request.text_missing_strategy } })
    fireEvent.change(screen.getByRole('combobox', { name: /Numeric outliers/ }), { target: { value: request.numeric_outlier_strategy } })
    fireEvent.click(screen.getByRole('button', { name: 'Create cleaned copy' }))

    await waitFor(() => expect(api.createCleaning).toHaveBeenCalledExactlyOnceWith(42, request))
    expect(await screen.findByRole('link', { name: /^Download CSV/ })).toHaveAttribute('href', '/api/datasets/42/cleanings/9/download')
    expect(screen.getByText('Cleaned copy created')).toBeInTheDocument()
  })
})
