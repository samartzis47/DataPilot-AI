import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { StatusMessage } from './Common'

describe('StatusMessage', () => {
  it('renders an API error state accessibly', () => {
    render(<StatusMessage title="Could not load datasets" detail="Dataset service unavailable" tone="error" />)
    expect(screen.getByRole('alert')).toHaveTextContent('Dataset service unavailable')
  })
})
