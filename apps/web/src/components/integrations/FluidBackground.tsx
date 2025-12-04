import type { ReactNode } from 'react'

import styles from './FluidBackground.module.css'

type FluidBackgroundProps = {
  children?: ReactNode
}

export function FluidBackground({ children }: FluidBackgroundProps) {
  return (
    <div className={styles.background} aria-hidden>
      <div className={`${styles.blob} ${styles.blobPurple}`} />
      <div className={`${styles.blob} ${styles.blobBlue}`} />
      <div className={`${styles.blob} ${styles.blobTeal}`} />
      {children}
    </div>
  )
}
