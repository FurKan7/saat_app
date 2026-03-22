'use client'

import { useEffect } from 'react'
import { getSupabaseBrowser } from '@/lib/supabase'
import { persistAccessToken } from '@/lib/auth-actions'

/**
 * Keeps `localStorage.supabase_token` in sync with Supabase Auth sessions
 * so axios continues to send Bearer tokens after refresh.
 */
export function AuthProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    const supa = getSupabaseBrowser()
    if (!supa) return

    supa.auth.getSession().then(({ data: { session } }) => {
      if (session?.access_token) persistAccessToken(session.access_token)
    })

    const {
      data: { subscription },
    } = supa.auth.onAuthStateChange((_event, session) => {
      persistAccessToken(session?.access_token ?? null)
    })

    return () => subscription.unsubscribe()
  }, [])

  return <>{children}</>
}
