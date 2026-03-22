'use client'

import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { api } from '@/lib/api'
import { Layout } from '@/components/Layout'
import { Button } from '@/components/ui/button'
import Link from 'next/link'

type UserCollection = {
  id: number
  name: string
  description?: string | null
  created_at: string
}

export default function CollectionsPage() {
  const router = useRouter()
  const queryClient = useQueryClient()

  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [localError, setLocalError] = useState<string | null>(null)

  const collectionsQuery = useQuery({
    queryKey: ['profile-collections'],
    queryFn: async () => {
      const response = await api.get<UserCollection[]>('/profile/collections')
      return response.data
    },
    retry: false,
  })

  useEffect(() => {
    if (collectionsQuery.isError) {
      const anyErr: any = collectionsQuery.error
      const status = anyErr?.response?.status
      if (status === 401) router.push('/login?next=/collections')
    }
  }, [collectionsQuery.isError, router])

  const createCollection = useMutation({
    mutationFn: async (payload: { name: string; description?: string }) => {
      const response = await api.post('/profile/collections', payload)
      return response.data as UserCollection
    },
    onSuccess: () => {
      setName('')
      setDescription('')
      setLocalError(null)
      queryClient.invalidateQueries({ queryKey: ['profile-collections'] })
    },
    onError: (e: any) => setLocalError(e?.response?.data?.detail ?? e?.message ?? 'Failed to create'),
  })

  const collections = collectionsQuery.data ?? []

  return (
    <Layout>
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-10 md:py-14">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Your Watch Collections</h1>
        <p className="text-gray-500 mb-6">Create collections and add watch suggestions to them.</p>

        <div className="rounded-2xl border border-gray-200 bg-white shadow-sm p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Create new collection</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Name</label>
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full rounded-xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-gray-900"
                placeholder="e.g., My Casio collection"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Description (optional)</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={3}
                className="w-full rounded-xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-gray-900"
                placeholder="What do you collect?"
              />
            </div>
            {localError && <p className="text-sm text-red-600">{localError}</p>}
            <Button
              onClick={() => createCollection.mutate({ name, description: description || undefined })}
              disabled={!name.trim() || createCollection.isPending}
              className="w-full py-3"
            >
              {createCollection.isPending ? 'Creating…' : 'Create collection'}
            </Button>
          </div>
        </div>

        <div className="space-y-3">
          {collections.length === 0 ? (
            <p className="text-gray-600">No collections yet. Create one above.</p>
          ) : (
            collections.map((c) => (
              <Link
                key={c.id}
                href={`/collections/${c.id}`}
                className="block rounded-2xl border border-gray-200 bg-white shadow-sm p-4 hover:border-gray-300 hover:shadow-md transition-all"
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-sm font-medium text-gray-900">{c.name}</p>
                    {c.description && <p className="text-sm text-gray-500 mt-1">{c.description}</p>}
                  </div>
                  <p className="text-xs text-gray-400">{new Date(c.created_at).toLocaleDateString()}</p>
                </div>
              </Link>
            ))
          )}
        </div>
      </div>
    </Layout>
  )
}

