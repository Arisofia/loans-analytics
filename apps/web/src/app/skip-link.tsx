'use client'

import { useCallback, type MouseEventHandler } from 'react'

interface SkipLinkProps {
  targetId?: string
}

export function SkipLink({ targetId = 'main-content' }: SkipLinkProps) {
  const handleClick = useCallback<MouseEventHandler<HTMLAnchorElement>>(
    (event) => {
      const target = document.getElementById(targetId)

      if (!target) {
        return
      }

      event.preventDefault()
      target.focus({ preventScroll: true })

      const prefersReducedMotion =
        typeof window !== 'undefined' &&
        typeof window.matchMedia === 'function' &&
        window.matchMedia('(prefers-reduced-motion: reduce)').matches

      target.scrollIntoView({
        behavior: prefersReducedMotion ? 'auto' : 'smooth',
        block: 'start',
      })
    },
    [targetId],
  )

  return (
    <a className="skipLink" href={`#${targetId}`} onClick={handleClick}>
      Skip to main content
    </a>
  )
}
