import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests if available (read on every request)
api.interceptors.request.use((config) => {
  if (typeof window === 'undefined') return config
  const token = localStorage.getItem('supabase_token')
  if (token) {
    config.headers = config.headers || {}
    config.headers['Authorization'] = `Bearer ${token}`
  } else if (config.headers && 'Authorization' in config.headers) {
    delete (config.headers as any)['Authorization']
  }
  return config
})

export interface WatchListQuery {
  query?: string
  brand?: string
  page?: number
  limit?: number
}

export interface WatchListResponse {
  watches: any[]
  total: number
  page: number
  limit: number
  total_pages: number
}

export interface WatchDetailResponse {
  watch_id: number
  brand: string | null
  product_name: string
  image_url: string | null
  specs: any[]
  comments_count: number
}

export interface CreateCommentRequest {
  content: string
  rating?: number
}

export interface CreateContributionRequest {
  spec_key: string
  proposed_value: string
  unit?: string
  note?: string
  evidence_url?: string
}

export interface VoteRequest {
  vote_type: 'confirm' | 'reject'
}

/** Admin: pending watch identification suggestions */
export interface WatchSuggestion {
  id: number
  submitted_by: string
  status: string
  sku?: string | null
  source?: string | null
  product_url?: string | null
  product_name?: string | null
  brand?: string | null
  image_url?: string | null
  ai_output_json?: Record<string, unknown> | null
  admin_notes?: string | null
  created_at: string
  updated_at: string
}

export interface AdminSuggestionActionBody {
  admin_notes?: string | null
}

export interface ProfileMe {
  id: string
  username?: string | null
  display_name?: string | null
  avatar_url?: string | null
  is_admin: boolean
}

