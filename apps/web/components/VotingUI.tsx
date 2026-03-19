'use client'

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { useState } from 'react'

interface VotingUIProps {
  contributionId: number
  votes?: {
    confirms: number
    rejects: number
    user_vote?: 'confirm' | 'reject' | null
  }
}

export function VotingUI({ contributionId, votes }: VotingUIProps) {
  const [localVotes, setLocalVotes] = useState(votes)
  const queryClient = useQueryClient()

  const voteMutation = useMutation({
    mutationFn: async (voteType: 'confirm' | 'reject') => {
      const response = await api.post(`/contributions/${contributionId}/vote`, {
        vote_type: voteType,
      })
      return response.data
    },
    onSuccess: (data) => {
      setLocalVotes(data.votes)
      queryClient.invalidateQueries({ queryKey: ['watch-contributions'] })
    },
  })

  const currentVotes = localVotes || votes || { confirms: 0, rejects: 0, user_vote: null }

  const handleVote = (voteType: 'confirm' | 'reject') => {
    voteMutation.mutate(voteType)
  }

  return (
    <div className="flex items-center gap-2">
      <button
        onClick={() => handleVote('confirm')}
        disabled={voteMutation.isPending}
        className={`px-3 py-1 rounded text-sm font-medium ${
          currentVotes.user_vote === 'confirm'
            ? 'bg-green-600 text-white'
            : 'bg-green-100 text-green-800 hover:bg-green-200'
        } disabled:opacity-50`}
      >
        ✓ {currentVotes.confirms}
      </button>
      <button
        onClick={() => handleVote('reject')}
        disabled={voteMutation.isPending}
        className={`px-3 py-1 rounded text-sm font-medium ${
          currentVotes.user_vote === 'reject'
            ? 'bg-red-600 text-white'
            : 'bg-red-100 text-red-800 hover:bg-red-200'
        } disabled:opacity-50`}
      >
        ✗ {currentVotes.rejects}
      </button>
    </div>
  )
}

