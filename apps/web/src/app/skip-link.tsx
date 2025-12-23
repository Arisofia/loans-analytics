import React from 'react'

interface SkipLinkProps {
  targetId?: string
  className?: string
}

export const SkipLink: React.FC<SkipLinkProps> = ({
  targetId = 'main-content',
  className = 'skip-link',
}) => {
  const handleClick = (e: React.MouseEvent<HTMLAnchorElement>) => {
    const target = document.getElementById(targetId)
    if (target) {
      e.preventDefault()
      target.focus({ preventScroll: false })
      target.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }

  return (
    <a href={`#${targetId}`} className={className} onClick={handleClick} tabIndex={0}>
      Skip to main content
    </a>
  )
}
