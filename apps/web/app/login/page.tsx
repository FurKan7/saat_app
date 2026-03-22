'use client'

import { Suspense, useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'
import { useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Layout } from '@/components/Layout'
import { Button } from '@/components/ui/button'
import { getSupabaseBrowser, isSupabaseConfigured } from '@/lib/supabase'
import { persistAccessToken } from '@/lib/auth-actions'

function LoginForm() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const queryClient = useQueryClient()
  const nextPath = (() => {
    const raw = searchParams.get('next')
    if (!raw || !raw.startsWith('/') || raw.startsWith('//')) return '/dashboard'
    return raw
  })()

  const [mode, setMode] = useState<'signin' | 'signup'>('signin')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [devToken, setDevToken] = useState('')
  const [showDev, setShowDev] = useState(false)

  useEffect(() => {
    if (!isSupabaseConfigured()) setShowDev(true)
  }, [])
  const [error, setError] = useState<string | null>(null)
  const [info, setInfo] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const supaConfigured = isSupabaseConfigured()

  const finishWithToken = async (accessToken: string) => {
    persistAccessToken(accessToken)
    await api.get('/profile/me')
    queryClient.invalidateQueries({ queryKey: ['profile-me'] })
    router.push(nextPath.startsWith('/') ? nextPath : '/dashboard')
  }

  const handleSupabaseAuth = async () => {
    setError(null)
    setInfo(null)
    const supa = getSupabaseBrowser()
    if (!supa) {
      setError('Supabase is not configured. Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY.')
      return
    }
    const em = email.trim()
    const pw = password
    if (!em || !pw) {
      setError('Enter email and password.')
      return
    }
    if (mode === 'signup' && pw !== confirm) {
      setError('Passwords do not match.')
      return
    }
    setLoading(true)
    try {
      if (mode === 'signup') {
        const { data, error: e } = await supa.auth.signUp({ email: em, password: pw })
        if (e) throw e
        if (data.session?.access_token) {
          await finishWithToken(data.session.access_token)
          return
        }
        setInfo(
          'Account created. If email confirmation is enabled in Supabase, check your inbox and then sign in.'
        )
        setMode('signin')
      } else {
        const { data, error: e } = await supa.auth.signInWithPassword({ email: em, password: pw })
        if (e) throw e
        const token = data.session?.access_token
        if (!token) throw new Error('No session returned. Confirm your email if required.')
        await finishWithToken(token)
      }
    } catch (e: any) {
      setError(e?.message ?? 'Authentication failed')
    } finally {
      setLoading(false)
    }
  }

  const handleDevToken = async () => {
    setError(null)
    setInfo(null)
    const t = devToken.trim()
    if (!t) {
      setError('Paste a JWT or use email sign-in above.')
      return
    }
    setLoading(true)
    try {
      await finishWithToken(t)
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? e?.message ?? 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-md mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h1 className="text-3xl font-bold text-gray-900 mb-2">
        {mode === 'signin' ? 'Sign in' : 'Create account'}
      </h1>
      <p className="text-gray-500 mb-6">
        {mode === 'signin'
          ? 'Use your WatchHub account to manage collections and uploads.'
          : 'Sign up to save watch collections and track identifications.'}
      </p>

      {!supaConfigured && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900 mb-6">
          Supabase env vars are missing. Copy <code className="text-xs">apps/web/.env.example</code> to{' '}
          <code className="text-xs">apps/web/.env.local</code> and add your project URL and anon key. You can still
          use the developer token field below.
        </div>
      )}

      <div className="rounded-2xl border border-gray-200 bg-white shadow-sm p-6 space-y-5">
        {supaConfigured && (
          <>
            <div className="flex rounded-xl border border-gray-200 p-1 bg-gray-50">
              <button
                type="button"
                onClick={() => {
                  setMode('signin')
                  setError(null)
                  setInfo(null)
                }}
                className={`flex-1 rounded-lg py-2 text-sm font-medium transition-colors ${
                  mode === 'signin' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Sign in
              </button>
              <button
                type="button"
                onClick={() => {
                  setMode('signup')
                  setError(null)
                  setInfo(null)
                }}
                className={`flex-1 rounded-lg py-2 text-sm font-medium transition-colors ${
                  mode === 'signup' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Sign up
              </button>
            </div>

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
            <div>
              <div className="flex items-center justify-between gap-2 mb-2">
                <label className="block text-sm font-medium text-gray-700">Password</label>
                {mode === 'signin' && (
                  <Link
                    href="/login/forgot-password"
                    className="text-sm font-medium text-gray-600 hover:text-gray-900"
                  >
                    Forgot password?
                  </Link>
                )}
              </div>
              <input
                type="password"
                autoComplete={mode === 'signup' ? 'new-password' : 'current-password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-gray-900"
              />
            </div>
            {mode === 'signup' && (
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
            )}

            <Button onClick={handleSupabaseAuth} disabled={loading} className="w-full py-3">
              {loading ? 'Please wait…' : mode === 'signin' ? 'Sign in' : 'Create account'}
            </Button>
          </>
        )}

        {info && <p className="text-sm text-gray-600">{info}</p>}
        {error && <p className="text-sm text-red-600">{error}</p>}

        <div className="border-t border-gray-100 pt-4">
          <button
            type="button"
            onClick={() => setShowDev((s) => !s)}
            className="text-xs font-medium text-gray-500 hover:text-gray-800"
          >
            {showDev ? 'Hide' : 'Developer'}: paste JWT instead
          </button>
          {showDev && (
            <div className="mt-3 space-y-3">
              <textarea
                value={devToken}
                onChange={(e) => setDevToken(e.target.value)}
                rows={4}
                className="w-full rounded-xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-gray-900"
                placeholder="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
              />
              <Button type="button" variant="outline" onClick={handleDevToken} disabled={loading} className="w-full">
                Save token & continue
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default function LoginPage() {
  return (
    <Layout>
      <Suspense
        fallback={
          <div className="max-w-md mx-auto px-4 py-16 text-center text-gray-500 text-sm">Loading…</div>
        }
      >
        <LoginForm />
      </Suspense>
    </Layout>
  )
}
