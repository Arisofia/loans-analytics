'use client'

export function FluidBackground() {
  return (
    <div className="absolute inset-0 overflow-hidden">
      <div className="absolute -left-20 -top-20 h-80 w-80 rounded-full bg-[#5a6dff]/30 blur-[120px]" />
      <div className="absolute right-0 top-10 h-96 w-96 rounded-full bg-[#c1a6ff]/20 blur-[140px]" />
      <div className="absolute left-1/3 bottom-0 h-64 w-64 rounded-full bg-[#0ea5e9]/25 blur-[120px]" />
    </div>
  )
}
