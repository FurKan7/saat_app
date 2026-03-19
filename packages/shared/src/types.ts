// Shared TypeScript types for Watch Community Platform

export type SourceType = 'official' | 'community_verified' | 'ai_estimated' | 'unknown';
export type ContributionStatus = 'pending' | 'approved' | 'rejected';
export type VoteType = 'confirm' | 'reject';
export type SpecSourceType = 'official' | 'scraper' | 'community' | 'ai';

export interface Watch {
  watch_id: number;
  source: string;
  product_url: string;
  image_url: string | null;
  brand: string | null;
  product_name: string;
  sku: string | null;
  price_raw: string | null;
  price_value: number | null;
  currency: 'TRY' | 'USD' | 'EUR' | 'GBP';
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface WatchSpecState {
  id: number;
  watch_id: number;
  spec_key: string;
  spec_value: string | null;
  unit: string | null;
  source_type: SourceType;
  confidence: number | null;
  resolved_at: string;
  updated_at: string;
}

export interface WatchSpecSource {
  id: number;
  watch_id: number;
  spec_key: string;
  spec_value: string;
  unit: string | null;
  source_type: SpecSourceType;
  source_name: string;
  source_url: string | null;
  created_at: string;
}

export interface WatchComment {
  id: number;
  watch_id: number;
  user_id: string;
  content: string;
  rating: number | null;
  created_at: string;
  updated_at: string;
  user?: {
    username: string | null;
    display_name: string | null;
    avatar_url: string | null;
  };
}

export interface WatchUserContribution {
  id: number;
  watch_id: number;
  user_id: string;
  spec_key: string;
  proposed_value: string;
  unit: string | null;
  note: string | null;
  evidence_url: string | null;
  status: ContributionStatus;
  created_at: string;
  updated_at: string;
  user?: {
    username: string | null;
    display_name: string | null;
  };
  votes?: {
    confirms: number;
    rejects: number;
    user_vote?: VoteType | null;
  };
}

export interface WatchContributionVote {
  id: number;
  contribution_id: number;
  user_id: string;
  vote_type: VoteType;
  created_at: string;
}

export interface WatchAIEstimation {
  id: number;
  watch_id: number;
  spec_key: string;
  estimated_value: string;
  unit: string | null;
  confidence: number;
  model_name: string;
  model_version: string | null;
  created_at: string;
}

export interface WatchEmbedding {
  id: number;
  watch_id: number;
  embedding: number[] | null;
  text_payload: string | null;
  model_name: string;
  created_at: string;
  updated_at: string;
}

export interface User {
  id: string;
  supabase_user_id: string;
  username: string | null;
  display_name: string | null;
  avatar_url: string | null;
  created_at: string;
  updated_at: string;
}

// API Request/Response types
export interface WatchListQuery {
  query?: string;
  brand?: string;
  page?: number;
  limit?: number;
}

export interface WatchListResponse {
  watches: Watch[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface WatchDetailResponse extends Watch {
  specs: WatchSpecState[];
  comments_count: number;
}

export interface CreateCommentRequest {
  content: string;
  rating?: number;
}

export interface CreateContributionRequest {
  spec_key: string;
  proposed_value: string;
  unit?: string;
  note?: string;
  evidence_url?: string;
}

export interface VoteRequest {
  vote_type: VoteType;
}

export interface AIIdentifyRequest {
  image_url?: string;
  image_file?: File;
  top_k?: number;
}

export interface AIIdentifyResponse {
  candidates: Array<{
    watch_id: number;
    brand: string | null;
    product_name: string;
    image_url: string | null;
    similarity_score: number;
  }>;
}

export interface WatchSpecsResponse {
  specs: WatchSpecState[];
  sources: Record<string, WatchSpecSource[]>;
}

