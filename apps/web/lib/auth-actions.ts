import type { QueryClient } from '@tanstack/react-query'
import { getSupabaseBrowser } from '@/lib/supabase'

export function persistAccessToken(token: string | null) {
  if (typeof window === 'undefined') return
  if (token) {
    localStorage.setItem('supabase_token', token)
  } else {
    localStorage.removeItem('supabase_token')
  }
}

export async function signOutClient(queryClient: QueryClient) {
  persistAccessToken(null)
  const supa = getSupabaseBrowser()
  if (supa) {
    await supa.auth.signOut()
  }
  queryClient.removeQueries({ queryKey: ['profile-me'] })
  queryClient.removeQueries({ queryKey: ['profile-collections'] })
}
