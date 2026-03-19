'use client'

interface SimilarityBarProps {
  score: number
  label?: string
  className?: string
}

export function SimilarityBar({ score, label, className = '' }: SimilarityBarProps) {
  const pct = Math.round(score * 100)
  return (
    <div className={className}>
      {label && (
        <span className="text-xs font-medium text-gray-500 uppercase tracking-wide block mb-1">
          {label}
        </span>
      )}
      <div className="h-2 w-full rounded-full bg-gray-100 overflow-hidden">
        <div
          className="h-full rounded-full bg-gray-900 transition-all duration-300"
          style={{ width: `${Math.min(100, pct)}%` }}
        />
      </div>
      <span className="text-xs text-gray-500 mt-1 inline-block">{pct}% match</span>
    </div>
  )
}
