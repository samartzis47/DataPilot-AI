import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { InsightsPanel } from './InsightsPanel'

vi.mock('../api/client', () => ({ api: { listInsights: vi.fn().mockResolvedValue([{ id: 4, dataset_id: 2, analysis_id: 7, provider: 'rules', model: null, summary: 'Sales data needs attention.', created_at: '2026-09-07T10:00:00Z', insights: [{ category: 'missing_values', severity: 'high', title: 'Missing values need attention', description: 'Several cells are empty.', evidence: ['Missing cells: 4'], confidence: 0.95 }], recommendations: [{ priority: 'high', action: 'Review missing values.', reason: 'They reduce completeness.' }] }]), createInsight: vi.fn() } }))

describe('InsightsPanel', () => {
  it('renders a successful persisted insight report', async () => {
    render(<InsightsPanel datasetId={2} />)
    expect(await screen.findByText('Sales data needs attention.')).toBeInTheDocument()
    expect(screen.getByText('Missing values need attention')).toBeInTheDocument()
    expect(screen.getByText('Review missing values.')).toBeInTheDocument()
  })
})
