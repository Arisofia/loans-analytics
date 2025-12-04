'use client'

import { useCallback, useMemo, useState } from 'react'

import {
  PLATFORMS,
  PLATFORM_LABELS,
  type Platform,
  type TokenStatus,
} from '@/lib/integrations/constants'
import type { BulkProcessResult, BulkTokenItem } from '@/types/integrations'

import styles from './BulkTokenInput.module.css'

type BulkTokenInputProps = {
  open: boolean
  onClose: () => void
  onProcessItem: (item: BulkTokenItem) => Promise<BulkProcessResult>
}

type ItemStatus = TokenStatus | 'pending' | 'success' | 'retrying' | 'error'

const defaultRow = 'platform,token,accountId(optional)'

export function BulkTokenInput({ open, onClose, onProcessItem }: BulkTokenInputProps) {
  const [rawInput, setRawInput] = useState('')
  const [items, setItems] = useState<BulkTokenItem[]>([])
  const [processing, setProcessing] = useState(false)
  const [summary, setSummary] = useState<string>('')

  const parsedItems = useMemo(() => parseInput(rawInput.trim()), [rawInput])

  const updateItem = useCallback((index: number, changes: Partial<BulkTokenItem>) => {
    setItems((current) =>
      current.map((item, idx) => (idx === index ? { ...item, ...changes } : item))
    )
  }, [])

  const processItems = async (list: BulkTokenItem[]) => {
    const results: BulkProcessResult[] = []
    for (let index = 0; index < list.length; index++) {
      const entry = list[index]
      let attempts = 0
      let success = false

      while (attempts < 3 && !success) {
        attempts += 1
        updateItem(index, {
          status: attempts > 1 ? ('retrying' as ItemStatus) : ('pending' as ItemStatus),
          attempts,
          message: `${new Date().toLocaleTimeString()} • attempt ${attempts}`,
        })
        try {
          const result = await onProcessItem(entry)
          success = result.status === 'success'
          updateItem(index, {
            status:
              result.status === 'success' ? ('success' as ItemStatus) : ('error' as ItemStatus),
            message: result.detail,
            resultId: result.tokenId,
          })
          if (result.status === 'success') {
            results.push(result)
          } else if (attempts >= 3) {
            results.push({ ...result, status: 'error' })
          } else {
            await waitForDelay(attempts)
          }
        } catch (error) {
          const detail = error instanceof Error ? error.message : 'Unable to connect'
          updateItem(index, {
            status: attempts >= 3 ? ('error' as ItemStatus) : ('retrying' as ItemStatus),
            attempts,
            message: `${new Date().toLocaleTimeString()} • ${detail}`,
          })
          if (attempts >= 3) {
            results.push({ item: entry, status: 'error', detail })
          } else {
            await waitForDelay(attempts)
          }
        }
      }

      if (!success && !results.find((result) => result.item === entry)) {
        results.push({ item: entry, status: 'error', detail: 'Max retries reached' })
      }
    }

    return results
  }

  const handleProcess = async () => {
    const list = parsedItems
    setItems(list.map((item) => ({ ...item, status: 'pending' as ItemStatus, attempts: 0 })))
    setProcessing(true)
    setSummary('')

    const results = await processItems(list)
    const successes = results.filter((result) => result.status === 'success').length
    const errors = results.filter((result) => result.status === 'error').length
    const successText = `${successes} / ${list.length} tokens processed successfully.`
    const errorText = errors ? `${errors} failed — review details before closing.` : ''
    setSummary([successText, errorText].filter(Boolean).join(' '))
    setProcessing(false)

    if (errors === 0 && list.length > 0) {
      setTimeout(onClose, 900)
    }
  }

  const retryFailures = async () => {
    const failures = items.filter((item) => item.status === 'error')
    if (!failures.length) return
    setProcessing(true)
    setSummary('')
    const refreshed = failures.map((item) => ({
      ...item,
      status: 'pending' as ItemStatus,
      attempts: 0,
    }))
    setItems((current) =>
      current.map((existing) =>
        existing.status === 'error'
          ? { ...existing, status: 'pending' as ItemStatus, attempts: 0 }
          : existing
      )
    )
    const results = await processItems(refreshed)
    const errors = results.filter((result) => result.status === 'error').length
    const successText = `${results.length - errors} / ${failures.length} retried tokens connected.`
    const errorText = errors ? `${errors} still failing.` : ''
    setSummary([successText, errorText].filter(Boolean).join(' '))
    setProcessing(false)
  }

  if (!open) return null

  return (
    <div className={styles.backdrop} role="dialog" aria-modal>
      <div className={styles.modal}>
        <div className={styles.header}>
          <h3>Bulk token intake</h3>
          <p className={styles.summary}>One line per token: platform,token,accountId?</p>
        </div>
        <div className={styles.body}>
          <div className={styles.inputArea}>
            <label htmlFor="bulk-token-input">Tokens</label>
            <textarea
              id="bulk-token-input"
              className={styles.textarea}
              value={rawInput}
              onChange={(event) => setRawInput(event.target.value)}
              placeholder={defaultRow}
              disabled={processing}
            />
          </div>
          <div className={styles.progressList} aria-live="polite">
            {items.length === 0 && <p>No items yet. Paste tokens to begin.</p>}
            {items.map((item, index) => (
              <div key={`${item.platform}-${index}`} className={styles.progressItem}>
                <div>
                  <strong>{PLATFORM_LABELS[item.platform]}</strong> —{' '}
                  {item.accountId || 'No account ID'}
                </div>
                <div>{item.message || 'Waiting to process'}</div>
                <div>Status: {item.status}</div>
                {item.attempts ? <div>Attempts: {item.attempts}</div> : null}
              </div>
            ))}
          </div>
        </div>
        <div className={styles.footer}>
          <div className={styles.summary}>{summary}</div>
          <div className={styles.actions}>
            <button
              className={`${styles.button} ${styles.secondary}`}
              type="button"
              onClick={onClose}
              disabled={processing}
            >
              Close
            </button>
            <button
              className={`${styles.button} ${styles.secondary}`}
              type="button"
              onClick={() => {
                void retryFailures()
              }}
              disabled={processing || !items.some((item) => item.status === 'error')}
            >
              Retry failures
            </button>
            <button
              className={`${styles.button} ${styles.primary}`}
              type="button"
              onClick={() => {
                void handleProcess()
              }}
              disabled={processing || !parsedItems.length}
            >
              {processing ? 'Processing...' : 'Connect all'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

function parseInput(input: string): BulkTokenItem[] {
  const rows = input
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => line.split(',').map((segment) => segment.trim()))
    .filter((parts) => parts.length >= 2)

  const validItems: BulkTokenItem[] = []

  for (const [rawPlatform, token, accountId] of rows) {
    const normalizedPlatform = rawPlatform?.toLowerCase() as Platform | undefined
    if (!normalizedPlatform || !PLATFORMS.includes(normalizedPlatform)) continue

    validItems.push({
      platform: normalizedPlatform,
      token: token ?? '',
      accountId: accountId ?? '',
      status: 'pending',
      attempts: 0,
    })
  }

  return validItems
}

function waitForDelay(attempt: number) {
  const base = 260
  const delay = base * Math.pow(2, attempt - 1)
  return new Promise((resolve) => setTimeout(resolve, delay))
}
