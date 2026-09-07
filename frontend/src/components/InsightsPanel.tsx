import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { parseApiError } from '../utils/errors'
import { formatDate } from '../utils/format'
import type { DatasetInsight, Provider } from '../types/api'
import { Badge, EmptyState, LoadingState, SectionHeading, StatusMessage } from './Common'

export function InsightsPanel({ datasetId }: { datasetId: number }) {
  const [insights, setInsights] = useState<DatasetInsight[]>([])
  const [provider, setProvider] = useState<Provider>('rules')
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  async function load() { setLoading(true); try { setInsights(await api.listInsights(datasetId)); setError(null) } catch (caught) { setError(parseApiError(caught)) } finally { setLoading(false) } }
  useEffect(() => { void load() }, [datasetId])
  async function generate() { setBusy(true); setError(null); try { await api.createInsight(datasetId, provider); await load() } catch (caught) { setError(parseApiError(caught)) } finally { setBusy(false) } }
  return <div className="insights-layout"><section className="panel"><SectionHeading eyebrow="Decision support" title="AI insights" detail="Generate a persisted report from the latest analysis." action={<div className="insight-controls"><select aria-label="Insight provider" value={provider} onChange={(event) => setProvider(event.target.value as Provider)}><option value="rules">Rules provider</option><option value="openai">OpenAI provider</option></select><button className="button button-primary" type="button" onClick={() => void generate()} disabled={busy}>{busy ? 'Generating...' : 'Generate report'}</button></div>} />{provider === 'openai' && <p className="hint">OpenAI requires backend configuration. No key is stored in the browser.</p>}{error && <StatusMessage title="Insight generation failed" detail={error} tone="error" />}{loading ? <LoadingState label="Loading insight history..." /> : insights.length ? <div className="insight-history">{insights.map((insight) => <InsightReport key={insight.id} insight={insight} />)}</div> : <EmptyState title="No insight reports" detail="Run an analysis first, then generate a rules-based report." />}</section></div>
}
function InsightReport({ insight }: { insight: DatasetInsight }) { return <article className="insight-report"><div className="insight-report-header"><div><span className="eyebrow">Report #{insight.id} · Analysis #{insight.analysis_id}</span><h3>{insight.summary}</h3></div><div className="report-meta"><Badge value={insight.provider} /><small>{insight.model || 'Deterministic rules'} · {formatDate(insight.created_at)}</small></div></div><div className="insight-grid">{insight.insights.map((item, index) => <div className="insight-card" key={`${item.title}-${index}`}><div className="insight-card-top"><Badge value={item.severity} tone={item.severity} /><span>{item.category.replace('_', ' ')}</span></div><h4>{item.title}</h4><p>{item.description}</p>{item.evidence.length > 0 && <small className="evidence">Evidence: {item.evidence.join(' · ')}</small>}<div className="confidence">Confidence <strong>{Math.round(item.confidence * 100)}%</strong></div></div>)}</div>{insight.recommendations.length > 0 && <div className="recommendation-block"><h4>Recommended actions</h4>{insight.recommendations.map((recommendation, index) => <div className="recommendation" key={`${recommendation.action}-${index}`}><Badge value={recommendation.priority} tone={recommendation.priority} /><div><strong>{recommendation.action}</strong><p>{recommendation.reason}</p></div></div>)}</div>}</article> }
