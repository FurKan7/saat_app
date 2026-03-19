// Zod schemas for validation

import { z } from 'zod';

export const createCommentSchema = z.object({
  content: z.string().min(1).max(5000),
  rating: z.number().int().min(1).max(5).optional(),
});

export const createContributionSchema = z.object({
  spec_key: z.string().min(1).max(100),
  proposed_value: z.string().min(1),
  unit: z.string().max(50).optional(),
  note: z.string().max(1000).optional(),
  evidence_url: z.string().url().optional().or(z.literal('')),
});

export const voteSchema = z.object({
  vote_type: z.enum(['confirm', 'reject']),
});

export const watchListQuerySchema = z.object({
  query: z.string().optional(),
  brand: z.string().optional(),
  page: z.coerce.number().int().min(1).default(1),
  limit: z.coerce.number().int().min(1).max(100).default(20),
});

export const aiIdentifySchema = z.object({
  image_url: z.string().url().optional(),
  top_k: z.coerce.number().int().min(1).max(20).default(5),
});

// Spec key normalization map (Turkish -> English)
export const specKeyNormalization: Record<string, string> = {
  // Turkish variations
  'kasa çapı': 'case_diameter_mm',
  'kasa çap': 'case_diameter_mm',
  'çap': 'case_diameter_mm',
  'kasa kalınlığı': 'case_thickness_mm',
  'kalınlık': 'case_thickness_mm',
  'ağırlık': 'weight_g',
  'gram': 'weight_g',
  'su geçirmezlik': 'water_resistance_atm',
  'su geçirmez': 'water_resistance_atm',
  'cam tipi': 'glass_type',
  'cam': 'glass_type',
  'hareket tipi': 'movement_type',
  'mekanizma': 'movement_type',
  'cinsiyet': 'gender',
  'lug genişliği': 'lug_width_mm',
  'lug to lug': 'lug_to_lug_mm',
  'lug-to-lug': 'lug_to_lug_mm',
  'kronometre': 'chronometer',
  'kasa rengi': 'case_color',
  'kadran tipi': 'dial_type',
  'arka kapak': 'case_back',
  
  // English variations (normalize to canonical)
  'case_diameter': 'case_diameter_mm',
  'diameter': 'case_diameter_mm',
  'case_thickness': 'case_thickness_mm',
  'thickness': 'case_thickness_mm',
  'weight': 'weight_g',
  'water_resistance': 'water_resistance_atm',
  'wr': 'water_resistance_atm',
  'glass': 'glass_type',
  'crystal': 'glass_type',
  'movement': 'movement_type',
  'caliber': 'movement_type',
  'lug_width': 'lug_width_mm',
  'lug_to_lug': 'lug_to_lug_mm',
};

export function normalizeSpecKey(key: string): string {
  const normalized = key.toLowerCase().trim();
  return specKeyNormalization[normalized] || normalized;
}

