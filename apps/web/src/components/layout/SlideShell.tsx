'use client'

import type { ReactNode } from 'react'

interface SlideShellProps {
  children: ReactNode
  slideNumber?: number
}

export function SlideShell({ children, slideNumber }: SlideShellProps) {
  return (
    <div className="flex h-full min-h-screen w-full items-stretch justify-center bg-[#020617] px-4 py-6">
      <div className="relative h-[900px] w-full max-w-[1600px] overflow-hidden rounded-[32px] bg-gradient-to-br from-[#040712] via-[#050816] to-[#020617] p-8 shadow-[0_40px_120px_rgba(0,0,0,0.75)]">
        <div className="pointer-events-none absolute inset-0 opacity-70">
          <div className="absolute -left-32 top-10 h-72 w-72 rounded-full bg-[#8B5CF6]/35 blur-[110px]" />
          <div className="absolute right-0 bottom-0 h-80 w-80 rounded-full bg-[#EC4899]/25 blur-[110px]" />
        </div>

        <div className="relative flex h-full w-full flex-col gap-8">{children}</div>

        {slideNumber !== undefined && (
          <div className="absolute bottom-6 right-8 text-sm font-medium text-slate-400/80">
            {slideNumber}
          </div>
        )}
      </div>
    </div>
  )
}
