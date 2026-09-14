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

  return (
    <div className="insights-layout">
      <section className="panel">
        <SectionHeading
          title="AI insights"
          detail="Generate a saved report from the latest dataset analysis."
          action={
            <div className="insight-controls">
              <label className="field insight-provider">
                <span>Insight provider</span>
                <select
                  aria-label="Insight provider"
                  aria-describedby={`insight-provider-help-${datasetId}`}
                  value={provider}
                  disabled={busy}
                  onChange={(event) => setProvider(event.target.value as Provider)}
                >
                  <option value="rules">Rules provider</option>
                  <option value="openai">OpenAI (optional)</option>
                </select>
              </label>
              <button className="button button-primary" type="button" onClick={() => void generate()} disabled={busy}>
                {busy && <span className="spinner" aria-hidden="true" />}
                {busy ? 'Generating...' : 'Generate report'}
              </button>
            </div>
          }
        />
        <p className="provider-note" id={`insight-provider-help-${datasetId}`}>
          {provider === 'rules'
            ? 'Rules reports are deterministic and do not require an API key. OpenAI is optional.'
            : 'OpenAI requires backend configuration. No key is stored in the browser.'}
        </p>
        {error && <StatusMessage title="Insight generation failed" detail={error} tone="error" />}
        {loading ? (
          <LoadingState label="Loading insight history..." />
        ) : insights.length ? (
          <div className="insight-history">
            {insights.map((insight) => <InsightReport key={insight.id} insight={insight} />)}
          </div>
        ) : (
          <EmptyState title="No insight reports yet" detail="Run a dataset analysis, then generate a report to review findings and recommended actions." />
        )}
      </section>
    </div>
  )
}

function InsightReport({ insight }: { insight: DatasetInsight }) {
  return (
    <article className="insight-report" aria-labelledby={`insight-report-${insight.id}`}>
      <div className="insight-report-header">
        <div className="report-identity">
          <h3 id={`insight-report-${insight.id}`}>Report #{insight.id}</h3>
          <span>Analysis #{insight.analysis_id}</span>
        </div>
        <div className="report-meta">
          <Badge value={insight.provider} />
          <small>{insight.model || 'Deterministic rules'}</small>
          <time dateTime={insight.created_at}>{formatDate(insight.created_at)}</time>
        </div>
      </div>
      <p className="report-summary">{insight.summary}</p>
      <div className="insight-grid">
        {insight.insights.map((item, index) => (
          <section className={`insight-card insight-card-${item.severity} insight-card-${item.category}`} key={`${item.title}-${index}`}>
            <div className="insight-card-top">
              <Badge value={item.severity} tone={item.severity} />
              <span>{item.category.replace('_', ' ')}</span>
            </div>
            <h4>{item.title}</h4>
            <p>{item.description}</p>
            {item.evidence.length > 0 && (
              <div className="evidence">
                <span className="evidence-label">Evidence</span>
                <ul>{item.evidence.map((evidence, evidenceIndex) => <li key={evidenceIndex}>{evidence}</li>)}</ul>
              </div>
            )}
            <div className="confidence"><span>Confidence</span><strong>{Math.round(item.confidence * 100)}%</strong></div>
          </section>
        ))}
      </div>
      {insight.recommendations.length > 0 && (
        <section className="recommendation-block">
          <h4>Recommended actions</h4>
          <ol className="recommendation-list">
            {insight.recommendations.map((recommendation, index) => (
              <li className="recommendation" key={`${recommendation.action}-${index}`}>
                <Badge value={recommendation.priority} tone={recommendation.priority} />
                <div><strong>{recommendation.action}</strong><p>{recommendation.reason}</p></div>
              </li>
            ))}
          </ol>
        </section>
      )}
    </article>
  )
}
