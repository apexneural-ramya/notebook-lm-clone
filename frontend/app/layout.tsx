import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'NotebookLM - Understand Anything',
  description: 'Document-grounded AI assistant with accurate citations',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}

