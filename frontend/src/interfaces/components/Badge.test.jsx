import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import Badge from './Badge'

describe('Badge', () => {
  it('translates status values to German', () => {
    render(<Badge value="new" type="status" />)
    expect(screen.getByText('Neu')).toBeInTheDocument()
  })

  it('maps priority "critical" to danger styling', () => {
    const { container } = render(<Badge value="critical" type="priority" />)
    const span = container.querySelector('span')
    expect(span).toHaveClass('badge')
    expect(span).toHaveClass('badge-danger')
    expect(span).toHaveTextContent('Kritisch')
  })

  it('translates category values to German', () => {
    render(<Badge value="bug" type="category" />)
    expect(screen.getByText('Fehler')).toBeInTheDocument()
  })

  it('falls back to the raw value for unknown types', () => {
    render(<Badge value="custom-label" type="unknown" />)
    expect(screen.getByText('custom-label')).toBeInTheDocument()
  })
})
