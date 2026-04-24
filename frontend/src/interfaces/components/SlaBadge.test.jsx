import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import SlaBadge from './SlaBadge'

describe('SlaBadge', () => {
  it('shows "SLA verletzt" when breached flag is true', () => {
    render(<SlaBadge dueAt={null} breached />)
    expect(screen.getByText('SLA verletzt')).toBeInTheDocument()
  })

  it('shows "Keine SLA-Frist" when no due date is set', () => {
    render(<SlaBadge dueAt={null} breached={false} />)
    expect(screen.getByText('Keine SLA-Frist')).toBeInTheDocument()
  })

  it('shows "Frist überschritten" when dueAt is in the past', () => {
    const pastIso = new Date(Date.now() - 60 * 60 * 1000).toISOString()
    render(<SlaBadge dueAt={pastIso} breached={false} />)
    expect(screen.getByText('Frist überschritten')).toBeInTheDocument()
  })

  it('shows "Fällig in < 24h" when dueAt is within 24h', () => {
    const soonIso = new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString()
    render(<SlaBadge dueAt={soonIso} breached={false} />)
    expect(screen.getByText('Fällig in < 24h')).toBeInTheDocument()
  })
})
