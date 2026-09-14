import type { DatasetProfile } from '../types/api'
import { formatNumber } from '../utils/format'
import { Badge, EmptyState, LoadingState, SectionHeading, StatusMessage } from './Common'

export function ProfilePanel({ profile, loading, error, onRetry }: { profile: DatasetProfile | null; loading: boolean; error: string | null; onRetry: () => void }) {
  if (loading) return <div className="panel"><LoadingState label="Profiling dataset..." /></div>
  if (error) return <div className="panel profile-state"><StatusMessage title="Profile unavailable" detail={error} tone="error" /><button className="button button-secondary retry-button" type="button" onClick={onRetry}>Try again</button></div>
  if (!profile) return <EmptyState title="Profile not loaded" detail="Select a dataset to inspect its profile." />
  return <div className="profile-stack">
    <dl className="metric-strip panel" aria-label="Dataset summary">
      <Metric label="Rows" value={formatNumber(profile.row_count)} />
      <Metric label="Columns" value={formatNumber(profile.column_count)} />
      <Metric label="Duplicates" value={formatNumber(profile.duplicate_row_count)} />
      <Metric label="Quality score" value={formatNumber(profile.quality.score)} suffix="/100" accent={profile.quality.score >= 85 ? 'good' : profile.quality.score >= 60 ? 'warn' : 'bad'} />
    </dl>
    <section className="panel">
      <SectionHeading title="Data quality" detail={`${profile.quality.completeness_percentage}% complete · ${formatNumber(profile.quality.missing_cell_count)} missing cells`} />
      {profile.quality.issues.length ? <ul className="issue-list">
        {profile.quality.issues.map((issue, index) => <li className="issue-row" key={`${issue.code}-${index}`}>
          <Badge value={issue.severity} tone={issue.severity} />
          <div><strong>{issue.message}</strong>{issue.column && <small>Column: {issue.column}</small>}</div>
        </li>)}
      </ul> : <StatusMessage title="No quality issues reported" tone="success" />}
    </section>
    <section className="panel column-profile">
      <SectionHeading title="Column profile" detail="Data types, missing values, and numeric statistics" />
      <div className="table-wrap" role="region" aria-label="Column profile table" tabIndex={0}>
        <table>
          <caption className="visually-hidden">Column types, missing and unique values, means, and potential numeric outliers</caption>
          <thead><tr><th scope="col">Column</th><th scope="col">Type</th><th scope="col" className="numeric-cell">Missing</th><th scope="col" className="numeric-cell">Unique</th><th scope="col">Numeric statistics</th></tr></thead>
          <tbody>{profile.columns.map((column) => <tr key={column.name}>
            <th scope="row" className="column-name">{column.name}</th>
            <td><span className="type-chip">{column.data_type}</span></td>
            <td className="numeric-cell">{formatNumber(column.missing_count)} <small>({column.missing_percentage}%)</small></td>
            <td className="numeric-cell">{formatNumber(column.unique_count)}</td>
            <td>{column.numeric_statistics ? <div className="table-statistics">
              <span><strong>{formatNumber(column.numeric_statistics.mean)}</strong> mean</span>
              <small>{formatNumber(column.numeric_statistics.outlier_count)} outliers ({column.numeric_statistics.outlier_percentage}%)</small>
            </div> : <span className="muted"><span aria-hidden="true">—</span><span className="visually-hidden">No numeric statistics available</span></span>}</td>
          </tr>)}</tbody>
        </table>
      </div>
    </section>
  </div>
}
function Metric({ label, value, suffix, accent }: { label: string; value: string; suffix?: string; accent?: string }) {
  return <div className={`metric ${accent ? 'metric-quality' : ''}`}>
    <dt>{label}</dt>
    <dd className={accent ? `metric-${accent}` : ''}>{value}{suffix && <small>{suffix}</small>}</dd>
  </div>
}
