'use client'

import { useCallback, useEffect, useState } from 'react'
import { BulkTokenInput } from './BulkTokenInput'
import {
  IntegrationPlatform,
  integrationEndpoints,
  integrationHeaders,
  parseErrorMessage,
  supabaseConfigAvailable,
} from '@/utils/integrations/api'

interface TokenStatus {
  platform: IntegrationPlatform
  connected: boolean
  lastSync?: string
  expiresIn?: string
  accountName?: string
  rateLimitRemaining?: number
}

interface Alert {
  tone: 'success' | 'warning' | 'error'
  text: string
}

const Icon = {
  Key: () => <span aria-hidden>🔑</span>,
  Link: () => <span aria-hidden>🔗</span>,
  Zap: () => <span aria-hidden>⚡</span>,
  Check: () => (
    <span aria-hidden className="text-green-400">
      ✔
    </span>
  ),
  Cross: () => (
    <span aria-hidden className="text-gray-400">
      ✖
    </span>
  ),
  Refresh: ({ spinning }: { spinning?: boolean }) => (
    <span aria-hidden className={spinning ? 'inline-block animate-spin' : undefined}>
      ⟳
    </span>
  ),
  Disconnect: () => <span aria-hidden>⨯</span>,
  Alert: () => (
    <span aria-hidden className="text-[#C1A6FF]">
      ℹ
    </span>
  ),
}

const defaultTokens: Record<IntegrationPlatform, TokenStatus> = {
  meta: { platform: 'meta', connected: false },
  linkedin: { platform: 'linkedin', connected: false },
  custom: { platform: 'custom', connected: false },
}

const defaultTokenInputs: Record<IntegrationPlatform, { token: string; accountId?: string }> = {
  meta: { token: '', accountId: '' },
  linkedin: { token: '' },
  custom: { token: '' },
}

