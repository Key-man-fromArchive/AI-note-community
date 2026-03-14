const BASE_URL = '/api'

export class ApiError extends Error {
  constructor(
    public status: number,
    public body: string,
  ) {
    super(`API Error: ${status}`)
  }
}

export function getApiErrorMessage(error: unknown, fallback: string) {
  if (!(error instanceof ApiError)) {
    return fallback
  }

  try {
    const parsed = JSON.parse(error.body) as { detail?: string }
    if (parsed.detail) {
      return parsed.detail
    }
  } catch {
    return fallback
  }

  return fallback
}

class ApiClient {
  private token: string | null = null

  setToken(token: string) {
    this.token = token
    localStorage.setItem('auth_token', token)
  }

  getToken() {
    return this.token
  }

  clearToken() {
    this.token = null
    localStorage.removeItem('auth_token')
  }

  setRefreshToken(token: string) {
    localStorage.setItem('refresh_token', token)
  }

  getRefreshToken() {
    return localStorage.getItem('refresh_token')
  }

  clearRefreshToken() {
    localStorage.removeItem('refresh_token')
  }

  restoreToken() {
    this.token = localStorage.getItem('auth_token')
  }

  private async tryRefreshToken() {
    const refreshToken = this.getRefreshToken()
    if (!refreshToken) return false

    try {
      const response = await fetch(`${BASE_URL}/auth/token/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      })
      if (!response.ok) return false
      const data = await response.json()
      this.setToken(data.access_token)
      return true
    } catch {
      return false
    }
  }

  private async requestRaw(path: string, options?: RequestInit): Promise<Response> {
    const headers: Record<string, string> = {
      ...(options?.headers as Record<string, string> | undefined),
    }
    if (!(options?.body instanceof FormData) && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json'
    }
    if (this.token) {
      headers.Authorization = `Bearer ${this.token}`
    }

    const url = `${BASE_URL}${path}`
    const response = await fetch(url, { ...options, headers })

    if (!response.ok) {
      const body = await response.text()
      if (response.status === 401 && !path.startsWith('/auth/')) {
        const refreshed = await this.tryRefreshToken()
        if (refreshed) {
          return this.requestRaw(path, options)
        }
      }
      throw new ApiError(response.status, body)
    }

    return response
  }

  async request<T>(path: string, options?: RequestInit): Promise<T> {
    const response = await this.requestRaw(path, options)

    if (response.status === 204) {
      return undefined as T
    }

    return response.json()
  }

  async getBlob(path: string) {
    const response = await this.requestRaw(path, { method: 'GET' })
    return response.blob()
  }

  get<T>(path: string) {
    return this.request<T>(path, { method: 'GET' })
  }

  post<T>(path: string, body?: unknown) {
    return this.request<T>(path, {
      method: 'POST',
      body: body === undefined ? undefined : JSON.stringify(body),
    })
  }

  put<T>(path: string, body?: unknown) {
    return this.request<T>(path, {
      method: 'PUT',
      body: body === undefined ? undefined : JSON.stringify(body),
    })
  }

  delete<T>(path: string) {
    return this.request<T>(path, { method: 'DELETE' })
  }
}

export const apiClient = new ApiClient()
apiClient.restoreToken()
