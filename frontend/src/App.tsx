import { useCallback, useEffect, useState } from 'react'
import { api } from './api/client'
import type { Dataset } from './types/api'
import { parseApiError } from './utils/errors'
import { DatasetList } from './components/DatasetList'
import { Header } from './components/Header'
import { EmptyState, LoadingState } from './components/Common'
import { UploadCard } from './components/UploadCard'
import { Workspace } from './components/Workspace'

export default function App() {
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [selected, setSelected] = useState<Dataset | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [refreshToken, setRefreshToken] = useState(0)
  const loadDatasets = useCallback(async () => { setLoading(true); try { const loaded = await api.listDatasets(); setDatasets(loaded); setSelected((current) => current && loaded.some((item) => item.id === current.id) ? loaded.find((item) => item.id === current.id) ?? null : loaded[0] ?? null); setError(null) } catch (caught) { setError(parseApiError(caught)) } finally { setLoading(false) } }, [])
  useEffect(() => { void loadDatasets() }, [loadDatasets])
  function handleUploaded(dataset: Dataset) { setDatasets((current) => [...current.filter((item) => item.id !== dataset.id), dataset]); setSelected(dataset); setRefreshToken((value) => value + 1) }
  return <div className="app-shell">
    <a className="skip-link" href="#main-content">Skip to main content</a>
    <Header onRefresh={() => { void loadDatasets(); setRefreshToken((value) => value + 1) }} />
    <main id="main-content" tabIndex={-1}>
      <div className="main-grid">
        <aside aria-label="Dataset tools">
          <UploadCard onUploaded={handleUploaded} />
          <DatasetList datasets={datasets} selectedId={selected?.id ?? null} loading={loading} error={error} onSelect={setSelected} onRefresh={() => void loadDatasets()} />
        </aside>
        <div className="workspace-column">
          {selected ? <Workspace dataset={selected} refreshToken={refreshToken} /> : <div className="welcome-panel panel">
            {loading ? <LoadingState label="Loading your workspace..." /> : <EmptyState
              title={error ? 'Your workspace is unavailable' : 'Start with a CSV dataset'}
              detail={error ? 'Refresh your datasets to try connecting again.' : 'Upload a file or select a saved dataset to inspect its quality, run analysis, and create a cleaned copy.'}
            />}
          </div>}
        </div>
      </div>
    </main>
    <footer><span>DataPilot AI</span><span>Dataset intelligence workspace</span></footer>
  </div>
}
