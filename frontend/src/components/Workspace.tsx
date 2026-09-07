import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { parseApiError } from '../utils/errors'
import type { Dataset, DatasetProfile } from '../types/api'
import { AnalysisPanel } from './AnalysisPanel'
import { CleaningPanel } from './CleaningPanel'
import { InsightsPanel } from './InsightsPanel'
import { ProfilePanel } from './ProfilePanel'
import { Badge } from './Common'

type Tab = 'overview' | 'analysis' | 'cleaning' | 'insights'

export function Workspace({ dataset, refreshToken }: { dataset: Dataset; refreshToken: number }) {
  const [tab, setTab] = useState<Tab>('overview')
  const [profile, setProfile] = useState<DatasetProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  async function loadProfile() { setLoading(true); try { setProfile(await api.getProfile(dataset.id)); setError(null) } catch (caught) { setError(parseApiError(caught)) } finally { setLoading(false) } }
  useEffect(() => { void loadProfile() }, [dataset.id, refreshToken])
  return <section className="workspace"><div className="workspace-heading"><div><h1>{dataset.original_filename}</h1><p className="workspace-subtitle">Dataset ID {dataset.id} · {dataset.content_type}</p></div><Badge value="persisted" tone="online" /></div><nav className="tabs" aria-label="Dataset workspace"><TabButton active={tab === 'overview'} onClick={() => setTab('overview')}>Overview</TabButton><TabButton active={tab === 'analysis'} onClick={() => setTab('analysis')}>Analysis</TabButton><TabButton active={tab === 'cleaning'} onClick={() => setTab('cleaning')}>Cleaning</TabButton><TabButton active={tab === 'insights'} onClick={() => setTab('insights')}>AI Insights</TabButton></nav>{tab === 'overview' && <ProfilePanel profile={profile} loading={loading} error={error} onRetry={() => void loadProfile()} />}{tab === 'analysis' && <AnalysisPanel datasetId={dataset.id} />}{tab === 'cleaning' && <CleaningPanel datasetId={dataset.id} />}{tab === 'insights' && <InsightsPanel datasetId={dataset.id} />}</section>
}
function TabButton({ active, onClick, children }: { active: boolean; onClick: () => void; children: string }) { return <button className={`tab ${active ? 'is-active' : ''}`} type="button" onClick={onClick} aria-current={active ? 'page' : undefined}>{children}</button> }
