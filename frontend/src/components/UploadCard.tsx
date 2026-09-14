import { useRef, useState } from 'react'
import { api } from '../api/client'
import { parseApiError } from '../utils/errors'
import { formatBytes } from '../utils/format'
import { validateCsvFile } from '../utils/validation'
import { StatusMessage } from './Common'
import type { Dataset } from '../types/api'

export function UploadCard({ onUploaded }: { onUploaded: (dataset: Dataset) => void }) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [dragging, setDragging] = useState(false)
  const [busy, setBusy] = useState(false)
  const [feedback, setFeedback] = useState<{ tone: 'error' | 'success'; text: string } | null>(null)

  function chooseFile(file: File | null) {
    const error = validateCsvFile(file)
    if (error) { setSelectedFile(null); setFeedback({ tone: 'error', text: error }); return }
    setSelectedFile(file); setFeedback(null)
  }

  async function upload() {
    if (!selectedFile) return
    setBusy(true); setFeedback(null)
    try { const dataset = await api.uploadDataset(selectedFile); setFeedback({ tone: 'success', text: `${dataset.original_filename} is ready.` }); setSelectedFile(null); if (inputRef.current) inputRef.current.value = ''; onUploaded(dataset) }
    catch (error) { setFeedback({ tone: 'error', text: parseApiError(error) }) }
    finally { setBusy(false) }
  }

  return <section className="upload-card panel" aria-labelledby="upload-heading">
    <div className="upload-copy"><h2 id="upload-heading">Upload dataset</h2><p>Add a CSV to start exploring your data.</p></div>
    <div
      className={`dropzone ${dragging ? 'is-dragging' : ''} ${busy ? 'is-busy' : ''}`}
      aria-busy={busy}
      onDragOver={(event) => { event.preventDefault(); if (!busy) setDragging(true) }}
      onDragLeave={(event) => { if (!event.currentTarget.contains(event.relatedTarget as Node | null)) setDragging(false) }}
      onDrop={(event) => { event.preventDefault(); setDragging(false); if (!busy) chooseFile(event.dataTransfer.files[0] ?? null) }}
    >
      <svg className="upload-icon" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M12 16V4m-4 4 4-4 4 4M4 15v5h16v-5" /></svg>
      <strong>{dragging ? 'Drop your CSV to select it' : 'Drop a CSV file here'}</strong>
      <span id="upload-help">CSV files only</span>
      <button className="button button-secondary" type="button" onClick={() => inputRef.current?.click()} disabled={busy} aria-describedby="upload-help">Choose file</button>
      <input ref={inputRef} hidden type="file" accept=".csv,text/csv" aria-label="Choose CSV file" disabled={busy} onChange={(event) => chooseFile(event.target.files?.[0] ?? null)} />
      {selectedFile && <div className="selected-file"><span title={selectedFile.name}>{selectedFile.name}</span><small>{formatBytes(selectedFile.size)}</small></div>}
    </div>
    {(feedback || selectedFile) && <div className="upload-footer">
      {feedback && <StatusMessage title={feedback.tone === 'success' ? 'Dataset uploaded' : 'Upload needs attention'} detail={feedback.text} tone={feedback.tone} />}
      {selectedFile && <button className="button button-primary" type="button" onClick={() => void upload()} disabled={busy}>
        {busy && <span className="spinner" aria-hidden="true" />}{busy ? 'Uploading...' : 'Upload CSV'}
      </button>}
    </div>}
  </section>
}
