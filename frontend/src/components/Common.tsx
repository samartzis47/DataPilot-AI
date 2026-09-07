import type { ReactNode } from 'react'
import type { JobStatus, Severity } from '../types/api'

export function StatusMessage({ title, detail, tone = 'neutral' }: { title: string; detail?: string; tone?: 'neutral' | 'error' | 'success' }) {
  return <div className={`status-message status-${tone}`} role={tone === 'error' ? 'alert' : undefined}><strong>{title}</strong>{detail && <span>{detail}</span>}</div>
}

export function EmptyState({ title, detail, action }: { title: string; detail: string; action?: ReactNode }) {
  return <div className="empty-state"><div className="empty-mark">--</div><h3>{title}</h3><p>{detail}</p>{action}</div>
}

export function SectionHeading({ eyebrow, title, detail, action }: { eyebrow?: string; title: string; detail?: string; action?: ReactNode }) {
  return <div className="section-heading"><div>{eyebrow && <p className="eyebrow">{eyebrow}</p>}<h2>{title}</h2>{detail && <p className="section-detail">{detail}</p>}</div>{action}</div>
}

export function Badge({ value, tone }: { value: string; tone?: JobStatus | Severity | 'online' | 'offline' }) {
  return <span className={`badge badge-${tone ?? value}`}>{value.replace('_', ' ')}</span>
}

export function LoadingState({ label = 'Loading' }: { label?: string }) {
  return <div className="loading-state"><span className="spinner" aria-hidden="true" />{label}</div>
}
