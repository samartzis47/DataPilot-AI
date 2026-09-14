import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { parseApiError } from '../utils/errors'
import { formatDate, formatNumber } from '../utils/format'
import type { CleanedDataset, CleaningRequest } from '../types/api'
import { EmptyState, LoadingState, SectionHeading, StatusMessage } from './Common'

const initialForm: CleaningRequest = { remove_duplicate_rows: false, numeric_missing_strategy: 'keep', text_missing_strategy: 'keep', numeric_outlier_strategy: 'keep' }

export function CleaningPanel({ datasetId }: { datasetId: number }) {
  const [form, setForm] = useState<CleaningRequest>(initialForm)
  const [history, setHistory] = useState<CleanedDataset[]>([])
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<CleanedDataset | null>(null)
  async function load() { setLoading(true); try { setHistory(await api.listCleanings(datasetId)); setError(null) } catch (caught) { setError(parseApiError(caught)) } finally { setLoading(false) } }
  useEffect(() => { setResult(null); void load() }, [datasetId])
  async function submit(event: React.FormEvent) { event.preventDefault(); setBusy(true); setError(null); try { const created = await api.createCleaning(datasetId, form); setResult(created); await load() } catch (caught) { setError(parseApiError(caught)) } finally { setBusy(false) } }
  function update<K extends keyof CleaningRequest>(key: K, value: CleaningRequest[K]) { setForm((current) => ({ ...current, [key]: value })) }
  return (
    <div className="cleaning-layout">
      <section className="panel">
        <SectionHeading title="Clean a copy" detail="Choose how to handle data issues. The original CSV is preserved." />
        {error && <StatusMessage title="Cleaning unavailable" detail={error} tone="error" />}
        <form className="cleaning-form" onSubmit={submit} aria-busy={busy}>
          <fieldset className="form-group" disabled={busy}>
            <legend>Duplicate rows</legend>
            <label className="toggle-row">
              <input type="checkbox" checked={form.remove_duplicate_rows} onChange={(event) => update('remove_duplicate_rows', event.target.checked)} />
              <span>
                <strong>Remove duplicate rows</strong>
                <small>Keep the first occurrence of each repeated row.</small>
              </span>
            </label>
          </fieldset>
          <fieldset className="form-group" disabled={busy}>
            <legend>Missing values</legend>
            <div className="form-fields">
              <Field id="cleaning-numeric-missing" label="Numeric missing values" hint="Use the column's average or middle value to fill numeric gaps.">
                <select id="cleaning-numeric-missing" aria-describedby="cleaning-numeric-missing-help" value={form.numeric_missing_strategy} onChange={(event) => update('numeric_missing_strategy', event.target.value as CleaningRequest['numeric_missing_strategy'])}>
                  <option value="keep">Keep as-is</option>
                  <option value="mean">Fill with mean</option>
                  <option value="median">Fill with median</option>
                </select>
              </Field>
              <Field id="cleaning-text-missing" label="Text missing values" hint="The mode fills gaps with the column's most frequent value.">
                <select id="cleaning-text-missing" aria-describedby="cleaning-text-missing-help" value={form.text_missing_strategy} onChange={(event) => update('text_missing_strategy', event.target.value as CleaningRequest['text_missing_strategy'])}>
                  <option value="keep">Keep as-is</option>
                  <option value="mode">Fill with mode</option>
                </select>
              </Field>
            </div>
          </fieldset>
          <fieldset className="form-group" disabled={busy}>
            <legend>Outlier handling</legend>
            <Field id="cleaning-numeric-outliers" label="Numeric outliers" hint="Remove entire rows containing outliers, or clip extreme values to the interquartile range (IQR) bounds.">
              <select id="cleaning-numeric-outliers" aria-describedby="cleaning-numeric-outliers-help" value={form.numeric_outlier_strategy} onChange={(event) => update('numeric_outlier_strategy', event.target.value as CleaningRequest['numeric_outlier_strategy'])}>
                <option value="keep">Keep as-is</option>
                <option value="remove">Remove rows</option>
                <option value="clip_iqr">Clip to IQR bounds</option>
              </select>
            </Field>
          </fieldset>
          <div className="form-actions">
            <button className="button button-primary" type="submit" disabled={busy}>
              {busy && <span className="spinner" aria-hidden="true" />}
              {busy ? 'Cleaning...' : 'Create cleaned copy'}
            </button>
            <p className="field-help">Save a separate CSV with these settings.</p>
          </div>
        </form>
        {result && (
          <div className="cleaning-result">
            <StatusMessage title="Cleaned copy created" detail={result.original_filename} tone="success" />
            <dl className="result-stats">
              <div><dt>Original rows</dt><dd>{formatNumber(result.original_row_count)}</dd></div>
              <div><dt>Cleaned rows</dt><dd>{formatNumber(result.cleaned_row_count)}</dd></div>
            </dl>
            <a className="button button-secondary" href={api.downloadCleaningUrl(datasetId, result.id)} aria-label={`Download CSV: ${result.original_filename}, copy ${result.id}`}>Download CSV</a>
          </div>
        )}
      </section>
      <section className="panel" aria-busy={loading}>
        <SectionHeading title="Cleaning history" detail="Saved copies, newest first." />
        {loading ? <LoadingState label="Loading cleaning history..." /> : history.length ? (
          <ul className="cleaning-history">
            {history.map((item) => (
              <li className="history-row" key={item.id}>
                <div className="history-row-copy">
                  <strong title={item.original_filename}>{item.original_filename}</strong>
                  <div className="history-meta">
                    <span>Copy #{item.id}</span>
                    <span>{formatNumber(item.cleaned_row_count)} rows</span>
                    <time dateTime={item.created_at}>{formatDate(item.created_at)}</time>
                  </div>
                </div>
                <a className="button button-secondary" href={api.downloadCleaningUrl(datasetId, item.id)} aria-label={`Download CSV: ${item.original_filename}, copy ${item.id}`}>Download CSV</a>
              </li>
            ))}
          </ul>
        ) : <EmptyState title="No cleaned copies yet" detail="Choose your cleaning settings and create a copy. Saved CSV downloads will appear here." />}
      </section>
    </div>
  )
}

function Field({ id, label, hint, children }: { id: string; label: string; hint: string; children: React.ReactNode }) {
  return <div className="field"><label htmlFor={id}>{label}</label>{children}<p className="field-help" id={`${id}-help`}>{hint}</p></div>
}
