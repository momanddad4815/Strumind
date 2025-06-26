'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import ProtectedRoute from '@/components/auth/ProtectedRoute'

export default function DashboardPage() {
  const router = useRouter()

  useEffect(() => {
    // Redirect to projects page
    router.push('/projects')
  }, [router])

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="spinner mb-4"></div>
          <p className="text-gray-600">Redirecting to projects...</p>
        </div>
      </div>
    </ProtectedRoute>
  )
}
