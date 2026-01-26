'use client'

import { useState } from 'react'

import { getSupabaseClient } from '@/lib/supabase/client'

type AccountConfiguration = {
  displayName: string
  region: string
  notificationEmail: string
}

type SaveStatus = 'idle' | 'saving' | 'success' | 'error'

export const AccountConfigurationForm = () => {
  const [formState, setFormState] = useState<AccountConfiguration>({
    displayName: '',
    region: 'north-america',
    notificationEmail: '',
  })
  const [status, setStatus] = useState<SaveStatus>('idle')
  const [message, setMessage] = useState<string>('')

  const handleChange = (key: keyof AccountConfiguration, value: string) => {
    setFormState((prev) => ({ ...prev, [key]: value }))
  }

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setStatus('saving')
    setMessage('')

    const supabase = getSupabaseClient()
    const {
      data: { user },
      error: userError,
    } = await supabase.auth.getUser()

    if (userError || !user) {
      setStatus('error')
      setMessage(userError?.message ?? 'Unable to load authenticated user.')
      return
    }

    const { error } = await supabase.from('account_settings').upsert({
      user_id: user.id,
      display_name: formState.displayName.trim(),
      region: formState.region,
      notification_email: formState.notificationEmail.trim(),
    })

    if (error) {
      setStatus('error')
      setMessage(error.message)
      return
    }

    setStatus('success')
    setMessage('Account configuration updated.')
  }

  return (
    <form className="space-y-4" onSubmit={handleSubmit}>
      <div className="space-y-1">
        <label
          className="text-xs font-semibold text-slate-200"
          htmlFor="displayName"
        >
          Account display name
        </label>
        <input
          className="w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100"
          id="displayName"
          onChange={(event) => handleChange('displayName', event.target.value)}
          type="text"
          value={formState.displayName}
        />
      </div>
      <div className="space-y-1">
        <label
          className="text-xs font-semibold text-slate-200"
          htmlFor="region"
        >
          Primary region
        </label>
        <select
          className="w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100"
          id="region"
          onChange={(event) => handleChange('region', event.target.value)}
          value={formState.region}
        >
          <option value="north-america">North America</option>
          <option value="latin-america">Latin America</option>
          <option value="emea">EMEA</option>
          <option value="apac">APAC</option>
        </select>
      </div>
      <div className="space-y-1">
        <label
          className="text-xs font-semibold text-slate-200"
          htmlFor="notificationEmail"
        >
          Notification email
        </label>
        <input
          className="w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100"
          id="notificationEmail"
          onChange={(event) =>
            handleChange('notificationEmail', event.target.value)
          }
          type="email"
          value={formState.notificationEmail}
        />
      </div>
      <button
        className="rounded bg-indigo-500 px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-700"
        disabled={status === 'saving'}
        type="submit"
      >
        {status === 'saving' ? 'Saving...' : 'Save configuration'}
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
