'use client'

import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { useParams, useRouter } from 'next/navigation'
import { Layout } from '@/components/Layout'
import { SpecBadge } from '@/components/SpecBadge'
import { Button } from '@/components/ui/button'
import { ContributionModal } from '@/components/ContributionModal'
import { VotingUI } from '@/components/VotingUI'
import { CommentsList } from '@/components/CommentsList'
import { useState } from 'react'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function WatchDetailPage() {
  const params = useParams()
  const router = useRouter()
  const watchId = parseInt(params.id as string)
  const [showContributionModal, setShowContributionModal] = useState(false)
  const [selectedSpecKey, setSelectedSpecKey] = useState<string | null>(null)

  const { data: watch, isLoading } = useQuery({
    queryKey: ['watch', watchId],
    queryFn: async () => {
      const response = await api.get(`/watches/${watchId}`)
      return response.data
    },
  })

  const { data: specsData } = useQuery({
    queryKey: ['watch-specs', watchId],
    queryFn: async () => {
      const response = await api.get(`/watches/${watchId}/specs`)
      return response.data
    },
  })

  const { data: contributions } = useQuery({
    queryKey: ['watch-contributions', watchId],
    queryFn: async () => {
      const response = await api.get(`/watches/${watchId}/contributions`)
      return response.data
    },
  })

  if (isLoading) {
    return (
      <Layout>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 md:py-10">
          <div className="animate-pulse space-y-6">
            <div className="h-8 w-32 bg-gray-200 rounded-2xl" />
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="aspect-square max-w-md bg-gray-200 rounded-2xl" />
              <div className="space-y-4">
                <div className="h-8 bg-gray-200 rounded-2xl w-3/4" />
                <div className="h-6 bg-gray-200 rounded-2xl w-1/2" />
                <div className="h-6 bg-gray-200 rounded-2xl w-1/3" />
              </div>
            </div>
          </div>
        </div>
      </Layout>
    )
  }

  if (!watch) {
    return (
      <Layout>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gray-100 text-gray-500 mb-4">
            <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Watch not found</h1>
          <Button type="button" variant="outline" onClick={() => router.push('/watches')}>
            ← Back to watches
          </Button>
        </div>
      </Layout>
    )
  }

  const imageUrl = watch.image_url?.split(' ')[0]
  const resolvedImageUrl =
    imageUrl && imageUrl.startsWith('/static/') ? `${API_BASE}${imageUrl}` : imageUrl

  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 md:py-10">
        <Button
          type="button"
          variant="ghost"
          onClick={() => router.back()}
          className="mb-6 -ml-1 rounded-2xl text-gray-500 hover:text-gray-900"
        >
          <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back
        </Button>

        {/* Watch Header */}
        <div className="rounded-2xl border border-gray-200 bg-white shadow-sm overflow-hidden mb-8">
        <div className={`grid gap-8 p-6 md:p-8 ${resolvedImageUrl ? 'grid-cols-1 lg:grid-cols-2' : ''}`}>
            {resolvedImageUrl && (
              <div className="aspect-square max-w-lg bg-gray-100 rounded-2xl overflow-hidden">
                <img
                  src={resolvedImageUrl}
                  alt={watch.product_name}
                  className="w-full h-full object-cover"
                />
              </div>
            )}
            <div className="flex flex-col justify-center">
              {watch.brand && (
                <p className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-2">
                  {watch.brand}
                </p>
              )}
              <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-3 tracking-tight">{watch.product_name}</h1>
              {watch.sku && (
                <p className="text-sm text-gray-500 mb-3">SKU: {watch.sku}</p>
              )}
              {watch.price_value != null && (
                <p className="text-2xl sm:text-3xl font-bold text-gray-900 mb-4">
                  {new Intl.NumberFormat('en-US', {
                    style: 'currency',
                    currency: watch.currency || 'USD',
                    minimumFractionDigits: 0,
                  }).format(watch.price_value)}
                </p>
              )}
              {watch.product_url && (
                <a
                  href={watch.product_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 text-gray-900 font-medium underline underline-offset-2 hover:no-underline rounded-2xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gray-900 focus-visible:ring-offset-2"
                >
                  View original product
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                </a>
              )}
            </div>
          </div>
        </div>

        {/* Specifications */}
        <div className="rounded-2xl border border-gray-200 bg-white shadow-sm p-6 md:p-8 mb-8">
          <h2 className="text-xl font-bold text-gray-900 mb-6">Specifications</h2>
          {specsData?.specs?.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {specsData.specs.map((spec: any) => (
                <div
                  key={spec.spec_key}
                  className="flex items-start justify-between p-4 border border-gray-200 rounded-2xl hover:border-gray-300 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                      <span className="font-semibold text-gray-900 capitalize">
                        {spec.spec_key.replace(/_/g, ' ')}
                      </span>
                      <SpecBadge sourceType={spec.source_type} />
                    </div>
                    <p className="text-gray-600">
                      {spec.spec_value || (
                        <span className="text-gray-400 italic">Unknown</span>
                      )}
                      {spec.unit && <span className="ml-1">{spec.unit}</span>}
                    </p>
                  </div>
                  {(!spec.spec_value || spec.source_type === 'unknown') && (
                    <Button
                      type="button"
                      size="sm"
                      className="ml-4 shrink-0 rounded-2xl"
                      onClick={() => {
                        setSelectedSpecKey(spec.spec_key)
                        setShowContributionModal(true)
                      }}
                    >
                      Contribute
                    </Button>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500">No specifications available yet.</p>
          )}
        </div>

        {/* Contributions */}
        {contributions && contributions.length > 0 && (
          <div className="rounded-2xl border border-gray-200 bg-white shadow-sm p-6 md:p-8 mb-8">
            <h2 className="text-xl font-bold text-gray-900 mb-6">Community Contributions</h2>
            <div className="space-y-4">
              {contributions.map((contrib: any) => (
                <div
                  key={contrib.id}
                  className="border border-gray-200 rounded-2xl p-5 hover:border-gray-300 hover:shadow-sm transition-all"
                >
                  <div className="flex items-start justify-between gap-4 mb-3">
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-gray-900 mb-1">
                        <span className="capitalize">{contrib.spec_key.replace(/_/g, ' ')}</span>:{' '}
                        {contrib.proposed_value}
                        {contrib.unit && <span className="text-gray-500 ml-1">{contrib.unit}</span>}
                      </p>
                      {contrib.note && (
                        <p className="text-sm text-gray-600 mt-2">{contrib.note}</p>
                      )}
                      {contrib.user && (
                        <p className="text-xs text-gray-400 mt-2">
                          by {contrib.user.display_name || contrib.user.username}
                        </p>
                      )}
                    </div>
                    <VotingUI contributionId={contrib.id} votes={contrib.votes} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Comments */}
        <div className="rounded-2xl border border-gray-200 bg-white shadow-sm p-6 md:p-8">
          <h2 className="text-xl font-bold text-gray-900 mb-6">Comments</h2>
          <CommentsList watchId={watchId} />
        </div>

        {showContributionModal && (
          <ContributionModal
            watchId={watchId}
            specKey={selectedSpecKey}
            onClose={() => {
              setShowContributionModal(false)
              setSelectedSpecKey(null)
            }}
          />
        )}
      </div>
    </Layout>
  )
}
