import type { Dataset } from '../types/api'
import { formatBytes } from '../utils/format'
import { EmptyState, LoadingState, SectionHeading, StatusMessage } from './Common'

export function DatasetList({ datasets, selectedId, loading, error, onSelect, onRefresh }: { datasets: Dataset[]; selectedId: number | null; loading: boolean; error: string | null; onSelect: (dataset: Dataset) => void; onRefresh: () => void }) {
  return <section className="dataset-list"><SectionHeading title="Your datasets" detail={`${datasets.length} persisted ${datasets.length === 1 ? 'dataset' : 'datasets'}`} action={<button className="text-button" type="button" onClick={onRefresh}>Refresh</button>} />
    {loading ? <LoadingState label="Loading datasets..." /> : error ? <StatusMessage title="Could not load datasets" detail={error} tone="error" /> : datasets.length === 0 ? <EmptyState title="No datasets yet" detail="Upload a CSV to create your first workspace." /> : <div className="dataset-items">{datasets.map((dataset) => <button key={dataset.id} type="button" className={`dataset-item ${selectedId === dataset.id ? 'is-selected' : ''}`} onClick={() => onSelect(dataset)}><span className="file-avatar">CSV</span><span className="dataset-item-copy"><strong>{dataset.original_filename}</strong><small>ID {dataset.id} · {dataset.content_type}</small></span><span className="dataset-size">{formatBytes(dataset.size_bytes)} <span aria-hidden="true">→</span></span></button>)}</div>}
  </section>
}
