'use client'

import { useState, useRef, useEffect } from 'react'
import { useInfiniteQuery, useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Layout } from '@/components/Layout'
import { WatchCard } from '@/components/WatchCard'
import { WatchCardSkeleton } from '@/components/WatchCardSkeleton'
import { SearchBar } from '@/components/SearchBar'
import { EmptyState } from '@/components/EmptyState'
import { Button } from '@/components/ui/button'

const PAGE_SIZE = 20

type WatchPage = { watches: { watch_id: number }[]; total: number; page: number; total_pages: number }

export default function Home() {
  const [searchQuery, setSearchQuery] = useState('')
  const [brandFilter, setBrandFilter] = useState('')
  const loadMoreRef = useRef<HTMLDivElement>(null)

  const apiBase = typeof window !== 'undefined' ? (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000') : 'http://localhost:8000'
  const {
    data,
    isLoading,
    isError,
    refetch,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteQuery({
    queryKey: ['watches', searchQuery, brandFilter],
    initialPageParam: 1,
    queryFn: async ({ pageParam }) => {
      const params = new URLSearchParams()
      if (searchQuery) params.append('query', searchQuery)
      if (brandFilter) params.append('brand', brandFilter)
      params.append('page', String(pageParam))
      params.append('limit', String(PAGE_SIZE))
      const response = await api.get(`/watches?${params.toString()}`)
      return response.data as WatchPage
    },
    getNextPageParam: (lastPage) =>
      lastPage.page < lastPage.total_pages ? lastPage.page + 1 : undefined,
    retry: 1,
  })

  useEffect(() => {
    if (!hasNextPage || isFetchingNextPage) return
    const el = loadMoreRef.current
    if (!el) return
    const obs = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting) fetchNextPage()
      },
      { rootMargin: '200px' }
    )
    obs.observe(el)
    return () => obs.disconnect()
  }, [hasNextPage, isFetchingNextPage, fetchNextPage])

  const watches = data?.pages.flatMap((p) => p.watches) ?? []
  const total = data?.pages[0]?.total ?? 0

  // Get unique brands for filter
  const { data: brandsData } = useQuery({
    queryKey: ['brands'],
    queryFn: async (): Promise<string[]> => {
      const response = await api.get('/watches?limit=1000')
      const brands = new Set(
        response.data.watches
          .map((w: { brand?: string | null }) => w.brand)
          .filter((b: string | null | undefined): b is string => Boolean(b))
      )
      return Array.from(brands).sort() as string[]
    },
  })

  return (
    <Layout searchValue={searchQuery} onSearchChange={setSearchQuery}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 md:py-12">
        {/* Hero */}
        <div className="text-center mb-8 md:mb-10">
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-2">
            Discover Watches
          </h1>
          <p className="text-base text-gray-500 max-w-xl mx-auto">
            Search the community database. Log in to identify a watch from a photo.
          </p>
        </div>

        {/* Large search (mobile) / filter row when nav has search */}
        <div className="mb-8 space-y-4">
          <div className="md:hidden max-w-2xl mx-auto">
            <SearchBar
              value={searchQuery}
              onChange={setSearchQuery}
              placeholder="Search by name, brand..."
            />
          </div>
          <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
            <select
              value={brandFilter}
              onChange={(e) => setBrandFilter(e.target.value)}
              className="rounded-2xl border border-gray-200 bg-white px-4 py-2.5 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-gray-900 focus:ring-offset-0"
              aria-label="Filter by brand"
            >
              <option value="">All brands</option>
              {brandsData?.map((brand) => (
                <option key={brand} value={brand}>{brand}</option>
              ))}
            </select>
            {data != null && (
              <p className="text-xs text-gray-500">
                {total} {total === 1 ? 'watch' : 'watches'}
                {watches.length < total && ` · showing ${watches.length}`}
              </p>
            )}
          </div>
        </div>

        {/* Grid */}
        {isLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 md:gap-6">
            {[...Array(8)].map((_, i) => (
              <WatchCardSkeleton key={i} />
            ))}
          </div>
        ) : isError ? (
          <div className="max-w-md mx-auto rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
            <p className="font-medium text-gray-900 mb-2">Could not load watches</p>
            <p className="text-sm text-gray-500 mb-4">
              Start the API in a second terminal: <code className="bg-gray-100 px-1 rounded">npm run dev:api</code>
            </p>
            <Button onClick={() => refetch()}>Retry</Button>
          </div>
        ) : watches.length > 0 ? (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 md:gap-6">
              {watches.map((watch: any) => (
                <WatchCard key={watch.watch_id} watch={watch} />
              ))}
            </div>
            <div ref={loadMoreRef} className="min-h-[100px] py-6">
              {isFetchingNextPage && (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 md:gap-6">
                  {[...Array(4)].map((_, i) => (
                    <WatchCardSkeleton key={`next-${i}`} />
                  ))}
                </div>
              )}
            </div>
          </>
        ) : (
          <EmptyState
            title="No watches found"
            description="Try different search or filter criteria."
            action={(searchQuery || brandFilter) && (
              <Button variant="outline" onClick={() => { setSearchQuery(''); setBrandFilter('') }}>
                Clear filters
              </Button>
            )}
          />
        )}
      </div>
    </Layout>
  )
}
