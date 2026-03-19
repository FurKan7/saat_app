'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { useState } from 'react'

interface CommentsListProps {
  watchId: number
}

export function CommentsList({ watchId }: CommentsListProps) {
  const [commentText, setCommentText] = useState('')
  const [rating, setRating] = useState<number | undefined>(undefined)
  const queryClient = useQueryClient()

  const { data: comments, isLoading } = useQuery({
    queryKey: ['watch-comments', watchId],
    queryFn: async () => {
      const response = await api.get(`/watches/${watchId}/comments`)
      return response.data
    },
  })

  const createComment = useMutation({
    mutationFn: async (data: { content: string; rating?: number }) => {
      const response = await api.post(`/watches/${watchId}/comments`, data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['watch-comments', watchId] })
      setCommentText('')
      setRating(undefined)
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!commentText.trim()) {
      alert('Please enter a comment')
      return
    }

    createComment.mutate({
      content: commentText,
      rating: rating,
    })
  }

  return (
    <div>
      <form onSubmit={handleSubmit} className="mb-6">
        <div className="mb-3">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Add a comment
          </label>
          <textarea
            value={commentText}
            onChange={(e) => setCommentText(e.target.value)}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
            placeholder="Share your thoughts about this watch..."
          />
        </div>

        <div className="mb-3">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Rating (optional)
          </label>
          <div className="flex gap-2">
            {[1, 2, 3, 4, 5].map((star) => (
              <button
                key={star}
                type="button"
                onClick={() => setRating(star)}
                className={`text-2xl ${
                  rating && star <= rating
                    ? 'text-yellow-400'
                    : 'text-gray-300 hover:text-yellow-300'
                }`}
              >
                ★
              </button>
            ))}
          </div>
        </div>

        <button
          type="submit"
          disabled={createComment.isPending}
          className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
        >
          {createComment.isPending ? 'Posting...' : 'Post Comment'}
        </button>
      </form>

      {isLoading ? (
        <div className="text-center py-4">
          <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"></div>
        </div>
      ) : comments && comments.length > 0 ? (
        <div className="space-y-4">
          {comments.map((comment: any) => (
            <div key={comment.id} className="border rounded-lg p-4">
              <div className="flex items-start justify-between mb-2">
                <div>
                  {comment.user && (
                    <p className="font-medium text-sm">
                      {comment.user.display_name || comment.user.username || 'Anonymous'}
                    </p>
                  )}
                  {comment.rating && (
                    <div className="flex gap-1 mt-1">
                      {[1, 2, 3, 4, 5].map((star) => (
                        <span
                          key={star}
                          className={star <= comment.rating ? 'text-yellow-400' : 'text-gray-300'}
                        >
                          ★
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                <span className="text-xs text-gray-500">
                  {new Date(comment.created_at).toLocaleDateString()}
                </span>
              </div>
              <p className="text-gray-700">{comment.content}</p>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-gray-600">No comments yet. Be the first to comment!</p>
      )}
    </div>
  )
}

