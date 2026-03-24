'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Watch, Menu, X, Camera, User } from 'lucide-react'
import { SearchBar } from '@/components/SearchBar'
import { api, type ProfileMe } from '@/lib/api'
import { signOutClient } from '@/lib/auth-actions'

interface LayoutProps {
  children: React.ReactNode
  searchValue?: string
  onSearchChange?: (value: string) => void
}

const adminNav = { href: '/admin', label: 'Admin' } as const

export function Layout({ children, searchValue = '', onSearchChange }: LayoutProps) {
  const pathname = usePathname()
  const router = useRouter()
  const queryClient = useQueryClient()
  const [mobileOpen, setMobileOpen] = useState(false)
  const [hasToken, setHasToken] = useState(false)

  useEffect(() => setMobileOpen(false), [pathname])
  useEffect(() => {
    document.body.style.overflow = mobileOpen ? 'hidden' : ''
    return () => {
      document.body.style.overflow = ''
    }
  }, [mobileOpen])

  useEffect(() => {
    setHasToken(typeof window !== 'undefined' && !!localStorage.getItem('supabase_token'))
  }, [pathname])

  const profileQuery = useQuery({
    queryKey: ['profile-me'],
    queryFn: async () => {
      const res = await api.get<ProfileMe>('/profile/me')
      return res.data
    },
    enabled: hasToken,
    retry: false,
  })

  const loggedIn = hasToken && profileQuery.isSuccess
  const showAdmin = profileQuery.data?.is_admin === true

  const navLinks = [
    { href: '/', label: 'Home' },
    { href: '/watches', label: 'Watches' },
    ...(loggedIn ? ([{ href: '/upload', label: 'Identify' }, { href: '/dashboard', label: 'Dashboard' }] as const) : []),
    { href: '/collections', label: 'Collections' },
    ...(showAdmin ? [adminNav] : []),
  ]

  const handleSignOut = async () => {
    setMobileOpen(false)
    await signOutClient(queryClient)
    setHasToken(false)
    router.push('/')
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="sticky top-0 z-40 border-b border-gray-200 bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-4 h-14 md:h-16">
            <Link href="/" className="flex items-center gap-2 shrink-0">
              <div className="w-9 h-9 rounded-2xl bg-gray-900 flex items-center justify-center text-white">
                <Watch className="w-5 h-5" />
              </div>
              <span className="text-lg font-semibold text-gray-900 hidden sm:inline">WatchHub</span>
            </Link>

            {onSearchChange && (
              <div className="hidden md:flex flex-1 max-w-xl mx-4">
                <SearchBar
                  value={searchValue}
                  onChange={onSearchChange}
                  placeholder="Search watches..."
                />
              </div>
            )}
            {!onSearchChange && <div className="hidden md:block flex-1" />}

            <div className="flex items-center gap-2 sm:gap-3 ml-auto">
              {loggedIn && (
                <Link href="/upload">
                  <span className="inline-flex items-center gap-2 rounded-2xl border border-gray-200 bg-white px-3 sm:px-4 py-2 text-sm font-medium text-gray-900 hover:bg-gray-50">
                    <Camera className="w-4 h-4" />
                    <span className="hidden sm:inline">Identify</span>
                  </span>
                </Link>
              )}

              {loggedIn ? (
                <>
                  <Link
                    href="/dashboard"
                    className="hidden md:inline text-sm font-medium text-gray-700 hover:text-gray-900"
                  >
                    Dashboard
                  </Link>
                  {showAdmin && (
                    <Link
                      href="/admin"
                      className="hidden md:inline text-sm font-medium text-violet-700 hover:text-violet-900"
                    >
                      Admin
                    </Link>
                  )}
                  <button
                    type="button"
                    onClick={handleSignOut}
                    className="hidden md:inline text-sm text-gray-500 hover:text-gray-900 px-1"
                  >
                    Sign out
                  </button>
                </>
              ) : (
                <Link
                  href="/login"
                  className="hidden md:inline text-sm font-medium text-gray-900 hover:text-gray-700 px-2"
                >
                  Log in
                </Link>
              )}

              <Link
                href={loggedIn ? '/dashboard' : '/login'}
                className="rounded-2xl border border-gray-200 bg-white p-2 text-gray-600 hover:bg-gray-50"
                aria-label={loggedIn ? 'Dashboard' : 'Log in'}
              >
                <User className="w-5 h-5" />
              </Link>

              <button
                type="button"
                aria-label="Menu"
                onClick={() => setMobileOpen((o) => !o)}
                className="md:hidden p-2 rounded-2xl text-gray-600 hover:bg-gray-100"
              >
                {mobileOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
              </button>
            </div>
          </div>
        </div>

        {mobileOpen && (
          <>
            <div className="fixed inset-0 z-40 bg-black/50 md:hidden" aria-hidden onClick={() => setMobileOpen(false)} />
            <div className="fixed top-14 left-0 right-0 z-50 border-b border-gray-200 bg-white p-4 md:hidden max-h-[calc(100vh-3.5rem)] overflow-y-auto">
              {onSearchChange && (
                <div className="mb-4">
                  <SearchBar value={searchValue} onChange={onSearchChange} placeholder="Search watches..." />
                </div>
              )}
              <nav className="flex flex-col gap-1">
                {navLinks.map((link) => {
                  const isActive =
                    pathname === link.href || (link.href !== '/' && pathname?.startsWith(link.href))
                  return (
                    <Link
                      key={link.href}
                      href={link.href}
                      onClick={() => setMobileOpen(false)}
                      className={`rounded-2xl px-4 py-3 text-sm font-medium ${isActive ? 'bg-gray-100 text-gray-900' : 'text-gray-600 hover:bg-gray-50'}`}
                    >
                      {link.label}
                    </Link>
                  )
                })}
                {loggedIn ? (
                  <button
                    type="button"
                    onClick={handleSignOut}
                    className="text-left rounded-2xl px-4 py-3 text-sm font-medium text-gray-500 hover:bg-gray-50"
                  >
                    Sign out
                  </button>
                ) : (
                  <Link
                    href="/login"
                    onClick={() => setMobileOpen(false)}
                    className="rounded-2xl px-4 py-3 text-sm font-medium text-gray-900 bg-gray-50"
                  >
                    Log in
                  </Link>
                )}
              </nav>
            </div>
          </>
        )}
      </header>

      <main className="flex-1">{children}</main>

      <footer className="border-t border-gray-200 bg-white py-6 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-gray-500">
          <span>Watch Community Platform</span>
          <div className="flex flex-wrap gap-x-6 gap-y-2 justify-center">
            <Link href="/" className="hover:text-gray-900">Home</Link>
            <Link href="/watches" className="hover:text-gray-900">Watches</Link>
            {loggedIn ? (
              <>
                <Link href="/upload" className="hover:text-gray-900">Identify</Link>
                <Link href="/dashboard" className="hover:text-gray-900">Dashboard</Link>
                <Link href="/collections" className="hover:text-gray-900">Collections</Link>
                {showAdmin && <Link href="/admin" className="hover:text-violet-700">Admin</Link>}
              </>
            ) : (
              <>
                <Link href="/login" className="hover:text-gray-900">Log in</Link>
                <Link href="/collections" className="hover:text-gray-900">Collections</Link>
              </>
            )}
          </div>
        </div>
      </footer>
    </div>
  )
}
