const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || ''

export const projectId = (() => {
  try {
    const url = new URL(supabaseUrl)
    const hostnameParts = url.hostname.split('.')
    // If the hostname has at least 3 parts, assume the first is the project ID (e.g., <project>.supabase.co)
    // For custom domains, you may need to adjust this logic.
    return hostnameParts.length >= 3 ? hostnameParts[0] : ''
  } catch {
    return ''
  }
})()

export const publicAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ''

export const supabaseConfigAvailable = Boolean(projectId && publicAnonKey)
