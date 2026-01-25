'use client'

import { FluidBackground } from '@/components/FluidBackground'
import { cn } from '@/lib/cn'
import { gradients, typography } from '@/utils/designSystem'
import type { ReactNode } from 'react'

interface SlideLayoutProps {
  section: string
  title?: string
  subtitle?: string
  slideNumber?: number
  children: ReactNode
  className?: string
}

export function SlideLayout({
  section,
  title,
  subtitle,
  slideNumber,
  children,
  className,
}: SlideLayoutProps) {
  return (
    <div className="relative h-full w-full overflow-hidden bg-[#030E19]">
      <FluidBackground />

      <div className="relative z-10 flex h-full flex-col gap-8 px-8 py-10 sm:px-16 sm:py-12">
        <div className="flex items-center justify-between">
          <div className="flex flex-col gap-2">
            <span style={typography.styles.sectionLabel}>{section}</span>
            {title && (
              <h1
                className="font-bold"
                style={{
                  ...typography.styles.slideTitle,
                  background: gradients.title,
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                }}
              >
                {title}
              </h1>
            )}
            {subtitle && <p style={typography.styles.body}>{subtitle}</p>}
          </div>

          {typeof slideNumber === 'number' && (
            <div className="shrink-0" style={typography.styles.slideNumber}>
              {slideNumber.toString().padStart(2, '0')}
            </div>
          )}
        </div>

        <div
          className={cn(
            'flex flex-1 flex-col gap-8 rounded-2xl border border-white/5 bg-white/5 p-6 backdrop-blur-sm shadow-lg shadow-black/30 transition duration-500',
            className
          )}
        >
          {children}
        </div>
      </div>
    </div>
  )
}
