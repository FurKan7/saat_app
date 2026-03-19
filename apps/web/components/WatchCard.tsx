'use client'

import Link from 'next/link'
import { Watch } from 'lucide-react'

interface WatchCardProps {
  watch: {
    watch_id: number
    product_name: string
    brand?: string | null
    image_url?: string | null
    price_value?: number | null
    currency?: string | null
  }
}

export function WatchCard({ watch }: WatchCardProps) {
  const imageUrl = watch.image_url?.split(' ')[0] || null

  return (
    <Link
      href={`/watches/${watch.watch_id}`}
      className="group block rounded-2xl border border-gray-200 bg-white p-0 shadow-sm overflow-hidden hover:shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gray-900 focus-visible:ring-offset-2"
    >
      <div className="aspect-square bg-gray-100 overflow-hidden">
        {imageUrl ? (
          <img
            src={imageUrl}
            alt={watch.product_name}
            className="w-full h-full object-cover"
            loading="lazy"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-400">
            <Watch className="w-12 h-12" />
          </div>
        )}
      </div>
      <div className="p-4">
        {watch.brand && (
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
            {watch.brand}
          </p>
        )}
        <h3 className="font-semibold text-gray-900 mb-2 line-clamp-2 text-sm">
          {watch.product_name}
        </h3>
        {watch.price_value != null && (
          <p className="text-base font-semibold text-gray-900">
            {new Intl.NumberFormat('en-US', {
              style: 'currency',
              currency: watch.currency || 'USD',
              minimumFractionDigits: 0,
            }).format(watch.price_value)}
          </p>
        )}
      </div>
    </Link>
  )
}
