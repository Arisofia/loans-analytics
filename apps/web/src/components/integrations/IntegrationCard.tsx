'use client'

import type { ChangeEvent } from 'react'

import {
  PLATFORM_ICONS,
  PLATFORM_LABELS,
  STATUS_COLORS,
  type Platform,
  type TokenStatus,
} from '@/lib/integrations/constants'
import type { TokenState } from '@/types/integrations'

import styles from './IntegrationCard.module.css'

type IntegrationCardProps = {
  platform: Platform
  state: TokenState
  onConnect: () => Promise<void>
  onDisconnect: () => Promise<void>
  onSync: () => Promise<void>
  onChange: (changes: Partial<Pick<TokenState, 'token' | 'accountId'>>) => void
}

const statusCopy: Record<TokenStatus, string> = {
  valid: 'Valid',
  invalid: 'Invalid',
  connected: 'Connected',
  disconnected: 'Disconnected',
  syncing: 'Syncing',
  error: 'Error',
}

export function IntegrationCard({
  platform,
  state,
  onConnect,
  onDisconnect,
  onSync,
  onChange,
}: IntegrationCardProps) {
  const handleInputChange = (event: ChangeEvent<HTMLInputElement>) => {
    const { name, value } = event.target
    onChange({ [name]: value })
  }

  return (
    <div className={styles.card} aria-label={`${PLATFORM_LABELS[platform]} integration card`}>
      <div className={styles.header}>
        <div className={styles.identity}>
          <div className={styles.icon} aria-hidden>
            {PLATFORM_ICONS[platform]}
          </div>
          <div className={styles.titleBlock}>
            <h3>{PLATFORM_LABELS[platform]}</h3>
            <p className={styles.meta}>Secure token storage & initial sync</p>
          </div>
        </div>
        <span
          className={styles.statusChip}
          style={{ borderColor: `${STATUS_COLORS[state.status]}33` }}
          aria-live="polite"
        >
          <span
            style={{
              width: 10,
              height: 10,
              borderRadius: '50%',
              background: STATUS_COLORS[state.status],
            }}
          />
          {statusCopy[state.status]}
        </span>
      </div>

      <div className={styles.inputs}>
        <div className={styles.inputField}>
          <label htmlFor={`${platform}-token`}>Access token</label>
          <input
            id={`${platform}-token`}
            name="token"
            value={state.token || ''}
            onChange={handleInputChange}
            placeholder="Paste provider token"
            autoComplete="off"
            aria-label={`${PLATFORM_LABELS[platform]} token input`}
          />
        </div>
        <div className={styles.inputField}>
          <label htmlFor={`${platform}-account`}>Account ID (optional)</label>
          <input
            id={`${platform}-account`}
            name="accountId"
            value={state.accountId || ''}
            onChange={handleInputChange}
            placeholder="Account or page ID"
            autoComplete="off"
          />
        </div>
      </div>

      <div className={styles.actions}>
        <button
          className={styles.button}
          type="button"
          onClick={() => {
            void onConnect()
          }}
          aria-label={`Connect ${platform}`}
        >
          Connect & Sync
        </button>
        <button
          className={`${styles.button} ${styles.secondary}`}
          type="button"
          onClick={() => {
            void onSync()
          }}
          disabled={state.status === 'disconnected'}
          aria-label={`Manual sync ${platform}`}
        >
          Manual Sync
        </button>
        <button
          className={`${styles.button} ${styles.secondary}`}
          type="button"
          onClick={() => {
            void onDisconnect()
          }}
          aria-label={`Disconnect ${platform}`}
        >
          Disconnect
        </button>
      </div>

      <div className={styles.log}>
        <strong>Status:</strong> {statusCopy[state.status]}{' '}
        {state.lastSync && `• Last sync ${state.lastSync}`}
        {state.message ? ` • ${state.message}` : null}
      </div>
    </div>
  )
}
