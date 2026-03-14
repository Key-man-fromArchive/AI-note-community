import { Navigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'

export function AdminRoute({ children }: { children: React.ReactNode }) {
  const { user } = useAuth()
  const isAdmin = user?.role === 'owner' || user?.role === 'admin'
  return isAdmin ? <>{children}</> : <Navigate to="/" replace />
}
