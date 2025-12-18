'use client'

import type { ReactNode } from 'react'

import { FluidBackground } from './FluidBackground'
import styles from './SlideShell.module.css'

type SlideShellProps = {
  slideNumber: number
  title: string
  subtitle: string
  children: ReactNode
}

export function SlideShell({ slideNumber, title, subtitle, children }: SlideShellProps) {
  return (
    <div className={styles.shell}>
      <FluidBackground />
      <div className={styles.frame}>
        <div className={styles.header}>
          <div className={styles.titles}>
            <p className={styles.subtitle}>{subtitle}</p>
            <h1 className={styles.title}>{title}</h1>
          </div>
        </div>
        {children}
        <div className={styles.watermark}>0{slideNumber}</div>
      </div>
    </div>
  )
}
