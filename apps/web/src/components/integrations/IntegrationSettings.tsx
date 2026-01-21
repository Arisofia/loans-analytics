'use client'

import { useMemo, useState } from 'react'

import { BulkTokenInput } from './BulkTokenInput'
import IntegrationCard from './IntegrationCard'
import { SlideLayout } from './SlideLayout'
import {
  PLATFORMS,
  PLATFORM_LABELS,
  type Platform,
  type TokenStatus,
} from '@/lib/integrations/constants'
import type { BulkProcessResult, BulkTokenItem, TokenState } from '@/types/integrations'

import styles from './IntegrationSettings.module.css'

export type StatusRow = {
  platform: Platform
  status?: TokenStatus
  account_id?: string
  last_sync?: string
  last_sync_status?: { message?: string }
  id?: string
}



const initialState: Record<Platform, TokenState> = PLATFORMS.reduce(
  (all, platform) => ({ ...all, [platform]: { status: 'disconnected' } }),
  {} as Record<Platform, TokenState>
)

export function IntegrationSettings() {
  const [projectId, setProjectId] = useState('demo-project')
  const [tokenState] = useState<Record<Platform, TokenState>>(initialState)
  const [bulkOpen] = useState(false)
  const [logEntries] = useState<string[]>([])
  const [loadingStatus] = useState(false)

  const statusSummary = useMemo(
    () =>
      PLATFORMS.map(
        (platform) => `${PLATFORM_LABELS[platform]}: ${tokenState[platform].status}`
      ).join(' • '),
    [tokenState]
  )

  return (
    <SlideLayout
      description="Configure provider access with per-platform tokens, safe bulk intake, and explicit sync controls. Tokens are encrypted before storage and every action is logged for auditability."
      actions={
        <>
          <div className={styles.toolbar}>
            <button className={styles.badge} type="button">
              {loadingStatus ? 'Refreshing status...' : 'Secure & audited'}
            </button>
            <div className={styles.labelledInput}>
              <label htmlFor="project-id">Project ID</label>
              <input
                id="project-id"
                value={projectId}
                onChange={(event) => setProjectId(event.target.value)}
                placeholder="Project identifier"
              />
            </div>
            <button
              className={styles.primaryButton}
              type="button"
              onClick={() => {
                void refreshStatus()
              }}
            >
              Refresh status
            </button>
            <button
              className={styles.secondaryButton}
              type="button"
              onClick={() => setBulkOpen(true)}
            >
              Bulk connect
            </button>
          </div>
        </>
      }
    >
      <>
        <div className={styles.grid}>
          {PLATFORMS.map((platform) => (
            <IntegrationCard
              key={platform}
              platform={platform}
              state={tokenState[platform]}
              onChange={(changes) => setPlatformState(platform, changes)}
              onConnect={() => connectPlatform(platform)}
              onDisconnect={() => disconnectPlatform(platform)}
              onSync={() => syncPlatform(platform)}
            />
          ))}
        </div>

        <div className={styles.syncLog} aria-live="polite">
          <div className={styles.summaryRow}>
            <strong>Progress log</strong>
            <span>{statusSummary}</span>
          </div>
          {logEntries.length === 0 ? (
            <p>No events yet.</p>
          ) : (
            logEntries.map((entry, index) => <div key={`${index}-${entry}`}>{entry}</div>)
          )}
        </div>

        <BulkTokenInput
          open={bulkOpen}
          onClose={() => setBulkOpen(false)}
          onProcessItem={handleBulkProcessItem}
        />
      </>
    </SlideLayout>
  )



  const connectPlatform = async (platform: Platform) => {
    const details = tokenState[platform]
    if (!details.token) {
      setPlatformState(platform, { message: 'Token is required for connection' })
      return
    }
    setPlatformState(platform, { status: 'syncing', message: 'Validating token...' })
    try {
      const result = await callEdgeFunction<{ id?: string }>('/connect', {
        projectId,
        platform,
        token: details.token,
        accountId: details.accountId,
      })
      const tokenId = result.id
      setPlatformState(platform, {
        status: 'connected',
        message: 'Connected — starting initial sync',
        tokenId,
      })
      appendLog(`${PLATFORM_LABELS[platform]} connected`)
      if (tokenId) {
        await callEdgeFunction('/sync', { tokenId })
        setPlatformState(platform, {
          message: 'Sync triggered',
          lastSync: new Date().toISOString(),
        })
      }
    } catch (error) {
      const detail = error instanceof Error ? error.message : 'Connect failed'
      setPlatformState(platform, { status: 'error', message: detail })
      appendLog(`${PLATFORM_LABELS[platform]} connection failed`)
    }
  }

  const disconnectPlatform = async (platform: Platform) => {
    const { tokenId } = tokenState[platform]
    setPlatformState(platform, { status: 'syncing', message: 'Disconnecting...' })
    try {
      await callEdgeFunction('/disconnect', { tokenId, platform })
      setPlatformState(platform, {
        status: 'disconnected',
        message: 'Disconnected',
        tokenId: undefined,
      })
      appendLog(`${PLATFORM_LABELS[platform]} disconnected`)
    } catch (error) {
      const detail = error instanceof Error ? error.message : 'Unable to disconnect'
      setPlatformState(platform, { status: 'error', message: detail })
    }
  }

  const syncPlatform = async (platform: Platform) => {
    const tokenId = tokenState[platform].tokenId
    if (!tokenId) {
      setPlatformState(platform, { message: 'No token found for sync' })
      return
    }
    setPlatformState(platform, { status: 'syncing', message: 'Sync in progress...' })
    try {
      await callEdgeFunction('/sync', { tokenId })
      setPlatformState(platform, {
        status: 'connected',
        message: 'Sync queued',
        lastSync: new Date().toISOString(),
      })
      appendLog(`${PLATFORM_LABELS[platform]} sync dispatched`)
    } catch (error) {
      const detail = error instanceof Error ? error.message : 'Sync failed'
      setPlatformState(platform, { status: 'error', message: detail })
    }
  }

  const handleBulkProcessItem = async (item: BulkTokenItem): Promise<BulkProcessResult> => {
    try {
      const response = await callEdgeFunction<{ id?: string }>('/connect', {
        projectId,
        platform: item.platform,
        token: item.token,
        accountId: item.accountId,
      })
      const tokenId = response.id
      if (tokenId) {
        await callEdgeFunction('/sync', { tokenId })
      }
      appendLog(`Bulk connected ${PLATFORM_LABELS[item.platform]}`)
      return {
        item,
        status: 'success',
        tokenId,
        detail: 'Connected & sync triggered',
      }
    } catch (error) {
      const detail = error instanceof Error ? error.message : 'Bulk connect failed'
      appendLog(`Bulk connect failed for ${PLATFORM_LABELS[item.platform]}`)
      return { item, status: 'error', detail }
    }
  }

  return (
    <SlideLayout
      description="Configure provider access with per-platform tokens, safe bulk intake, and explicit sync controls. Tokens are encrypted before storage and every action is logged for auditability."
      actions={
        <div className={styles.toolbar}>
          <button className={styles.badge} type="button">
            {loadingStatus ? 'Refreshing status...' : 'Secure & audited'}
          </button>
          <div className={styles.labelledInput}>
            <label htmlFor="project-id">Project ID</label>
            <input
              id="project-id"
              value={projectId}
              onChange={(event) => setProjectId(event.target.value)}
              placeholder="Project identifier"
            />
          </div>
            {/* <button
              className={styles.primaryButton}
              type="button"
              onClick={() => {
                void refreshStatus()
              }}
            >
              Refresh status
            </button> */}
          <button
            className={styles.secondaryButton}
            type="button"
            onClick={() => setBulkOpen(true)}
          >
            Bulk connect
          </button>
        </div>
      }
    >
      <div className={styles.grid}>
        {PLATFORMS.map((platform) => (
          <IntegrationCard
            key={platform}
            platform={platform}
            state={tokenState[platform]}
            onChange={(changes) => setPlatformState(platform, changes)}
            onConnect={() => connectPlatform(platform)}
            onDisconnect={() => disconnectPlatform(platform)}
            onSync={() => syncPlatform(platform)}
          />
        ))}
      </div>

      <div className={styles.syncLog} aria-live="polite">
        <div className={styles.summaryRow}>
          <strong>Progress log</strong>
          <span>{statusSummary}</span>
        </div>
        {logEntries.length === 0 ? (
          <p>No events yet.</p>
        ) : (
          logEntries.map((entry, index) => <div key={`${index}-${entry}`}>{entry}</div>)
        )}
      </div>

      <BulkTokenInput
        open={bulkOpen}
        onClose={() => setBulkOpen(false)}
        onProcessItem={handleBulkProcessItem}
      />
    </SlideLayout>
  )
}
