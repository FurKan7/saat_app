'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { Layout } from '@/components/Layout'
import { Button } from '@/components/ui/button'
import { getSupabaseBrowser, isSupabaseConfigured } from '@/lib/supabase'
import { persistAccessToken } from '@/lib/auth-actions'

export default function ResetPasswordPage() {
  const router = useRouter()
  const [ready, setReady] = useState(false)
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    const supa = getSupabaseBrowser()
    if (!supa) {
      setReady(false)
      return
    }
    // Recovery links put tokens in the URL hash; getSession picks them up.
    supa.auth.getSession().then(({ data: { session } }) => {
      setReady(!!session)
    })
    const {
      data: { subscription },
    } = supa.auth.onAuthStateChange((event) => {
      if (event === 'PASSWORD_RECOVERY' || event === 'SIGNED_IN') {
        setReady(true)
      }
    })
    return () => subscription.unsubscribe()
  }, [])

  const handleUpdate = async () => {
    setError(null)
    const supa = getSupabaseBrowser()
    if (!supa) return
    if (password.length < 6) {
      setError('Use at least 6 characters.')
      return
    }
    if (password !== confirm) {
      setError('Passwords do not match.')
      return
    }
    setLoading(true)
    try {
      const { error: e } = await supa.auth.updateUser({ password })
      if (e) throw e
      const { data: s } = await supa.auth.getSession()
      const token = s.session?.access_token
      if (token) persistAccessToken(token)
      router.push('/dashboard')
    } catch (e: any) {
      setError(e?.message ?? 'Could not update password.')
    } finally {
      setLoading(false)
    }
  }

  if (!isSupabaseConfigured()) {
    return (
      <Layout>
        <div className="max-w-md mx-auto px-4 py-16 text-center text-sm text-gray-600">Supabase is not configured.</div>
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="max-w-md mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Set new password</h1>
        <p className="text-gray-500 mb-6">Choose a new password for your WatchHub account.</p>

        {!ready ? (
          <div className="rounded-2xl border border-gray-200 bg-white shadow-sm p-6 text-sm text-gray-600 space-y-3">
            <p>Waiting for a valid recovery session…</p>
            <p>
              Open this page from the link in your email. If the link expired, request a new one from{' '}
              <Link href="/login/forgot-password" className="text-gray-900 font-medium underline">
                Forgot password
              </Link>
              .
            </p>
          </div>
        ) : (
          <div className="rounded-2xl border border-gray-200 bg-white shadow-sm p-6 space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">New password</label>
              <input
                type="password"
                autoComplete="new-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-gray-900"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Confirm password</label>
              <input
                type="password"
                autoComplete="new-password"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                className="w-full rounded-xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-gray-900"
              />
            </div>
            {error && <p className="text-sm text-red-600">{error}</p>}
            <Button onClick={handleUpdate} disabled={loading} className="w-full py-3">
              {loading ? 'Saving…' : 'Update password'}
            </Button>
          </div>
        )}
      </div>
    </Layout>
  )
}
