/** Base URL for auth redirects (password recovery). Prefer env in production. */
export function getAuthRedirectBaseUrl(): string {
  if (typeof window !== 'undefined') {
    return window.location.origin
  }
  return (process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000').replace(/\/$/, '')
}
