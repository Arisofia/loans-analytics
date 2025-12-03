'use client'

import styles from './analytics.module.css'
import type { TreemapEntry } from '@/types/analytics'

type Props = {
  entries: TreemapEntry[]
}

export function TreemapVisualization({ entries }: Props) {
  return (
    <section className={styles.section}>
      <div className={styles.sectionHeader}>
        <p className={styles.sectionTitle}>Segment treemap</p>
        <p className={styles.sectionCopy}>
          Weighted principal balances per status to inform marketing and underwriting.
        </p>
      </div>
      <div className={styles.treemapList}>
        {entries.map((entry) => (
          <div className={styles.treemapItem} key={entry.label}>
            <span>{entry.label}</span>
            <span style={{ color: entry.color, fontWeight: 600 }}>
              {entry.value.toLocaleString()}
            </span>
          </div>
        ))}
      </div>
    </section>
  )
}
