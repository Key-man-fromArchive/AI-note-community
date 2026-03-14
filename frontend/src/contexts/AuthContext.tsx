import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react'
import { apiClient } from '@/lib/api'

interface User {
  user_id: number
  email: string
  name: string
  org_id: number
  org_slug: string
  role: string
}

interface SignupRequest {
  email: string
  password: string
  name: string
  org_name?: string
  org_slug?: string
}

interface AuthContextValue {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  signup: (data: SignupRequest) => Promise<void>
  applySession: (data: AuthSession) => void
  logout: () => void
}

interface AuthSession {
  access_token: string
  refresh_token: string
  user_id: number
  email: string
  name: string
  org_id: number
  org_slug: string
  role: string
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const applySession = useCallback((data: AuthSession) => {
    apiClient.setToken(data.access_token)
    apiClient.setRefreshToken(data.refresh_token)
    setUser({
      user_id: data.user_id,
      email: data.email,
      name: data.name,
      org_id: data.org_id,
      org_slug: data.org_slug,
      role: data.role,
    })
  }, [])

  const fetchUser = useCallback(async () => {
    const data = await apiClient.get<User>('/auth/me')
    setUser(data)
  }, [])

  useEffect(() => {
    const bootstrap = async () => {
      try {
        if (apiClient.getToken() || apiClient.getRefreshToken()) {
          await fetchUser()
        }
      } catch {
        apiClient.clearToken()
        apiClient.clearRefreshToken()
      } finally {
        setIsLoading(false)
      }
    }
    bootstrap()
  }, [fetchUser])

  const login = useCallback(async (email: string, password: string) => {
    const data = await apiClient.post<AuthSession>('/auth/login', { email, password })
    applySession(data)
  }, [applySession])

  const signup = useCallback(async (request: SignupRequest) => {
    const data = await apiClient.post<AuthSession>('/members/signup', request)
    applySession(data)
  }, [applySession])

  const logout = useCallback(() => {
    apiClient.clearToken()
    apiClient.clearRefreshToken()
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, isLoading, isAuthenticated: !!user, login, signup, applySession, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
