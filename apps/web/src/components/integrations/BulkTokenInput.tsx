'use client'

import { useState } from 'react'
import {
  IntegrationPlatform,
  integrationEndpoints,
  integrationHeaders,
  supabaseConfigAvailable,
} from '@/utils/integrations/api'

interface TokenInputs {
  metaToken: string
  metaAccountId: string
  linkedinToken: string
  customToken: string
}

interface StatusMessage {
  tone: 'success' | 'warning' | 'error'
  text: string
}

const Icon = {
  Zap: () => (
    <span aria-hidden className="text-lg">
      ⚡
    </span>
  ),
  Check: () => (
    <span aria-hidden className="text-green-400">
      ✔
    </span>
  ),
  Alert: () => (
    <span aria-hidden className="text-red-400">
      ✖
    </span>
  ),
}

export function BulkTokenInput({ onComplete }: { onComplete: () => void }) {
  const [tokens, setTokens] = useState<TokenInputs>({
    metaToken: '',
    metaAccountId: '',
    linkedinToken: '',
    customToken: '',
  })
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState<string[]>([])
  const [status, setStatus] = useState<StatusMessage | null>(null)

  const hasTokens = tokens.metaToken || tokens.linkedinToken || tokens.customToken

  // Map IntegrationPlatform values to TokenInputs keys
  const platformTokenKeyMap: Record<IntegrationPlatform, keyof TokenInputs> = {
    meta: 'metaToken',
    linkedin: 'linkedinToken',
    custom: 'customToken',
  }

  const connectPlatform = async (platform: IntegrationPlatform) => {
    const tokenKey = platformTokenKeyMap[platform]
    const token = tokens[tokenKey]
    if (!token) return false

    setProgress((prev) => [...prev, `Connecting ${platform}...`])
    try {
      const response = await fetch(integrationEndpoints.connect, {
        method: 'POST',
        headers: integrationHeaders,
        body: JSON.stringify({
          platform,
          token,
          accountId: platform === 'meta' ? tokens.metaAccountId || undefined : undefined,
        }),
      })

      if (!response.ok) {
        setProgress((prev) => [...prev, `❌ ${platform} connection failed`])
        return false
      }
    } catch (error) {
      console.error(`${platform} connect error:`, error)
      setProgress((prev) => [...prev, `❌ ${platform} connection failed`])
      return false
    }

    setProgress((prev) => [...prev, `✅ ${platform} connected`])

    if (platform === 'meta' || platform === 'linkedin') {
      setProgress((prev) => [...prev, `Syncing ${platform} data...`])
      try {
        const syncResponse = await fetch(integrationEndpoints.sync, {
          method: 'POST',
          headers: integrationHeaders,
          body: JSON.stringify({ platform }),
        })

        if (syncResponse.ok) {
          const syncData = (await syncResponse.json()) as { recordsUpdated?: number }
          setProgress((prev) => [
            ...prev,
            `✅ Synced ${syncData.recordsUpdated || 0} ${platform === 'meta' ? 'Meta' : 'LinkedIn'} records`,
          ])
        } else {
          setProgress((prev) => [...prev, `❌ ${platform} sync failed`])
        }
      } catch (error) {
        console.error(`${platform} sync error:`, error)
        setProgress((prev) => [...prev, `❌ ${platform} sync failed`])
      }
    }

    return true
  }

  const connectAll = async () => {
    if (!supabaseConfigAvailable) {
      setStatus({
        tone: 'error',
        text: 'Supabase project information is missing. Add NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY.',
      })
      return
    }

    setLoading(true)
    setProgress([])
    setStatus(null)

    const attempted: IntegrationPlatform[] = []

    if (tokens.metaToken) attempted.push('meta')
    if (tokens.linkedinToken) attempted.push('linkedin')
    if (tokens.customToken) attempted.push('custom')

    let successes = 0

    for (const platform of attempted) {
      const success = await connectPlatform(platform)
      if (success) successes += 1
    }

    if (attempted.length === 0) {
      setStatus({ tone: 'warning', text: 'Enter at least one token to continue.' })
    } else if (successes === attempted.length) {
      setStatus({ tone: 'success', text: `All ${successes} integrations connected successfully.` })
      setTimeout(() => onComplete(), 1200)
    } else {
      setStatus({
        tone: 'warning',
        text: `${successes}/${attempted.length} integrations connected. Check details below.`,
      })
    }
    setLoading(false)
  }

  return (
    <div className="mb-6 rounded-xl border border-[#C1A6FF]/30 bg-gradient-to-br from-[#C1A6FF]/10 to-[#6D7D8E]/10 p-6">
      <div className="mb-4 flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-[#C1A6FF] to-[#6D7D8E]">
          <Icon.Zap />
        </div>
        <div>
          <h3 className="font-medium text-white">Quick Setup</h3>
          <p className="text-sm text-[#9EA9B3]">Enter all tokens at once</p>
        </div>
      </div>

      <div className="space-y-4">
        <div>
          <label className="mb-2 block text-sm text-[#9EA9B3]" htmlFor="metaToken">
            Meta Access Token
          </label>
          <input
            id="metaToken"
            type="password"
            value={tokens.metaToken}
            onChange={(e) => setTokens((prev) => ({ ...prev, metaToken: e.target.value }))}
            placeholder="Paste Meta/Facebook access token"
            className="w-full rounded-lg border border-[#6D7D8E]/30 bg-[#0C2742]/60 px-4 py-2 text-white placeholder-[#6D7D8E] focus:border-[#C1A6FF]/50 focus:outline-none"
            disabled={loading}
          />
        </div>

        <div>
          <label className="mb-2 block text-sm text-[#9EA9B3]" htmlFor="metaAccountId">
            Instagram Account ID (optional)
          </label>
          <input
            id="metaAccountId"
            type="text"
            value={tokens.metaAccountId}
            onChange={(e) => setTokens((prev) => ({ ...prev, metaAccountId: e.target.value }))}
            placeholder="1234567890"
            className="w-full rounded-lg border border-[#6D7D8E]/30 bg-[#0C2742]/60 px-4 py-2 text-white placeholder-[#6D7D8E] focus:border-[#C1A6FF]/50 focus:outline-none"
            disabled={loading}
          />
        </div>

        <div>
          <label className="mb-2 block text-sm text-[#9EA9B3]" htmlFor="linkedinToken">
            LinkedIn Access Token
          </label>
          <input
            id="linkedinToken"
            type="password"
            value={tokens.linkedinToken}
            onChange={(e) => setTokens((prev) => ({ ...prev, linkedinToken: e.target.value }))}
            placeholder="Paste LinkedIn access token"
            className="w-full rounded-lg border border-[#6D7D8E]/30 bg-[#0C2742]/60 px-4 py-2 text-white placeholder-[#6D7D8E] focus:border-[#C1A6FF]/50 focus:outline-none"
            disabled={loading}
          />
        </div>

        <div>
          <label className="mb-2 block text-sm text-[#9EA9B3]" htmlFor="customToken">
            Custom/Codex Token
          </label>
          <input
            id="customToken"
            type="password"
            value={tokens.customToken}
            onChange={(e) => setTokens((prev) => ({ ...prev, customToken: e.target.value }))}
            placeholder="Paste custom API token"
            className="w-full rounded-lg border border-[#6D7D8E]/30 bg-[#0C2742]/60 px-4 py-2 text-white placeholder-[#6D7D8E] focus:border-[#C1A6FF]/50 focus:outline-none"
            disabled={loading}
          />
        </div>

        {progress.length > 0 && (
          <div className="rounded-lg bg-[#0C2742]/40 p-4">
            {progress.map((msg, index) => (
              <div key={index} className="flex items-center gap-2 text-sm">
                {msg.startsWith('✅') ? (
                  <Icon.Check />
                ) : msg.startsWith('❌') ? (
                  <Icon.Alert />
                ) : (
                  <span className="text-[#C1A6FF]">•</span>
                )}
                <span
                  className={
                    msg.startsWith('✅')
                      ? 'text-green-400'
                      : msg.startsWith('❌')
                        ? 'text-red-400'
                        : 'text-[#9EA9B3]'
                  }
                >
                  {msg.replace(/^[✅❌]\s*/, '')}
                </span>
              </div>
            ))}
          </div>
        )}

        {status && (
          <div
            className={`rounded-lg border p-3 ${
              status.tone === 'success'
                ? 'border-green-400/40 bg-green-400/10 text-green-100'
                : status.tone === 'warning'
                  ? 'border-amber-300/40 bg-amber-300/10 text-amber-100'
                  : 'border-red-400/40 bg-red-400/10 text-red-100'
            }`}
          >
            {status.text}
          </div>
        )}

        <button
          onClick={() => {
            void connectAll()
          }}
          disabled={loading || !hasTokens}
          className="flex w-full items-center justify-center gap-2 rounded-lg px-6 py-3 text-white transition-all disabled:cursor-not-allowed disabled:opacity-50"
          style={{
            background:
              hasTokens && !loading
                ? 'linear-gradient(135deg, #C1A6FF 0%, #6D7D8E 100%)'
                : undefined,
          }}
        >
          {loading ? (
            <>
              <span className="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent" />
              <span>Connecting...</span>
            </>
          ) : (
            <>
              <Icon.Zap />
              <span>Connect All &amp; Sync</span>
            </>
          )}
        </button>

        {!hasTokens && (
          <p className="text-center text-xs text-[#9EA9B3]">Enter at least one token to continue</p>
        )}
      </div>
    </div>
  )
}
