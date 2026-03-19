import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests if available
if (typeof window !== 'undefined') {
  const token = localStorage.getItem('supabase_token')
  if (token) {
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`
  }
}

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

