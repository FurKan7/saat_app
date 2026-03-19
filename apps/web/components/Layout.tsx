'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Watch, Menu, X, Camera, User } from 'lucide-react'
import { SearchBar } from '@/components/SearchBar'

interface LayoutProps {
  children: React.ReactNode
  /** Optional: show large search in nav (e.g. on home). When set, nav search is used for query. */
  searchValue?: string
  onSearchChange?: (value: string) => void
}

export function Layout({ children, searchValue = '', onSearchChange }: LayoutProps) {
  const pathname = usePathname()
  const [mobileOpen, setMobileOpen] = useState(false)

  useEffect(() => setMobileOpen(false), [pathname])
  useEffect(() => {
    document.body.style.overflow = mobileOpen ? 'hidden' : ''
    return () => { document.body.style.overflow = '' }
  }, [mobileOpen])

  const navLinks = [
    { href: '/', label: 'Home' },
    { href: '/watches', label: 'Watches' },
    { href: '/upload', label: 'Identify' },
  ]

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="sticky top-0 z-40 border-b border-gray-200 bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-4 h-14 md:h-16">
            {/* Logo */}
            <Link href="/" className="flex items-center gap-2 shrink-0">
              <div className="w-9 h-9 rounded-2xl bg-gray-900 flex items-center justify-center text-white">
                <Watch className="w-5 h-5" />
              </div>
              <span className="text-lg font-semibold text-gray-900 hidden sm:inline">WatchHub</span>
            </Link>

            {/* Center search (desktop) */}
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

            {/* Right: Upload + Auth */}
            <div className="flex items-center gap-2 ml-auto">
              <Link href="/upload">
                <span className="inline-flex items-center gap-2 rounded-2xl border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-900 hover:bg-gray-50">
                  <Camera className="w-4 h-4" />
                  <span className="hidden sm:inline">Identify</span>
                </span>
              </Link>
              <button
                type="button"
                className="rounded-2xl border border-gray-200 bg-white p-2 text-gray-600 hover:bg-gray-50"
                aria-label="Account"
              >
                <User className="w-5 h-5" />
              </button>
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

        {/* Mobile menu */}
        {mobileOpen && (
          <>
            <div className="fixed inset-0 z-40 bg-black/50 md:hidden" aria-hidden onClick={() => setMobileOpen(false)} />
            <div className="fixed top-14 left-0 right-0 z-50 border-b border-gray-200 bg-white p-4 md:hidden">
              {onSearchChange && (
                <div className="mb-4">
                  <SearchBar value={searchValue} onChange={onSearchChange} placeholder="Search watches..." />
                </div>
              )}
              <nav className="flex flex-col gap-1">
                {navLinks.map((link) => {
                  const isActive = pathname === link.href || (link.href !== '/' && pathname?.startsWith(link.href))
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
              </nav>
            </div>
          </>
        )}
      </header>

      <main className="flex-1">{children}</main>

      <footer className="border-t border-gray-200 bg-white py-6 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-gray-500">
          <span>Watch Community Platform</span>
          <div className="flex gap-6">
            <Link href="/" className="hover:text-gray-900">Home</Link>
            <Link href="/watches" className="hover:text-gray-900">Watches</Link>
            <Link href="/upload" className="hover:text-gray-900">Identify</Link>
          </div>
        </div>
      </footer>
    </div>
  )
}
