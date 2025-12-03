import type { ReactNode } from 'react'

import styles from './SlideLayout.module.css'

type SlideLayoutProps = {
  description: string
  actions?: ReactNode
  children: ReactNode
}

export function SlideLayout({ description, actions, children }: SlideLayoutProps) {
  return (
    <div className={styles.layout}>
      <div className={styles.topRow}>
        <p className={styles.copy}>{description}</p>
        {actions && <div className={styles.actions}>{actions}</div>}
      </div>
      <div className={styles.contentPanel}>{children}</div>
    </div>
  )
}
