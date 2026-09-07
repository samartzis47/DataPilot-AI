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

  return <section className="upload-card panel">
    <div className="upload-copy"><h2>Upload dataset</h2><p>Upload a CSV to create a workspace.</p></div>
    <div className={`dropzone ${dragging ? 'is-dragging' : ''}`} onDragOver={(event) => { event.preventDefault(); setDragging(true) }} onDragLeave={() => setDragging(false)} onDrop={(event) => { event.preventDefault(); setDragging(false); chooseFile(event.dataTransfer.files[0] ?? null) }}>
      <div className="upload-icon" aria-hidden="true">↑</div><strong>Drop a CSV file here</strong><span>or</span><button className="button button-secondary" type="button" onClick={() => inputRef.current?.click()}>Choose file</button><input ref={inputRef} className="visually-hidden" type="file" accept=".csv,text/csv" onChange={(event) => chooseFile(event.target.files?.[0] ?? null)} />
      {selectedFile && <div className="selected-file"><span>{selectedFile.name}</span><small>{formatBytes(selectedFile.size)}</small></div>}
    </div>
    <div className="upload-footer">{feedback && <StatusMessage title={feedback.text} tone={feedback.tone} />}{selectedFile && <button className="button button-primary" type="button" onClick={() => void upload()} disabled={busy}>{busy ? 'Uploading...' : 'Upload CSV'}</button>}</div>
  </section>
}