export function IntegrationSettings() {
  const [tokens, setTokens] = useState<Record<IntegrationPlatform, TokenStatus>>(defaultTokens)
  const [tokenInputs, setTokenInputs] =
    useState<Record<IntegrationPlatform, { token: string; accountId?: string }>>(defaultTokenInputs)
  const [showTokenInput, setShowTokenInput] = useState<IntegrationPlatform | null>(null)
  const [loading, setLoading] = useState(false)
  const [syncing, setSyncing] = useState<IntegrationPlatform | null>(null)
  const [showBulkInput, setShowBulkInput] = useState(false)
  const [alert, setAlert] = useState<Alert | null>(null)

  const loadTokenStatus = useCallback(async () => {
    if (!supabaseConfigAvailable) return
    try {
      const response = await fetch(integrationEndpoints.status, {
        headers: integrationHeaders,
      })

      if (response.ok) {
        const data = (await response.json()) as {
          tokens?: Record<IntegrationPlatform, TokenStatus>
        }
        setTokens(data.tokens ?? defaultTokens)
      }
    } catch (error) {
      console.error('Failed to load token status:', error)
    }
  }, [])

  useEffect(() => {
    void loadTokenStatus()
  }, [loadTokenStatus])

  const saveToken = async (platform: IntegrationPlatform) => {
    const { token, accountId } = tokenInputs[platform]

    if (!token.trim()) {
      setAlert({ tone: 'error', text: 'Please enter a valid token' })
      return
    }
    if (!supabaseConfigAvailable) {
      setAlert({ tone: 'error', text: 'Supabase environment variables are missing.' })
      return
    }

    setLoading(true)
    try {
      const response = await fetch(integrationEndpoints.connect, {
        method: 'POST',
        headers: integrationHeaders,
        body: JSON.stringify({
          platform,
          token,
          accountId: accountId || undefined,
        }),
      })

      if (response.ok) {
        const data = (await response.json()) as { accountName?: string }
        setAlert({ tone: 'success', text: `${platform.toUpperCase()} connected successfully.` })
        setTokens((prev) => ({
          ...prev,
          [platform]: {
            ...prev[platform],
            connected: true,
            accountName: data.accountName,
            lastSync: new Date().toISOString(),
          },
        }))
        setShowTokenInput(null)
        setTokenInputs((prev) => ({
          ...prev,
          [platform]: { token: '', accountId: platform === 'meta' ? '' : undefined },
        }))
      } else {
        const errorMessage = await parseErrorMessage(response, 'Failed to connect')
        setAlert({ tone: 'error', text: errorMessage })
      }
    } catch (error) {
      console.error('Error saving token:', error)
      setAlert({ tone: 'error', text: 'Failed to save token' })
    } finally {
      setLoading(false)
    }
  }

  const disconnectToken = async (platform: IntegrationPlatform) => {
    if (!supabaseConfigAvailable) {
      setAlert({ tone: 'error', text: 'Supabase environment variables are missing.' })
      return
    }

    setLoading(true)
    try {
      const response = await fetch(integrationEndpoints.disconnect, {
        method: 'DELETE',
        headers: integrationHeaders,
        body: JSON.stringify({ platform }),
      })

      if (response.ok) {
        setAlert({ tone: 'success', text: `${platform.toUpperCase()} disconnected.` })
        setTokens((prev) => ({
          ...prev,
          [platform]: {
            ...prev[platform],
            connected: false,
            accountName: undefined,
            lastSync: undefined,
          },
        }))
      } else {
        const errorMessage = await parseErrorMessage(response, 'Failed to disconnect')
        setAlert({ tone: 'error', text: errorMessage })
      }
    } catch (error) {
      console.error('Error disconnecting:', error)
      setAlert({ tone: 'error', text: 'Failed to disconnect' })
    } finally {
      setLoading(false)
    }
  }

  const syncData = async (platform: IntegrationPlatform) => {
    if (!supabaseConfigAvailable) {
      setAlert({ tone: 'error', text: 'Supabase environment variables are missing.' })
      return
    }

    setSyncing(platform)
    try {
      const response = await fetch(integrationEndpoints.sync, {
        method: 'POST',
        headers: integrationHeaders,
        body: JSON.stringify({ platform }),
      })

      if (response.ok) {
        const data = (await response.json()) as { recordsUpdated?: number }
        setAlert({
          tone: 'success',
          text: `Synced ${data.recordsUpdated || 0} records from ${platform.toUpperCase()}.`,
        })
        setTokens((prev) => ({
          ...prev,
          [platform]: {
            ...prev[platform],
            lastSync: new Date().toISOString(),
          },
        }))
      } else {
        const errorMessage = await parseErrorMessage(response, 'Sync failed')
        setAlert({ tone: 'error', text: errorMessage })
      }
    } catch (error) {
      console.error('Sync error:', error)
      setAlert({ tone: 'error', text: 'Sync failed' })
    } finally {
      setSyncing(null)
    }
  }

  const formatTimeAgo = (isoDate?: string) => {
    if (!isoDate) return 'Never'
    const date = new Date(isoDate)
    const seconds = Math.floor((Date.now() - date.getTime()) / 1000)
    if (seconds < 60) return 'Just now'
    if (seconds < 3600) return `${Math.floor(seconds / 60)} min ago`
    if (seconds < 86400) return `${Math.floor(seconds / 3600)} hours ago`
    return `${Math.floor(seconds / 86400)} days ago`
  }

  const alertClasses = (tone: Alert['tone']) => {
    if (tone === 'success') return 'border-green-400/40 bg-green-400/10 text-green-100'
    if (tone === 'warning') return 'border-amber-300/40 bg-amber-300/10 text-amber-100'
    return 'border-red-400/40 bg-red-400/10 text-red-100'
  }

  const renderStatusChip = (connected: boolean) => (
    <div
      className={
        connected
          ? 'flex items-center gap-2 rounded-full border border-green-500/30 bg-green-500/20 px-3 py-1.5'
          : 'flex items-center gap-2 rounded-full border border-gray-500/30 bg-gray-500/20 px-3 py-1.5'
      }
    >
      {connected ? <Icon.Check /> : <Icon.Cross />}
      <span className={connected ? 'text-sm text-green-400' : 'text-sm text-gray-400'}>
        {connected ? 'Connected' : 'Not Connected'}
      </span>
    </div>
  )

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0C2742] to-[#1a3a5a] p-6 sm:p-8">
      <div className="mx-auto max-w-4xl">
        <div className="mb-8">
          <div className="mb-2 flex items-center justify-between gap-3">
            <h1
              className="text-2xl font-semibold text-white"
              style={{
                background: 'linear-gradient(135deg, #C1A6FF 0%, #6D7D8E 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              Integration Settings
            </h1>
            <button
              onClick={() => setShowBulkInput(!showBulkInput)}
              className="flex items-center gap-2 rounded-lg px-4 py-2 text-white transition-all"
              style={{
                background: showBulkInput
                  ? 'rgba(193, 166, 255, 0.2)'
                  : 'linear-gradient(135deg, #C1A6FF 0%, #6D7D8E 100%)',
                border: showBulkInput ? '1px solid rgba(193, 166, 255, 0.4)' : 'none',
              }}
            >
              <Icon.Zap />
              <span>{showBulkInput ? 'Individual Setup' : 'Quick Setup (All Tokens)'}</span>
            </button>
          </div>
          <p className="text-[#9EA9B3]">
            Connect your social media accounts to automatically populate your analytics dashboard (Deck 2) with real-time data.
          </p>
          {!supabaseConfigAvailable && (
            <div className="mt-3 rounded-lg border border-amber-300/40 bg-amber-300/10 p-3 text-sm text-amber-50">
              Add NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY to enable live
              connections.
            </div>
          )}
        </div>

        {showBulkInput && (
          <BulkTokenInput
            onComplete={() => {
              setShowBulkInput(false)
              void loadTokenStatus()
            }}
          />
        )}

        {alert && (
          <div className={`mb-4 rounded-lg border p-3 ${alertClasses(alert.tone)}`}>
            {alert.text}
          </div>
        )}

        <div className="space-y-6">
          <div className="rounded-xl border border-[#6D7D8E]/30 bg-[#0C2742]/40 p-6 backdrop-blur-md">
            <div className="mb-4 flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-gradient-to-br from-[#E1306C] to-[#405DE6] text-xl text-white">
                  <Icon.Link />
                </div>
                <div>
                  <h3 className="font-medium text-white">Meta Platform</h3>
                  <p className="text-sm text-[#9EA9B3]">Instagram &amp; Facebook</p>
                </div>
              </div>
              {renderStatusChip(tokens.meta.connected)}
            </div>

            {tokens.meta.connected ? (
              <div className="space-y-3 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-[#9EA9B3]">Account:</span>
                  <span className="text-white">{tokens.meta.accountName || 'Unknown'}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[#9EA9B3]">Last sync:</span>
                  <span className="text-white">{formatTimeAgo(tokens.meta.lastSync)}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[#9EA9B3]">Token expires:</span>
                  <span className="text-white">{tokens.meta.expiresIn || '45 days'}</span>
                </div>
                <div className="mt-4 flex gap-2">
                  <button
                    onClick={() => {
                      void syncData('meta')
                    }}
                    disabled={syncing === 'meta'}
                    className="flex flex-1 items-center justify-center gap-2 rounded-lg border border-[#C1A6FF]/30 bg-[#C1A6FF]/20 px-4 py-2 text-[#C1A6FF] transition-all disabled:opacity-60"
                  >
                    <Icon.Refresh spinning={syncing === 'meta'} />
                    {syncing === 'meta' ? 'Syncing...' : 'Sync Now'}
                  </button>
                  <button
                    onClick={() => {
                      void disconnectToken('meta')
                    }}
                    disabled={loading}
                    className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/20 px-4 py-2 text-red-400 transition-all disabled:opacity-60"
                  >
                    <Icon.Disconnect />
                    Disconnect
                  </button>
                </div>
              </div>
            ) : (
              <div>
                {showTokenInput === 'meta' ? (
                  <div className="space-y-3">
                    <div>
                      <label
                        className="mb-2 block text-sm text-[#9EA9B3]"
                        htmlFor="metaAccessToken"
                      >
                        Access Token
                      </label>
                      <input
                        id="metaAccessToken"
                        type="password"
                        value={tokenInputs.meta.token}
                        onChange={(e) =>
                          setTokenInputs((prev) => ({
                            ...prev,
                            meta: { ...prev.meta, token: e.target.value },
                          }))
                        }
                        placeholder="Paste your Meta access token"
                        className="w-full rounded-lg border border-[#6D7D8E]/30 bg-[#0C2742]/60 px-4 py-2 text-white placeholder-[#6D7D8E] focus:border-[#C1A6FF]/50 focus:outline-none"
                      />
                    </div>
                    <div>
                      <label
                        className="mb-2 block text-sm text-[#9EA9B3]"
                        htmlFor="metaInstagramAccount"
                      >
                        Instagram Account ID (optional)
                      </label>
                      <input
                        id="metaInstagramAccount"
                        type="text"
                        value={tokenInputs.meta.accountId}
                        onChange={(e) =>
                          setTokenInputs((prev) => ({
                            ...prev,
                            meta: { ...prev.meta, accountId: e.target.value },
                          }))
                        }
                        placeholder="1234567890"
                        className="w-full rounded-lg border border-[#6D7D8E]/30 bg-[#0C2742]/60 px-4 py-2 text-white placeholder-[#6D7D8E] focus:border-[#C1A6FF]/50 focus:outline-none"
                      />
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => {
                          void saveToken('meta')
                        }}
                        disabled={loading}
                        className="flex-1 rounded-lg px-4 py-2 text-white transition-all disabled:opacity-60"
                        style={{ background: 'linear-gradient(135deg, #C1A6FF 0%, #6D7D8E 100%)' }}
                      >
                        {loading ? 'Connecting...' : 'Save Token'}
                      </button>
                      <button
                        onClick={() => {
                          setShowTokenInput(null)
                          setTokenInputs((prev) => ({
                            ...prev,
                            meta: { token: '', accountId: '' },
                          }))
                        }}
                        className="rounded-lg border border-[#6D7D8E]/30 bg-[#0C2742]/60 px-4 py-2 text-[#9EA9B3] transition-all hover:bg-[#0C2742]/80"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <button
                    onClick={() => setShowTokenInput('meta')}
                    className="flex w-full items-center justify-center gap-2 rounded-lg px-4 py-2 text-white transition-all"
                    style={{ background: 'linear-gradient(135deg, #C1A6FF 0%, #6D7D8E 100%)' }}
                  >
                    <Icon.Key />
                    Connect Meta Account
                  </button>
                )}
              </div>
            )}
          </div>

          <div className="rounded-xl border border-[#6D7D8E]/30 bg-[#0C2742]/40 p-6 backdrop-blur-md">
            <div className="mb-4 flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-[#0077B5] text-xl text-white">
                  <Icon.Link />
                </div>
                <div>
                  <h3 className="font-medium text-white">LinkedIn</h3>
                  <p className="text-sm text-[#9EA9B3]">Company Page Analytics</p>
                </div>
              </div>
              {renderStatusChip(tokens.linkedin.connected)}
            </div>

            {tokens.linkedin.connected ? (
              <div className="flex flex-col items-center justify-center gap-2">
                <div className="mb-2 flex items-center gap-2">
                  <span className="text-green-400"><Icon.Check /></span>
                  <span className="text-white">
                    Connected{tokens.linkedin.accountName ? ` as ${tokens.linkedin.accountName}` : ''}
                  </span>
                </div>
                <button
                  onClick={() => setShowTokenInput('linkedin')}
                  className="flex w-full items-center justify-center gap-2 rounded-lg bg-[#0077B5] px-4 py-2 text-white transition-all hover:bg-[#006399]"
                >
                  <Icon.Key />
                  Reconnect LinkedIn
                </button>
              </div>
            ) : (
              <button
                onClick={() => setShowTokenInput('linkedin')}
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-[#0077B5] px-4 py-2 text-white transition-all hover:bg-[#006399]"
              >
                <Icon.Key />
                Connect LinkedIn
              </button>
            )}
          </div>

          <div className="rounded-xl border border-[#6D7D8E]/30 bg-[#0C2742]/40 p-6 backdrop-blur-md">
            <div className="mb-4 flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-gradient-to-br from-[#C1A6FF] to-[#6D7D8E] text-xl text-white">
                  <Icon.Key />
                </div>
                <div>
                  <h3 className="font-medium text-white">Custom Integration</h3>
                  <p className="text-sm text-[#9EA9B3]">Codex or Custom API</p>
                </div>
              </div>
              {renderStatusChip(tokens.custom.connected)}
            </div>

            <button
              onClick={() => setShowTokenInput('custom')}
              className="flex w-full items-center justify-center gap-2 rounded-lg px-4 py-2 text-white transition-all"
              style={{ background: 'linear-gradient(135deg, #C1A6FF 0%, #6D7D8E 100%)' }}
            >
              <Icon.Key />
              {tokens.custom.connected
                ? (
                  <>
                    {tokens.custom.accountName
                      ? `Connected: ${tokens.custom.accountName}`
                      : 'Custom Integration Connected'}
                    {tokens.custom.lastSync && (
                      <span className="ml-2 text-xs text-[#9EA9B3]">
                        Last Sync: {tokens.custom.lastSync}
                      </span>
                    )}
                  </>
                )
                : 'Configure Custom Integration'}
            </button>
          </div>
        </div>

        <div className="mt-8 rounded-xl border border-[#C1A6FF]/30 bg-[#C1A6FF]/10 p-6">
          <div className="flex gap-3">
            <div className="mt-0.5 flex h-5 w-5 items-center justify-center">
              <Icon.Alert />
            </div>
            <div>
              <h4 className="mb-2 font-medium text-white">Need Help?</h4>
              <p className="mb-3 text-sm text-[#9EA9B3]">
                Follow the <a href="https://github.com/your-org/your-repo/blob/main/META_INTEGRATION_GUIDE.md" target="_blank" rel="noopener noreferrer" className="font-bold underline">META_INTEGRATION_GUIDE.md</a> to get your access tokens.
              </p>
              <ul className="list-inside list-disc space-y-1 text-sm text-[#9EA9B3]">
                <li>Meta tokens expire after 45 days (we&apos;ll remind you)</li>
                <li>Data syncs automatically every hour</li>
                <li>Manual sync available anytime</li>
                <li>All tokens stored securely server-side</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
