'use client'

interface SpecBadgeProps {
  sourceType: 'official' | 'community_verified' | 'ai_estimated' | 'disputed' | 'unknown'
}

export function SpecBadge({ sourceType }: SpecBadgeProps) {
  const badgeConfig: Record<
    SpecBadgeProps['sourceType'],
    { label: string; className: string }
  > = {
    official: {
      label: 'Official',
      className: 'bg-emerald-100 text-emerald-800',
    },
    community_verified: {
      label: 'Verified',
      className: 'bg-primary-100 text-primary-800',
    },
    ai_estimated: {
      label: 'AI',
      className: 'bg-violet-100 text-violet-800',
    },
    disputed: {
      label: 'Disputed',
      className: 'bg-amber-100 text-amber-800',
    },
    unknown: {
      label: 'Unknown',
      className: 'bg-stone-100 text-stone-600',
    },
  }

  const config = badgeConfig[sourceType]

  return (
    <span
      className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${config.className}`}
    >
      {config.label}
    </span>
  )
}

