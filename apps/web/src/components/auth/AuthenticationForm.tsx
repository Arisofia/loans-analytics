'use client'

import { useState } from 'react'

import { getSupabaseClient } from '@/lib/supabase/client'

type AuthStatus = 'idle' | 'submitting' | 'success' | 'error'

type AuthFormState = {
  email: string
  password: string
}

export const AuthenticationForm = () => {
  const [formState, setFormState] = useState<AuthFormState>({
    email: '',
    password: '',
  })
  const [status, setStatus] = useState<AuthStatus>('idle')
  const [message, setMessage] = useState<string>('')

  const handleChange = (key: keyof AuthFormState, value: string) => {
    setFormState((prev) => ({ ...prev, [key]: value }))
  }

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setStatus('submitting')
    setMessage('')

    const supabase = getSupabaseClient()
    const { error } = await supabase.auth.signInWithPassword({
      email: formState.email.trim(),
      password: formState.password,
    })

    if (error) {
      setStatus('error')
      setMessage(error.message)
      return
    }

    setStatus('success')
    setMessage('Authentication complete. Redirecting...')
  }

  return (
    <form className="space-y-4" onSubmit={handleSubmit}>
      <div className="space-y-1">
        <label className="text-xs font-semibold text-slate-200" htmlFor="email">
          Email
        </label>
        <input
          className="w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100"
          id="email"
          onChange={(event) => handleChange('email', event.target.value)}
          type="email"
          value={formState.email}
        />
      </div>
      <div className="space-y-1">
        <label
          className="text-xs font-semibold text-slate-200"
          htmlFor="password"
        >
          Password
        </label>
        <input
          className="w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100"
          id="password"
          onChange={(event) => handleChange('password', event.target.value)}
          type="password"
          value={formState.password}
        />
      </div>
      <button
        className="rounded bg-indigo-500 px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-700"
        disabled={status === 'submitting'}
        type="submit"
      >
        {status === 'submitting' ? 'Signing in...' : 'Sign in'}
      </button>
      {message && (
        <p
          className={
            status === 'error'
              ? 'text-xs text-rose-300'
              : 'text-xs text-emerald-300'
          }
        >
          {message}
        </p>
      )}
    </form>
  )
}
