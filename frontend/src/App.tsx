import { QueryClientProvider } from '@tanstack/react-query'
import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { AuthProvider, useAuth } from '@/contexts/AuthContext'
import { queryClient } from '@/lib/query-client'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { Layout } from '@/components/Layout'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { AdminRoute } from '@/components/AdminRoute'
import Login from '@/pages/Login'
import Signup from '@/pages/Signup'
import Setup from '@/pages/Setup'
import Notes from '@/pages/Notes'
import Search from '@/pages/Search'
import Graph from '@/pages/Graph'
import Feedback from '@/pages/Feedback'
import Members from '@/pages/Members'
import Settings from '@/pages/Settings'

function ProtectedApp() {
  const { isAuthenticated, isLoading } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return (
      <div className="auth-shell">
        <LoadingSpinner />
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to={location.pathname === '/setup' ? '/setup' : '/login'} replace />
  }

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Notes />} />
        <Route path="/search" element={<Search />} />
        <Route path="/graph" element={<Graph />} />
        <Route path="/feedback" element={<Feedback />} />
        <Route path="/members" element={<AdminRoute><Members /></AdminRoute>} />
        <Route path="/settings" element={<AdminRoute><Settings /></AdminRoute>} />
      </Routes>
    </Layout>
  )
}

export default function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            <Route path="/setup" element={<Setup />} />
            <Route path="/*" element={<ProtectedApp />} />
          </Routes>
        </AuthProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  )
}
