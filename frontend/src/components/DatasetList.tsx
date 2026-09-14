import type { Dataset } from '../types/api'
import { formatBytes } from '../utils/format'
import { EmptyState, LoadingState, SectionHeading, StatusMessage } from './Common'

export function DatasetList({ datasets, selectedId, loading, error, onSelect, onRefresh }: { datasets: Dataset[]; selectedId: number | null; loading: boolean; error: string | null; onSelect: (dataset: Dataset) => void; onRefresh: () => void }) {
  return <section className="dataset-list" aria-label="Your datasets">
    <SectionHeading title="Your datasets" detail={`${datasets.length} saved ${datasets.length === 1 ? 'dataset' : 'datasets'}`} action={<button className="text-button" type="button" onClick={onRefresh} disabled={loading} aria-label="Refresh datasets">Refresh</button>} />
    {loading ? <LoadingState label="Loading datasets..." /> : error ? <StatusMessage title="Could not load datasets" detail={error} tone="error" /> : datasets.length === 0 ? <EmptyState title="No datasets yet" detail="Your uploaded CSV files will appear here, ready to reopen." /> : <ul className="dataset-items">
      {datasets.map((dataset) => <li key={dataset.id}>
        <button type="button" className={`dataset-item ${selectedId === dataset.id ? 'is-selected' : ''}`} onClick={() => onSelect(dataset)} aria-pressed={selectedId === dataset.id} title={dataset.original_filename}>
          <span className="file-avatar" aria-hidden="true">CSV</span>
          <span className="dataset-item-copy">
            <strong>{dataset.original_filename}</strong>
            <span className="dataset-item-meta"><span>ID {dataset.id}</span><span>{formatBytes(dataset.size_bytes)}</span></span>
            <small className="dataset-content-type">{dataset.content_type}</small>
          </span>
          <span className="dataset-selection" aria-hidden="true">{selectedId === dataset.id ? 'Selected' : 'Open'}</span>
        </button>
      </li>)}
    </ul>}
  </section>
}
