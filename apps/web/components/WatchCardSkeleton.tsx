'use client'

import { Skeleton } from '@/components/ui/skeleton'

export function WatchCardSkeleton() {
  return (
    <div className="rounded-2xl border border-gray-200 bg-white overflow-hidden shadow-sm">
      <Skeleton className="aspect-square rounded-none bg-gray-100" />
      <div className="p-4 space-y-3">
        <Skeleton className="h-3 w-16 bg-gray-200 rounded" />
        <Skeleton className="h-4 w-full bg-gray-200 rounded" />
        <Skeleton className="h-4 w-3/4 bg-gray-200 rounded" />
        <Skeleton className="h-5 w-24 bg-gray-200 rounded" />
      </div>
    </div>
  )
}
