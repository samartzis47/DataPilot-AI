import { act, cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { api } from '../api/client'
import type { Dataset } from '../types/api'
import { UploadCard } from './UploadCard'

vi.mock('../api/client', () => ({ api: { uploadDataset: vi.fn() } }))

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

describe('UploadCard', () => {
  it('uploads the chosen CSV, prevents repeated actions while busy, and clears the completed selection', async () => {
    const file = new File(['region,revenue\nNorth,120'], 'sales.csv', { type: 'text/csv' })
    const dataset: Dataset = { id: 42, original_filename: file.name, content_type: file.type, size_bytes: file.size }
    let completeUpload!: (value: Dataset) => void
    vi.mocked(api.uploadDataset).mockReturnValue(new Promise<Dataset>((resolve) => { completeUpload = resolve }))
    const onUploaded = vi.fn()

    render(<UploadCard onUploaded={onUploaded} />)
    fireEvent.change(screen.getByLabelText('Choose CSV file'), { target: { files: [file] } })
    expect(screen.getByText(file.name, { exact: true })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Upload CSV' }))

    expect(api.uploadDataset).toHaveBeenCalledTimes(1)
    expect(vi.mocked(api.uploadDataset).mock.calls[0][0]).toBe(file)
    expect(screen.getByRole('button', { name: /Uploading/ })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Choose file' })).toBeDisabled()
    expect(onUploaded).not.toHaveBeenCalled()

    await act(async () => { completeUpload(dataset) })

    expect(onUploaded).toHaveBeenCalledExactlyOnceWith(dataset)
    expect(screen.getByRole('status')).toHaveTextContent(`${file.name} is ready.`)
    expect(screen.queryByText(file.name, { exact: true })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Upload CSV' })).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Choose file' })).toBeEnabled()
  })
})
