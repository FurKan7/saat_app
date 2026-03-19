'use client'

import { Filter } from 'lucide-react'

interface FiltersPanelProps {
  brandFilter: string
  onBrandChange: (value: string) => void
  brands: string[]
  sortValue: string
  onSortChange: (value: string) => void
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function FiltersPanel({
  brandFilter,
  onBrandChange,
  brands,
  sortValue,
  onSortChange,
  open,
  onOpenChange,
}: FiltersPanelProps) {
  return (
    <>
      <button
        type="button"
        onClick={() => onOpenChange(!open)}
        className="lg:hidden inline-flex items-center gap-2 rounded-2xl border border-gray-200 bg-white px-4 py-2.5 text-sm font-medium text-gray-900"
      >
        <Filter className="w-4 h-4" />
        Filters
      </button>

      {/* Mobile overlay */}
      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          aria-hidden
          onClick={() => onOpenChange(false)}
        />
      )}

      {/* Sidebar: always visible on lg, drawer on mobile */}
      <aside
        className={`
          w-full lg:w-56 shrink-0
          lg:block
          fixed lg:static top-0 left-0 z-50 h-full lg:h-auto
          bg-white lg:bg-transparent border-r lg:border-r-0 border-gray-200
          transition-transform duration-200 ease-out
          ${open ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}
      >
        <div className="p-4 lg:p-0 lg:pr-6 space-y-6">
          <div>
            <label className="text-xs font-medium text-gray-500 uppercase tracking-wide block mb-2">
              Brand
            </label>
            <select
              value={brandFilter}
              onChange={(e) => onBrandChange(e.target.value)}
              className="w-full rounded-2xl border border-gray-200 bg-white px-4 py-2.5 text-sm text-gray-900"
              aria-label="Filter by brand"
            >
              <option value="">All brands</option>
              {brands.map((b) => (
                <option key={b} value={b}>{b}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs font-medium text-gray-500 uppercase tracking-wide block mb-2">
              Sort
            </label>
            <select
              value={sortValue}
              onChange={(e) => onSortChange(e.target.value)}
              className="w-full rounded-2xl border border-gray-200 bg-white px-4 py-2.5 text-sm text-gray-900"
              aria-label="Sort by"
            >
              <option value="newest">Newest</option>
              <option value="oldest">Oldest</option>
            </select>
          </div>
        </div>
      </aside>
    </>
  )
}
