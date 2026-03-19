import type { Metadata } from 'next'
import Script from 'next/script'
import { Inter } from 'next/font/google'
import './globals.css'
import { Providers } from './providers'

const fontSans = Inter({
  subsets: ['latin'],
  variable: '--font-sans',
})

export const metadata: Metadata = {
  title: 'Watch Community Platform',
  description: 'Discover, share, and contribute watch specifications',
}

// Reload once on chunk load timeout (workaround for ChunkLoadError)
const chunkRetryScript = `window.__chunkRetries=0;window.addEventListener('error',function(e){if(e.message&&String(e.message).indexOf('Loading chunk')!==-1&&(window.__chunkRetries||0)<2){window.__chunkRetries=(window.__chunkRetries||0)+1;window.location.reload();}});`

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={fontSans.variable}>
      <body className="font-sans antialiased">
        <Script id="chunk-retry" strategy="beforeInteractive">
          {chunkRetryScript}
        </Script>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}

