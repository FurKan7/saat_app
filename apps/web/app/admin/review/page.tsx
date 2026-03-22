'use client'

import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { api, type WatchSuggestion } from '@/lib/api'
import { Layout } from '@/components/Layout'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

function resolveImageUrl(url: string | null | undefined): string | null {
  if (!url) return null
  if (url.startsWith('/static/')) return `${API_BASE}${url}`
  return url
}

function FieldRow({ label, value }: { label: string; value: string | null | undefined }) {
  const v = value?.trim()
  return (
    <div className="min-w-0">
      <p className="text-[11px] font-medium text-gray-400 uppercase tracking-wide">{label}</p>
      <p className="text-sm text-gray-900 break-words">{v || '—'}</p>
    </div>
  )
}

function SuggestionRow({
  s,
  onDone,
}: {
  s: WatchSuggestion
  onDone: () => void
}) {
  const [notes, setNotes] = useState('')
  const [showRawAi, setShowRawAi] = useState(false)

  const approve = useMutation({
    mutationFn: async () => {
      await api.post(`/admin/watch-suggestions/${s.id}/approve`, {
        admin_notes: notes.trim() || null,
      })
    },
    onSuccess: onDone,
  })

  const reject = useMutation({
    mutationFn: async () => {
      await api.post(`/admin/watch-suggestions/${s.id}/reject`, {
        admin_notes: notes.trim() || null,
      })
    },
    onSuccess: onDone,
  })

  const busy = approve.isPending || reject.isPending
  const ai = (s.ai_output_json || {}) as Record<string, unknown>
  const detected = ai.detected_text
  const imgSrc = resolveImageUrl(s.image_url)

  return (
    <Card>
      <CardHeader className="pb-2 space-y-3">
        <div className="rounded-xl border border-amber-100 bg-amber-50/80 px-3 py-2 text-sm text-amber-950">
          <strong className="font-sans font-semibold">Human review</strong>
          <span className="text-amber-900/90">
            {' '}
            — No matching watch was found in the catalog. AI ran on the image; your approval
            creates the catalog entry and links the user’s collection item.
          </span>
        </div>

        <div className="flex flex-col sm:flex-row sm:items-start gap-4">
          <div className="shrink-0 w-full sm:w-36 aspect-square rounded-xl bg-gray-100 overflow-hidden border border-gray-100">
            {imgSrc ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={imgSrc} alt="" className="w-full h-full object-cover" />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-xs text-gray-400">No image</div>
            )}
          </div>
          <div className="flex-1 min-w-0">
            <CardTitle className="text-lg font-semibold text-gray-900">
              {s.product_name ?? 'Untitled'}
            </CardTitle>
            <p className="text-xs text-gray-400 mt-2">Suggestion #{s.id}</p>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        <div className="grid gap-6 md:grid-cols-2">
          <div className="space-y-3 rounded-xl border border-gray-100 bg-white p-4">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold uppercase tracking-wide text-gray-500">User submitted</span>
            </div>
            <div className="grid gap-3 gap-y-4">
              <FieldRow label="Brand" value={s.brand as string | undefined} />
              <FieldRow label="Product / model" value={s.product_name as string | undefined} />
              <FieldRow label="SKU" value={s.sku as string | undefined} />
              <FieldRow label="Source" value={s.source as string | undefined} />
              <FieldRow label="Product URL" value={s.product_url as string | undefined} />
            </div>
            {s.product_url && (
              <a
                href={s.product_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-blue-600 hover:underline break-all inline-block"
              >
                Open link
              </a>
            )}
          </div>

          <div className="space-y-3 rounded-xl border border-gray-100 bg-gray-50/80 p-4">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold uppercase tracking-wide text-gray-500">AI analysis</span>
            </div>
            <div className="grid gap-3 gap-y-4">
              <FieldRow label="Brand (guess)" value={ai.brand_guess != null ? String(ai.brand_guess) : undefined} />
              <FieldRow label="Dial color" value={ai.dial_color != null ? String(ai.dial_color) : undefined} />
              <FieldRow
                label="Bracelet material"
                value={ai.bracelet_material != null ? String(ai.bracelet_material) : undefined}
              />
              <FieldRow
                label="Confidence"
                value={ai.confidence != null ? String(ai.confidence) : undefined}
              />
              <FieldRow
                label="Notes"
                value={ai.short_explanation != null ? String(ai.short_explanation) : undefined}
              />
            </div>
            {Object.keys(ai).length === 0 && (
              <p className="text-sm text-gray-500">No AI output stored yet (processing may have failed).</p>
            )}
            <button
              type="button"
              onClick={() => setShowRawAi((o) => !o)}
              className="text-xs font-medium text-gray-600 hover:text-gray-900"
            >
              {showRawAi ? 'Hide' : 'Show'} raw AI JSON
            </button>
            {showRawAi && (
              <pre className="text-xs text-gray-700 whitespace-pre-wrap break-words bg-white rounded border border-gray-200 p-3 max-h-48 overflow-auto">
                {JSON.stringify(ai, null, 2)}
              </pre>
            )}
            {detected != null && typeof detected === 'object' && (
              <div>
                <p className="text-[11px] font-medium text-gray-400 uppercase tracking-wide mb-1">Detected text (OCR)</p>
                <pre className="text-xs text-gray-700 whitespace-pre-wrap break-words bg-white rounded border border-gray-200 p-3 max-h-32 overflow-auto">
                  {JSON.stringify(detected, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Admin notes (optional)</label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={2}
            disabled={busy}
            className="w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-gray-900"
            placeholder="Internal note for this decision…"
          />
        </div>
      </CardContent>
      <CardFooter className="flex flex-wrap gap-2 justify-end border-t border-gray-100 pt-4">
        <Button type="button" variant="outline" disabled={busy} onClick={() => reject.mutate()}>
          Reject
        </Button>
        <Button type="button" disabled={busy} onClick={() => approve.mutate()}>
          Approve & add to catalog
        </Button>
      </CardFooter>
      {(approve.isError || reject.isError) && (
        <p className="px-6 pb-4 text-sm text-red-600">
          {(approve.error as any)?.response?.data?.detail ??
            (reject.error as any)?.response?.data?.detail ??
            'Action failed'}
        </p>
      )}
    </Card>
  )
}

export default function AdminReviewPage() {
  const router = useRouter()
  const queryClient = useQueryClient()

  const listQuery = useQuery({
    queryKey: ['admin-watch-suggestions'],
    queryFn: async () => {
      const res = await api.get<WatchSuggestion[]>('/admin/watch-suggestions', {
        params: { status: 'pending_admin' },
      })
      return res.data
    },
    retry: false,
  })

  useEffect(() => {
    if (!listQuery.isError) return
    const status = (listQuery.error as any)?.response?.status
    if (status === 401) router.push('/login?next=/admin/review')
  }, [listQuery.isError, listQuery.error, router])

  const forbidden = listQuery.isError && (listQuery.error as any)?.response?.status === 403

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['admin-watch-suggestions'] })
  }

  return (
    <Layout>
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10 md:py-14">
        <div className="mb-8">
          <Link href="/admin" className="text-sm text-violet-700 hover:underline mb-2 inline-block">
            ← Admin home
          </Link>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Review queue</h1>
          <p className="text-gray-500">
            User-submitted watches that did not match the catalog. AI has filled the fields below; you decide whether
            to publish them.
          </p>
          <p className="text-sm text-gray-400 mt-3">
            Access: set <code className="text-gray-600 bg-gray-100 px-1 rounded">users.is_admin = true</code> for
            your account in the database, or set{' '}
            <code className="text-gray-600 bg-gray-100 px-1 rounded">ADMIN_SUPABASE_USER_ID</code> on the API. Then{' '}
            <Link href="/login" className="text-blue-600 hover:underline">
              log in
            </Link>
            .
          </p>
        </div>

        {listQuery.isLoading && <p className="text-gray-500 text-sm">Loading queue…</p>}

        {forbidden && (
          <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
            You are signed in, but this account is not an admin (403).
          </div>
        )}

        {listQuery.isError && !forbidden && (listQuery.error as any)?.response?.status !== 401 && (
          <p className="text-sm text-red-600">
            {(listQuery.error as any)?.response?.data?.detail ?? 'Failed to load suggestions'}
          </p>
        )}

        {!listQuery.isLoading && !listQuery.isError && (
          <>
            {listQuery.data?.length === 0 ? (
              <p className="text-gray-500 text-sm">No pending suggestions.</p>
            ) : (
              <ul className="space-y-8">
                {listQuery.data?.map((s) => (
                  <li key={s.id}>
                    <SuggestionRow s={s} onDone={invalidate} />
                  </li>
                ))}
              </ul>
            )}
          </>
        )}
      </div>
    </Layout>
  )
}
