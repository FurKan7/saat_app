'use client'

import { useState, useRef, DragEvent } from 'react'
import { useMutation } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { useRouter } from 'next/navigation'
import { toast } from 'sonner'
import { Layout } from '@/components/Layout'
import { SimilarityBar } from '@/components/SimilarityBar'
import { Button } from '@/components/ui/button'

type DetectionCrop = {
  label: string
  image_url: string
  box: number[]
  score: number
}

type DebugInfo = {
  request_id: string
  annotated_image_url?: string
  debug_json_url?: string
  detector_used: boolean
  models: Record<string, string>
  timing: Record<string, number | null>
}

type IdentifyResponse = {
  candidates?: Array<{ watch_id: number; product_name?: string; brand?: string; image_url?: string; similarity_score?: number }>
  is_unknown?: boolean
  vlm_attributes?: {
    brand_guess?: string
    dial_color?: string
    bracelet_material?: string
    confidence?: number
    short_explanation?: string
  }
  retrieval_time_ms?: number
  vlm_time_ms?: number
  detection_crops?: DetectionCrop[]
  detected_text?: Record<string, string>
  debug_info?: DebugInfo
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function UploadPage() {
  const [imageUrl, setImageUrl] = useState('')
  const [imageFile, setImageFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [showDebug, setShowDebug] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const router = useRouter()
  const resultsRef = useRef<HTMLDivElement>(null)

  const identifyMutation = useMutation({
    mutationFn: async (formData: FormData) => {
      const response = await api.post<IdentifyResponse>('/ai/identify', formData, {
        headers: { 'Content-Type': false } as unknown as Record<string, string>,
      })
      return response.data
    },
    onSuccess: (data: IdentifyResponse) => {
      if (data.is_unknown) toast.info('No close match found.')
      else if (data.candidates?.length) toast.success('Identification complete.')
      resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    },
    onError: (err: { response?: { data?: { detail?: string } }; message?: string }) => {
      const msg = err.response?.data?.detail ?? err.message ?? 'Request failed'
      toast.error(typeof msg === 'string' ? msg : 'Identification failed')
    },
  })

  const handleFileChange = (file: File) => {
    setImageFile(file)
    setImageUrl('')
    const reader = new FileReader()
    reader.onloadend = () => setPreview(reader.result as string)
    reader.readAsDataURL(file)
  }

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) handleFileChange(file)
  }

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => { e.preventDefault(); setIsDragging(true) }
  const handleDragLeave = () => setIsDragging(false)
  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault(); setIsDragging(false)
    const file = e.dataTransfer.files[0]
    if (file?.type.startsWith('image/')) handleFileChange(file)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!imageFile && !imageUrl) return
    const formData = new FormData()
    if (imageFile) formData.append('image_file', imageFile)
    else if (imageUrl) formData.append('image_url', imageUrl)
    formData.append('top_k', '5')
    formData.append('use_vlm', 'true')
    identifyMutation.mutate(formData)
  }

  const data = identifyMutation.data

  return (
    <Layout>
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 md:py-10">
        <div className="text-center mb-8 md:mb-10">
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-2">Identify Watch</h1>
          <p className="text-base text-gray-500">Upload a photo and get AI-suggested matches from the database.</p>
        </div>

        {/* Upload form */}
        <div className="rounded-2xl border border-gray-200 bg-white shadow-sm p-6 md:p-8 mb-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div
              role="button" tabIndex={0}
              onDragOver={handleDragOver} onDragLeave={handleDragLeave} onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); fileInputRef.current?.click() } }}
              className={`border-2 border-dashed rounded-2xl p-10 md:p-12 text-center cursor-pointer transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gray-900 focus-visible:ring-offset-2 ${isDragging ? 'border-gray-900 bg-gray-50' : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'}`}
            >
              <input ref={fileInputRef} type="file" accept="image/*" onChange={handleFileInputChange} className="hidden" />
              <div className="space-y-4">
                <div className="mx-auto w-14 h-14 bg-gray-100 rounded-2xl flex items-center justify-center text-gray-600">
                  <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                </div>
                <div>
                  <p className="text-base font-semibold text-gray-900">{isDragging ? 'Drop your image here' : 'Drag & drop an image here'}</p>
                  <p className="text-sm text-gray-500 mt-1">or click to browse</p>
                </div>
                <p className="text-xs text-gray-400">JPG, PNG, WEBP (max 10MB)</p>
              </div>
            </div>

            <div className="text-center text-gray-500 font-medium text-sm">or</div>

            <div>
              <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Image URL</label>
              <input
                type="url" value={imageUrl}
                onChange={(e) => { setImageUrl(e.target.value); setImageFile(null); setPreview(e.target.value) }}
                placeholder="https://example.com/watch.jpg"
                className="w-full rounded-2xl border border-gray-200 bg-white px-4 py-2.5 text-sm text-gray-900"
              />
            </div>

            {preview && (
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Preview</p>
                <div className="rounded-2xl overflow-hidden border border-gray-200 bg-gray-50">
                  <img src={preview} alt="Preview" className="w-full h-auto max-h-96 object-contain" />
                </div>
              </div>
            )}

            <Button type="submit" disabled={identifyMutation.isPending || (!imageFile && !imageUrl)} className="w-full py-4 text-base rounded-2xl">
              {identifyMutation.isPending ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Identifying…
                </span>
              ) : 'Identify Watch'}
            </Button>
          </form>
        </div>

        {/* Results */}
        {identifyMutation.isSuccess && data && (
          <div ref={resultsRef} className="space-y-6 animate-fade-in">

            {/* Detection crops — always shown */}
            {data.detection_crops && data.detection_crops.length > 0 && (
              <div className="rounded-2xl border border-gray-200 bg-white shadow-sm p-6">
                <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">Detected regions</h3>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
                  {data.detection_crops.map((crop, i) => (
                    <div key={i} className="rounded-xl border border-gray-100 overflow-hidden bg-gray-50">
                      <img src={`${API_BASE}${crop.image_url}`} alt={crop.label} className="w-full h-32 object-contain bg-white" />
                      <div className="px-3 py-2">
                        <p className="text-xs font-medium text-gray-900 truncate">{crop.label}</p>
                        <p className="text-xs text-gray-500">{(crop.score * 100).toFixed(0)}% confidence</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Annotated image + VLM attributes — always shown */}
            <div className="rounded-2xl border border-gray-200 bg-white shadow-sm overflow-hidden">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-0">
                <div className="p-4 md:p-6 bg-gray-50 flex items-center justify-center min-h-[200px]">
                  {data.debug_info?.annotated_image_url ? (
                    <img src={`${API_BASE}${data.debug_info.annotated_image_url}`} alt="Annotated" className="max-h-80 w-auto object-contain rounded-2xl" />
                  ) : preview ? (
                    <img src={preview} alt="Uploaded" className="max-h-80 w-auto object-contain rounded-2xl" />
                  ) : (
                    <span className="text-sm text-gray-400">No preview</span>
                  )}
                </div>
                <div className="p-4 md:p-6 flex flex-col justify-center">
                  <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Detected by AI</h3>

                  {data.detected_text && Object.keys(data.detected_text).length > 0 && (
                    <div className="mb-4 p-3 bg-blue-50 rounded-xl">
                      <p className="text-xs font-medium text-blue-700 uppercase tracking-wide mb-1">Text found on watch</p>
                      {Object.entries(data.detected_text).map(([key, val]) => (
                        <p key={key} className="text-sm font-semibold text-blue-900">{val}</p>
                      ))}
                    </div>
                  )}

                  {data.vlm_attributes ? (
                    <dl className="space-y-3">
                      {data.vlm_attributes.brand_guess && data.vlm_attributes.brand_guess !== 'null' && (
                        <div>
                          <dt className="text-xs font-medium text-gray-500 uppercase tracking-wide">Brand</dt>
                          <dd className="font-semibold text-gray-900 mt-0.5">{data.vlm_attributes.brand_guess}</dd>
                        </div>
                      )}
                      {data.vlm_attributes.dial_color && data.vlm_attributes.dial_color !== 'null' && (
                        <div>
                          <dt className="text-xs font-medium text-gray-500 uppercase tracking-wide">Dial color</dt>
                          <dd className="font-semibold text-gray-900 mt-0.5">{data.vlm_attributes.dial_color}</dd>
                        </div>
                      )}
                      {data.vlm_attributes.bracelet_material && data.vlm_attributes.bracelet_material !== 'null' && (
                        <div>
                          <dt className="text-xs font-medium text-gray-500 uppercase tracking-wide">Bracelet</dt>
                          <dd className="font-semibold text-gray-900 mt-0.5">{data.vlm_attributes.bracelet_material}</dd>
                        </div>
                      )}
                      <div>
                        <dt className="text-xs font-medium text-gray-500 uppercase tracking-wide">Confidence</dt>
                        <dd className="font-semibold text-gray-900 mt-0.5">{((data.vlm_attributes.confidence ?? 0) * 100).toFixed(0)}%</dd>
                      </div>
                      {data.vlm_attributes.short_explanation && (
                        <div className="pt-2 border-t border-gray-100">
                          <dt className="text-xs font-medium text-gray-500 uppercase tracking-wide">Note</dt>
                          <dd className="text-sm text-gray-600 mt-0.5">{data.vlm_attributes.short_explanation}</dd>
                        </div>
                      )}
                    </dl>
                  ) : (
                    <p className="text-sm text-gray-500">No attributes extracted.</p>
                  )}
                </div>
              </div>
            </div>

            {/* Unknown watch warning */}
            {data.is_unknown && (
              <div className="bg-amber-50 border border-amber-200 rounded-2xl p-6 md:p-8">
                <div className="flex items-start gap-4">
                  <div className="shrink-0 w-12 h-12 bg-amber-100 rounded-xl flex items-center justify-center text-amber-600">
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                  </div>
                  <div className="min-w-0">
                    <h2 className="text-xl font-bold text-amber-900 mb-2">Unknown watch</h2>
                    <p className="text-amber-800">The image didn&apos;t match any watch in our database closely.</p>
                  </div>
                </div>
              </div>
            )}

            {/* Matching watches — always shown if candidates exist */}
            {data.candidates && data.candidates.length > 0 && (
              <div className="rounded-2xl border border-gray-200 bg-white shadow-sm p-6 md:p-8">
                <div className="flex flex-wrap items-center justify-between gap-2 mb-6">
                  <h2 className="text-xl font-bold text-gray-900">
                    {data.is_unknown ? 'Closest matches (low confidence)' : 'Matching watches'}
                  </h2>
                  <p className="text-xs text-gray-500">
                    {data.retrieval_time_ms != null && `${data.retrieval_time_ms}ms`}
                    {data.vlm_time_ms != null && ` · ${data.vlm_time_ms}ms analysis`}
                  </p>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {data.candidates.map((c) => (
                    <button
                      type="button" key={c.watch_id}
                      onClick={() => router.push(`/watches/${c.watch_id}`)}
                      className="text-left rounded-2xl border border-gray-200 bg-white p-4 hover:border-gray-300 hover:shadow-sm transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gray-900 focus-visible:ring-offset-2"
                    >
                      <div className="flex items-start gap-4">
                        {c.image_url && <img src={c.image_url.split(' ')[0]} alt="" className="w-20 h-20 object-cover rounded-2xl bg-gray-100 shrink-0" />}
                        <div className="min-w-0 flex-1">
                          <h3 className="font-semibold text-gray-900 mb-1 text-sm">{c.product_name}</h3>
                          {c.brand && <p className="text-xs text-gray-500 mb-2">{c.brand}</p>}
                          <SimilarityBar score={c.similarity_score ?? 0} />
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Debug panel — always shown */}
            {data.debug_info && (
              <div className="rounded-2xl border border-gray-100 bg-gray-50">
                <button type="button" onClick={() => setShowDebug(!showDebug)} className="w-full px-6 py-3 flex items-center justify-between text-left">
                  <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">Debug details</span>
                  <svg className={`w-4 h-4 text-gray-400 transition-transform ${showDebug ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {showDebug && (
                  <div className="px-6 pb-4 space-y-2 text-xs text-gray-600">
                    <p><span className="font-medium">Request ID:</span> {data.debug_info.request_id}</p>
                    <p><span className="font-medium">Detector:</span> {data.debug_info.models?.detector || 'N/A'} {data.debug_info.detector_used ? '(used)' : '(fallback)'}</p>
                    <p><span className="font-medium">Embedder:</span> {data.debug_info.models?.embedder || 'N/A'}</p>
                    <p><span className="font-medium">VLM:</span> {data.debug_info.models?.vlm || 'N/A'}</p>
                    <div className="flex flex-wrap gap-3 pt-1">
                      {Object.entries(data.debug_info.timing || {}).map(([k, v]) => (
                        <span key={k} className="bg-white border border-gray-200 rounded-lg px-2 py-1">{k}: {v != null ? `${v}ms` : '—'}</span>
                      ))}
                    </div>
                    {data.debug_info.debug_json_url && (
                      <a href={`${API_BASE}${data.debug_info.debug_json_url}`} target="_blank" rel="noopener noreferrer" className="inline-block mt-1 text-blue-600 underline">
                        View debug.json
                      </a>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {identifyMutation.isError && (
          <div className="bg-red-50 border border-red-200 rounded-2xl p-6 md:p-8">
            <div className="flex items-start gap-4">
              <div className="shrink-0 w-10 h-10 flex items-center justify-center text-red-600">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <h3 className="font-semibold text-red-900 mb-1">Identification failed</h3>
                <p className="text-red-700 text-sm">
                  {identifyMutation.error?.response?.data?.detail ?? identifyMutation.error?.message ?? 'Try another image or check your connection.'}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  )
}
