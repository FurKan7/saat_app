'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { Layout } from '@/components/Layout'
import { api, type ProfileMe } from '@/lib/api'
import {
  ClipboardList,
  ExternalLink,
  Home,
  LayoutDashboard,
  Search,
  Shield,
  Upload,
} from 'lucide-react'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const cardClass =
  'flex items-start gap-4 rounded-2xl border border-gray-200 bg-white p-5 shadow-sm hover:border-violet-200 hover:shadow-md transition-all text-left w-full'

export default function AdminDashboardPage() {
  const router = useRouter()
  const [hydrated, setHydrated] = useState(false)
  const [hasToken, setHasToken] = useState(false)
  const [showSql, setShowSql] = useState(false)

  useEffect(() => {
    setHasToken(!!localStorage.getItem('supabase_token'))
    setHydrated(true)
  }, [])

  const profileQuery = useQuery({
    queryKey: ['profile-me'],
    queryFn: async () => {
      const res = await api.get<ProfileMe>('/profile/me')
      return res.data
    },
    enabled: hydrated && hasToken,
    retry: false,
  })

  useEffect(() => {
    if (!hydrated) return
    if (!hasToken) router.replace('/login?next=/admin')
  }, [hydrated, hasToken, router])

  useEffect(() => {
    if (!profileQuery.isError) return
    const status = (profileQuery.error as any)?.response?.status
    if (status === 401) router.push('/login?next=/admin')
  }, [profileQuery.isError, profileQuery.error, router])

  if (!hydrated || !hasToken || profileQuery.isLoading) {
    return (
      <Layout>
        <div className="max-w-4xl mx-auto px-4 py-16 text-center text-gray-500 text-sm">Loading…</div>
      </Layout>
    )
  }

  if (profileQuery.isError && (profileQuery.error as any)?.response?.status !== 401) {
    return (
      <Layout>
        <div className="max-w-4xl mx-auto px-4 py-16 text-center text-sm text-red-600">Could not load profile.</div>
      </Layout>
    )
  }

  const profile = profileQuery.data
  if (!profile?.is_admin) {
    return (
      <Layout>
        <div className="max-w-lg mx-auto px-4 sm:px-6 lg:px-8 py-14">
          <div className="rounded-2xl border border-amber-200 bg-amber-50 px-5 py-4 text-sm text-amber-950">
            <div className="flex gap-3">
              <Shield className="w-5 h-5 shrink-0 text-amber-800" />
              <div>
                <p className="font-semibold">Admin access required</p>
                <p className="text-amber-900/90 mt-1 leading-relaxed">
                  Grant access in Supabase (see below on this page once you are an admin) or set{' '}
                  <code className="text-xs bg-white/80 px-1 rounded">ADMIN_SUPABASE_USER_ID</code> on the API.
                </p>
                <button
                  type="button"
                  onClick={() => setShowSql((s) => !s)}
                  className="mt-3 text-sm font-medium text-amber-900 underline"
                >
                  {showSql ? 'Hide' : 'Show'} how to promote an admin in Supabase
                </button>
                {showSql && (
                  <div className="mt-3 rounded-xl bg-white/90 border border-amber-100 p-3 text-xs text-amber-950 space-y-2">
                    <p>
                      In <strong>Supabase → SQL Editor</strong>, run (use the user&apos;s login email):
                    </p>
                    <pre className="bg-gray-900 text-gray-100 p-3 rounded-lg overflow-x-auto text-[11px] leading-relaxed">
{`UPDATE users
SET is_admin = true
WHERE username = 'their-email@example.com';`}
                    </pre>
                    <p>
                      Or <strong>Table Editor → users</strong>: set <code className="bg-amber-100 px-1">is_admin</code>{' '}
                      to <code className="bg-amber-100 px-1">true</code> for that row. Users appear after they sign in
                      to the app once.
                    </p>
                  </div>
                )}
                <Link href="/dashboard" className="inline-block mt-4 text-sm font-medium text-amber-900 underline">
                  Back to your dashboard
                </Link>
              </div>
            </div>
          </div>
        </div>
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-10">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-violet-600 text-white flex items-center justify-center shadow-sm">
              <Shield className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Admin</h1>
              <p className="text-gray-500 text-sm mt-0.5">Everything you need in one place.</p>
            </div>
          </div>
          <Link
            href="/dashboard"
            className="inline-flex items-center justify-center rounded-xl border border-gray-200 bg-white px-4 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            <LayoutDashboard className="w-4 h-4 mr-2" />
            User dashboard
          </Link>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <Link href="/admin/review" className={cardClass}>
            <div className="w-10 h-10 rounded-xl bg-violet-50 text-violet-700 flex items-center justify-center shrink-0">
              <ClipboardList className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-gray-900">Review queue</h2>
              <p className="text-sm text-gray-500 mt-1">Pending AI suggestions — approve or reject for the catalog.</p>
              <span className="inline-block mt-2 text-sm font-medium text-violet-700">Open →</span>
            </div>
          </Link>

          <Link href="/watches" className={cardClass}>
            <div className="w-10 h-10 rounded-xl bg-gray-100 text-gray-800 flex items-center justify-center shrink-0">
              <Search className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-gray-900">Watches catalog</h2>
              <p className="text-sm text-gray-500 mt-1">Browse and search public watch entries.</p>
              <span className="inline-block mt-2 text-sm font-medium text-gray-700">Open →</span>
            </div>
          </Link>

          <Link href="/upload" className={cardClass}>
            <div className="w-10 h-10 rounded-xl bg-gray-100 text-gray-800 flex items-center justify-center shrink-0">
              <Upload className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-gray-900">Identify</h2>
              <p className="text-sm text-gray-500 mt-1">Test uploads and AI identification flow.</p>
              <span className="inline-block mt-2 text-sm font-medium text-gray-700">Open →</span>
            </div>
          </Link>

          <Link href="/" className={cardClass}>
            <div className="w-10 h-10 rounded-xl bg-gray-100 text-gray-800 flex items-center justify-center shrink-0">
              <Home className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-gray-900">Home</h2>
              <p className="text-sm text-gray-500 mt-1">Public landing and search.</p>
              <span className="inline-block mt-2 text-sm font-medium text-gray-700">Open →</span>
            </div>
          </Link>

          <a
            href={`${API_BASE}/docs`}
            target="_blank"
            rel="noopener noreferrer"
            className={cardClass}
          >
            <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-800 flex items-center justify-center shrink-0">
              <ExternalLink className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-gray-900">API docs (Swagger)</h2>
              <p className="text-sm text-gray-500 mt-1">Interactive backend reference — new tab.</p>
              <span className="inline-block mt-2 text-sm font-medium text-emerald-800">Open ↗</span>
            </div>
          </a>

          <a
            href="https://supabase.com/dashboard"
            target="_blank"
            rel="noopener noreferrer"
            className={cardClass}
          >
            <div className="w-10 h-10 rounded-xl bg-sky-50 text-sky-800 flex items-center justify-center shrink-0">
              <ExternalLink className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-gray-900">Supabase dashboard</h2>
              <p className="text-sm text-gray-500 mt-1">Auth users, SQL, Table Editor — promote admins here.</p>
              <span className="inline-block mt-2 text-sm font-medium text-sky-800">Open ↗</span>
            </div>
          </a>
        </div>

        <div className="mt-10 rounded-2xl border border-gray-200 bg-gray-50/80 p-6">
          <h3 className="text-sm font-semibold text-gray-900 mb-2">Promote or revoke admins</h3>
          <p className="text-sm text-gray-600 leading-relaxed mb-3">
            Admins are stored on <code className="text-xs bg-white border border-gray-200 px-1 rounded">public.users</code>
            , not in Supabase Auth alone. After a user has signed in at least once, set{' '}
            <code className="text-xs bg-white border px-1 rounded">is_admin</code> in the Table Editor or run:
          </p>
          <pre className="bg-gray-900 text-gray-100 p-4 rounded-xl text-xs overflow-x-auto leading-relaxed">
{`UPDATE users SET is_admin = true
WHERE username = 'admin@example.com';

UPDATE users SET is_admin = false
WHERE username = 'former@example.com';`}
          </pre>
        </div>
      </div>
    </Layout>
  )
}
