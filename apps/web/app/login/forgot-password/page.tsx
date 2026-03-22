'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Layout } from '@/components/Layout'
import { Button } from '@/components/ui/button'
import { getSupabaseBrowser, isSupabaseConfigured } from '@/lib/supabase'
import { getAuthRedirectBaseUrl } from '@/lib/site-url'

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [info, setInfo] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async () => {
    setError(null)
    setInfo(null)
    const supa = getSupabaseBrowser()
    if (!supa) {
      setError('Supabase is not configured.')
      return
    }
    const em = email.trim()
    if (!em) {
      setError('Enter your email address.')
      return
    }
    setLoading(true)
    try {
      const redirectTo = `${getAuthRedirectBaseUrl()}/auth/reset-password`
      const { error: e } = await supa.auth.resetPasswordForEmail(em, { redirectTo })
      if (e) throw e
      setInfo(
        'If an account exists for that email, you will receive a link to choose a new password. Check spam folders too.'
      )
    } catch (e: any) {
      setError(e?.message ?? 'Could not send reset email.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Layout>
      <div className="max-w-md mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Forgot password</h1>
        <p className="text-gray-500 mb-6">
          Enter the email you used for WatchHub. We will send a link to reset your password.
        </p>

        {!isSupabaseConfigured() && (
          <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900 mb-6">
            Supabase is not configured in this app build.
          </div>
        )}

        <div className="rounded-2xl border border-gray-200 bg-white shadow-sm p-6 space-y-5">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
            <input
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-gray-900"
              placeholder="you@example.com"
            />
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          {info && <p className="text-sm text-gray-600">{info}</p>}
          <Button onClick={handleSubmit} disabled={loading} className="w-full py-3">
            {loading ? 'Sending…' : 'Send reset link'}
          </Button>
          <p className="text-sm text-center text-gray-500">
            <Link href="/login" className="text-gray-900 font-medium hover:underline">
              Back to sign in
            </Link>
          </p>
        </div>

        <p className="text-xs text-gray-400 mt-6 text-center">
          Add <code className="bg-gray-100 px-1 rounded">{getAuthRedirectBaseUrl()}/auth/reset-password</code> to
          Supabase → Authentication → URL configuration → Redirect URLs.
        </p>
      </div>
    </Layout>
  )
}
