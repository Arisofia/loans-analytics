import React from 'react'
import { render, screen } from '@testing-library/react'
import HomePage from '../index'

// Mock Next.js Head component
jest.mock('next/head', () => {
  return {
    __esModule: true,
    default: ({ children }: { children: React.ReactNode }) => {
      return <>{children}</>
    },
  }
})

// Mock child components
jest.mock('@/components/account/AccountConfigurationForm', () => ({
  AccountConfigurationForm: () => (
    <div data-testid="account-config-form">Account Configuration Form</div>
  ),
}))

jest.mock('@/components/auth/AuthenticationForm', () => ({
  AuthenticationForm: () => (
    <div data-testid="auth-form">Authentication Form</div>
  ),
}))

describe('HomePage', () => {
  it('renders without crashing', () => {
    render(<HomePage />)
    // Check for main content instead of title (title is in <Head> which doesn't render in jsdom)
    expect(screen.getByText('Abaco Intelligence Platform')).toBeInTheDocument()
  })

  it('displays the main heading', () => {
    render(<HomePage />)
    expect(
      screen.getByText('Operational controls for secured lending portfolios')
    ).toBeInTheDocument()
  })

  it('renders authentication section', () => {
    render(<HomePage />)
    expect(screen.getByText('Secure access')).toBeInTheDocument()
    expect(screen.getByTestId('auth-form')).toBeInTheDocument()
  })

  it('renders account configuration section', () => {
    render(<HomePage />)
    expect(screen.getByText('Account configuration')).toBeInTheDocument()
    expect(screen.getByTestId('account-config-form')).toBeInTheDocument()
  })

  it('displays the platform branding', () => {
    render(<HomePage />)
    expect(screen.getByText('Abaco Intelligence Platform')).toBeInTheDocument()
  })
})
