'use client'

import { useEffect, useRef, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Layout } from '@/components/Layout'
import { Button } from '@/components/ui/button'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type UserCollection = {
  id: number
  name: string
  description?: string | null
}

type CollectionItem = {
  id: number
  collection_id: number
  status: string
  sku?: string | null
  source?: string | null
  product_url?: string | null
  product_name?: string | null
  brand?: string | null
  image_url?: string | null
  watch_id?: number | null
  suggestion_id?: number | null
  created_at: string
}

function itemTitle(it: CollectionItem): string {
  const brand = it.brand?.trim()
  const model = it.product_name?.trim()
  if (brand && model) return `${brand} · ${model}`
  if (brand) return brand
  if (model) return model
  return 'Watch entry'
}

export default function CollectionDetailPage() {
  const params = useParams()
  const router = useRouter()
  const queryClient = useQueryClient()

  const collectionId = parseInt(params.id as string)

  const collectionQuery = useQuery({
    queryKey: ['profile-collection', collectionId],
    queryFn: async () => {
      const response = await api.get<UserCollection>(`/profile/collections/${collectionId}`)
      return response.data
    },
    retry: false,
  })

  useEffect(() => {
    if (collectionQuery.isError) {
      const anyErr: any = collectionQuery.error
      const status = anyErr?.response?.status
      if (status === 401) {
        router.push(`/login?next=${encodeURIComponent(`/collections/${collectionId}`)}`)
      }
    }
  }, [collectionQuery.isError, router, collectionId])

  const itemsQuery = useQuery({
    queryKey: ['collection-items', collectionId],
    queryFn: async () => {
      const response = await api.get<CollectionItem[]>(`/profile/collections/${collectionId}/items`)
      return response.data
    },
    refetchInterval: (query) => {
      const data = query.state.data as CollectionItem[] | undefined
      if (!data?.length) return false
      const hasInProgress = data.some((i) => ['processing_ai', 'pending_admin'].includes(i.status))
      return hasInProgress ? 2500 : false
    },
  })

  const [brand, setBrand] = useState('')
  const [model, setModel] = useState('')
  const [imageFile, setImageFile] = useState<File | null>(null)
  const imageInputRef = useRef<HTMLInputElement>(null)
  const [formError, setFormError] = useState<string | null>(null)

  const addItem = useMutation({
    mutationFn: async (formData: FormData) => {
      const response = await api.post(`/profile/collections/${collectionId}/items`, formData, {
        headers: { 'Content-Type': false } as any,
      })
      return response.data as CollectionItem
    },
    onSuccess: () => {
      setBrand('')
      setModel('')
      setImageFile(null)
      if (imageInputRef.current) imageInputRef.current.value = ''
      setFormError(null)
      queryClient.invalidateQueries({ queryKey: ['collection-items', collectionId] })
    },
    onError: (e: any) => {
      setFormError(e?.response?.data?.detail ?? e?.message ?? 'Failed to add watch')
    },
  })

  const items = itemsQuery.data ?? []
  const collection = collectionQuery.data

  const statusLabel = (s: string) => {
    switch (s) {
      case 'processing_ai':
        return 'Processing'
      case 'matched_existing':
        return 'Linked to catalog'
      case 'pending_admin':
        return 'Pending admin approval'
      case 'approved_linked':
        return 'Approved & linked'
      case 'rejected':
        return 'Rejected'
      default:
        return s
    }
  }

  const canSubmit = Boolean(brand.trim())

  const submit = () => {
    setFormError(null)
    if (!canSubmit) return
    const fd = new FormData()
    fd.append('brand', brand.trim())
    if (model.trim()) fd.append('product_name', model.trim())
    if (imageFile) fd.append('image_file', imageFile)
    addItem.mutate(fd)
  }

  return (
    <Layout>
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10 md:py-14">
        <Button type="button" variant="outline" onClick={() => router.push('/collections')} className="mb-4">
          ← Back
        </Button>

        <h1 className="text-3xl font-bold text-gray-900 mb-2">{collection?.name ?? 'Collection'}</h1>
        {collection?.description && <p className="text-gray-500 mb-6">{collection.description}</p>}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
          <div className="space-y-4">
            <div className="rounded-2xl border border-gray-200 bg-white shadow-sm p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-1">Add watch to this collection</h2>
              <p className="text-sm text-gray-500 mb-5">
                Brand is required. Model and a photo of your watch are optional; a photo helps review and cataloging.
              </p>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Brand (required)</label>
                  <input
                    value={brand}
                    onChange={(e) => setBrand(e.target.value)}
                    className="w-full rounded-xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-gray-900"
                    placeholder="e.g. Casio"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Model (optional)</label>
                  <input
                    value={model}
                    onChange={(e) => setModel(e.target.value)}
                    className="w-full rounded-xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-gray-900"
                    placeholder="e.g. G-Shock DW-5600"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Photo of your watch (optional)</label>
                  <input
                    ref={imageInputRef}
                    type="file"
                    accept="image/*"
                    onChange={(e) => setImageFile(e.target.files?.[0] ?? null)}
                    className="block w-full text-sm text-gray-600 file:mr-4 file:rounded-lg file:border-0 file:bg-gray-100 file:px-4 file:py-2 file:text-sm file:font-medium file:text-gray-900 hover:file:bg-gray-200"
                  />
                </div>

                {formError && <p className="text-sm text-red-600">{formError}</p>}

                <Button onClick={submit} disabled={!canSubmit || addItem.isPending} className="w-full py-3">
                  {addItem.isPending ? 'Adding…' : 'Add to collection'}
                </Button>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <div className="rounded-2xl border border-gray-200 bg-white shadow-sm p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Items & status</h2>

              {itemsQuery.isLoading ? (
                <p className="text-gray-500">Loading…</p>
              ) : items.length === 0 ? (
                <p className="text-gray-600">No items yet.</p>
              ) : (
                <div className="space-y-3">
                  {items.map((it) => (
                    <div key={it.id} className="border border-gray-200 rounded-2xl p-4 flex items-start gap-4">
                      <div className="w-20 h-20 rounded-xl bg-gray-100 overflow-hidden flex items-center justify-center text-gray-400 text-xs shrink-0">
                        {it.image_url ? (
                          <img
                            src={it.image_url.startsWith('/static/') ? `${API_BASE}${it.image_url}` : it.image_url}
                            alt=""
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <span>No image</span>
                        )}
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-semibold text-gray-900 truncate">{itemTitle(it)}</p>
                        <p className="text-xs text-gray-500 mt-1">{statusLabel(it.status)}</p>
                        {it.suggestion_id && (
                          <p className="text-xs text-gray-500 mt-1">Suggestion #{it.suggestion_id}</p>
                        )}
                        {it.watch_id && <p className="text-xs text-gray-500 mt-1">Watch linked: #{it.watch_id}</p>}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </Layout>
  )
}
