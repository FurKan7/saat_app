'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Layout } from '@/components/Layout'
import { Button } from '@/components/ui/button'
import { api, type ProfileMe } from '@/lib/api'
import { signOutClient } from '@/lib/auth-actions'
import { Camera, ChevronRight, FolderPlus, FolderOpen, LogOut, Shield, Sparkles } from 'lucide-react'

type UserCollection = {
  id: number
  name: string
  description?: string | null
  created_at: string
}

export default function DashboardPage() {
  const router = useRouter()
  const queryClient = useQueryClient()

  /** Avoid redirecting to /login before we have read localStorage (fixes false “logged out” flash). */
  const [hydrated, setHydrated] = useState(false)
  const [hasToken, setHasToken] = useState(false)

  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [formError, setFormError] = useState<string | null>(null)

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

  const collectionsQuery = useQuery({
    queryKey: ['profile-collections'],
    queryFn: async () => {
      const res = await api.get<UserCollection[]>('/profile/collections')
      return res.data
    },
    enabled: hydrated && hasToken && profileQuery.isSuccess,
    retry: false,
  })

  const createCollection = useMutation({
    mutationFn: async (payload: { name: string; description?: string }) => {
      const res = await api.post<UserCollection>('/profile/collections', payload)
      return res.data
    },
    onSuccess: () => {
      setName('')
      setDescription('')
      setFormError(null)
      queryClient.invalidateQueries({ queryKey: ['profile-collections'] })
    },
    onError: (e: any) => setFormError(e?.response?.data?.detail ?? e?.message ?? 'Failed to create'),
  })

  useEffect(() => {
    if (!hydrated) return
    if (!hasToken) router.replace('/login?next=/dashboard')
  }, [hydrated, hasToken, router])

  useEffect(() => {
    if (!profileQuery.isError) return
    const status = (profileQuery.error as any)?.response?.status
    if (status === 401) router.replace('/login?next=/dashboard')
  }, [profileQuery.isError, profileQuery.error, router])

  const handleSignOut = async () => {
    await signOutClient(queryClient)
    router.push('/')
  }

  if (!hydrated || (hasToken && profileQuery.isLoading)) {
    return (
      <Layout>
        <div className="min-h-[50vh] flex flex-col items-center justify-center px-4">
          <div className="w-10 h-10 rounded-full border-2 border-gray-200 border-t-gray-900 animate-spin mb-4" />
          <p className="text-sm text-gray-500">Loading your hub…</p>
        </div>
      </Layout>
    )
  }

  if (!hasToken) {
    return null
  }

  if (profileQuery.isError) {
    return (
      <Layout>
        <div className="max-w-md mx-auto px-4 py-20 text-center">
          <p className="text-sm text-red-600 mb-4">Could not load your profile.</p>
          <Button variant="outline" onClick={() => router.push('/login?next=/dashboard')}>
            Sign in again
          </Button>
        </div>
      </Layout>
    )
  }

  const profile = profileQuery.data!
  const collections = collectionsQuery.data ?? []
  const display = profile.display_name || profile.username || 'Watch lover'

  return (
    <Layout>
      {/* Distinct from login: full-width tinted band + structured hub (not a single auth card). */}
      <div className="bg-gradient-to-b from-slate-100/90 via-gray-50 to-gray-50 min-h-[calc(100vh-8rem)]">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-10 md:py-14">
          <header className="relative overflow-hidden rounded-3xl bg-gray-900 text-white px-6 py-8 sm:px-10 sm:py-10 mb-8 shadow-lg">
            <div className="absolute top-0 right-0 w-40 h-40 bg-white/5 rounded-full -translate-y-1/2 translate-x-1/2" />
            <div className="absolute bottom-0 left-0 w-32 h-32 bg-violet-500/20 rounded-full translate-y-1/2 -translate-x-1/2" />
            <div className="relative flex flex-col sm:flex-row sm:items-end sm:justify-between gap-6">
              <div>
                <p className="text-xs font-medium uppercase tracking-widest text-white/50 mb-2">Your hub</p>
                <h1 className="text-3xl sm:text-4xl font-bold tracking-tight">My watches</h1>
                <p className="text-white/75 mt-3 text-sm sm:text-base max-w-md leading-relaxed">
                  Welcome back, <span className="text-white font-medium">{display}</span>. Organize collections and
                  add pieces you own or want to identify.
                </p>
              </div>
              <button
                type="button"
                onClick={handleSignOut}
                className="shrink-0 inline-flex items-center justify-center gap-2 rounded-2xl bg-white/10 hover:bg-white/15 border border-white/10 px-4 py-2.5 text-sm font-medium text-white transition-colors"
              >
                <LogOut className="w-4 h-4" />
                Sign out
              </button>
            </div>
          </header>

          <div className="grid gap-4 sm:grid-cols-3 mb-8">
            <div className="rounded-2xl bg-white border border-gray-200/80 shadow-sm px-4 py-4 text-center sm:text-left">
              <p className="text-xs font-medium text-gray-400 uppercase tracking-wide">Collections</p>
              <p className="text-2xl font-semibold text-gray-900 mt-1">
                {collectionsQuery.isLoading ? '—' : collections.length}
              </p>
            </div>
            <div className="rounded-2xl bg-white border border-gray-200/80 shadow-sm px-4 py-4 text-center sm:text-left sm:col-span-2 flex items-center gap-3">
              <div className="hidden sm:flex w-10 h-10 rounded-xl bg-amber-100 text-amber-800 items-center justify-center shrink-0">
                <Sparkles className="w-5 h-5" />
              </div>
              <div className="text-left">
                <p className="text-xs font-medium text-gray-400 uppercase tracking-wide">Quick action</p>
                <Link
                  href="/upload"
                  className="text-sm font-semibold text-gray-900 hover:text-violet-700 inline-flex items-center gap-1 mt-0.5"
                >
                  Identify a watch from a photo
                  <ChevronRight className="w-4 h-4" />
                </Link>
              </div>
            </div>
          </div>

          <section className="mb-8">
            <div className="flex items-center gap-2 mb-4">
              <FolderPlus className="w-5 h-5 text-gray-700" />
              <h2 className="text-lg font-semibold text-gray-900">Create a collection</h2>
            </div>
            <div className="rounded-3xl bg-white border border-gray-200 shadow-sm p-6 sm:p-8">
              <p className="text-sm text-gray-500 mb-6">
                Group watches by theme, brand, or occasion. You can add items and photos inside each collection.
              </p>
              <div className="space-y-4 max-w-xl">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Collection name</label>
                  <input
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="w-full rounded-xl border border-gray-200 bg-gray-50/50 px-4 py-3 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-gray-900 focus:bg-white"
                    placeholder="e.g. Weekend rotation, GMT favorites"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Notes (optional)</label>
                  <textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    rows={2}
                    className="w-full rounded-xl border border-gray-200 bg-gray-50/50 px-4 py-3 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-gray-900 focus:bg-white resize-none"
                    placeholder="Anything you want to remember"
                  />
                </div>
                {formError && <p className="text-sm text-red-600">{formError}</p>}
                <Button
                  onClick={() => createCollection.mutate({ name, description: description || undefined })}
                  disabled={!name.trim() || createCollection.isPending}
                  className="rounded-xl px-6 py-3"
                >
                  {createCollection.isPending ? 'Creating…' : 'Create collection'}
                </Button>
              </div>
            </div>
          </section>

          <section>
            <div className="flex items-center justify-between gap-4 mb-4">
              <div className="flex items-center gap-2">
                <FolderOpen className="w-5 h-5 text-gray-700" />
                <h2 className="text-lg font-semibold text-gray-900">Your collections</h2>
              </div>
              {collections.length > 0 && (
                <Link href="/collections" className="text-sm font-medium text-violet-700 hover:underline">
                  Open full list
                </Link>
              )}
            </div>

            <div className="rounded-3xl bg-white border border-gray-200 shadow-sm overflow-hidden divide-y divide-gray-100">
              {collectionsQuery.isLoading ? (
                <p className="p-8 text-sm text-gray-500 text-center">Loading collections…</p>
              ) : collections.length === 0 ? (
                <div className="p-10 text-center">
                  <FolderOpen className="w-12 h-12 text-gray-200 mx-auto mb-3" />
                  <p className="text-sm text-gray-500">No collections yet. Create one above to get started.</p>
                </div>
              ) : (
                collections.map((c) => (
                  <Link
                    key={c.id}
                    href={`/collections/${c.id}`}
                    className="flex items-center gap-4 p-5 hover:bg-violet-50/40 transition-colors group"
                  >
                    <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-gray-100 to-gray-50 border border-gray-100 flex items-center justify-center text-gray-600 group-hover:border-violet-200 group-hover:text-violet-800">
                      <FolderOpen className="w-6 h-6" />
                    </div>
                    <div className="flex-1 min-w-0 text-left">
                      <p className="text-base font-medium text-gray-900 truncate">{c.name}</p>
                      {c.description ? (
                        <p className="text-sm text-gray-500 truncate mt-0.5">{c.description}</p>
                      ) : (
                        <p className="text-xs text-gray-400 mt-0.5">
                          Updated {new Date(c.created_at).toLocaleDateString()}
                        </p>
                      )}
                    </div>
                    <ChevronRight className="w-5 h-5 text-gray-300 group-hover:text-violet-500 shrink-0" />
                  </Link>
                ))
              )}
            </div>
          </section>

          <Link
            href="/upload"
            className="mt-8 flex items-center gap-4 rounded-3xl border-2 border-dashed border-gray-300 bg-white/60 hover:border-violet-300 hover:bg-violet-50/30 p-6 transition-colors"
          >
            <div className="w-12 h-12 rounded-2xl bg-gray-900 text-white flex items-center justify-center shrink-0">
              <Camera className="w-6 h-6" />
            </div>
            <div className="flex-1 text-left">
              <p className="font-semibold text-gray-900">Identify a watch</p>
              <p className="text-sm text-gray-500 mt-0.5">Upload a photo — AI helps match the catalog.</p>
            </div>
            <ChevronRight className="w-5 h-5 text-gray-400" />
          </Link>

          {profile.is_admin && (
            <div className="mt-8 rounded-3xl border border-violet-200 bg-violet-50/90 p-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div className="flex items-start gap-3">
                <Shield className="w-6 h-6 text-violet-700 shrink-0" />
                <div>
                  <p className="font-semibold text-violet-950">Administrator</p>
                  <p className="text-sm text-violet-900/80 mt-1">Review queue and catalog tools.</p>
                </div>
              </div>
              <Link
                href="/admin"
                className="inline-flex items-center justify-center rounded-xl bg-violet-700 text-white text-sm font-medium px-5 py-2.5 hover:bg-violet-800 shrink-0"
              >
                Admin dashboard
              </Link>
            </div>
          )}
        </div>
      </div>
    </Layout>
  )
}
