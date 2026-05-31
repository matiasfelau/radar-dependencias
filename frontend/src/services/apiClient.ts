import axios, { AxiosInstance } from 'axios'
import type { AlertsResponse, AuthUser, CreateUserResponse, LoginResponse, UserSummary } from './hooks'

const API_BASE_URL = (import.meta as any).env.VITE_API_URL || 'http://localhost:8000/api/v1'
const AUTH_TOKEN_KEY = 'radar-auth-token'

export function getStoredAuthToken() {
  return sessionStorage.getItem(AUTH_TOKEN_KEY)
}

export function setStoredAuthToken(token: string) {
  sessionStorage.setItem(AUTH_TOKEN_KEY, token)
}

export function clearStoredAuthToken() {
  sessionStorage.removeItem(AUTH_TOKEN_KEY)
}

export interface ApiClient {
  login(username: string, password: string): Promise<LoginResponse>
  logout(): Promise<void>
  getCurrentUser(): Promise<AuthUser>
  changePassword(currentPassword: string | null, newPassword: string): Promise<AuthUser>
  listUsers(): Promise<UserSummary[]>
  createUser(data: { username: string; is_admin: boolean; permissions: string[] }): Promise<CreateUserResponse>
  updateUser(userId: number, data: { is_admin: boolean; permissions: string[] }): Promise<UserSummary>
  resetUserPassword(userId: number): Promise<{ temp_password: string }>
  getProjects(): Promise<any>
  getAlerts(): Promise<AlertsResponse>
  triggerDebugScan(): Promise<{
    activated: number
    resolved: number
    scanned_pairs: number
    upserted?: number
    deleted?: number
    vulnerable?: number
    with_updates?: number
  }>
  getSettings(): Promise<any>
  updateSettings(data: any): Promise<any>
  testTelegram(): Promise<{ ok: boolean; detail: string }>
  rotateProjectApiKey(projectName: string): Promise<any>
  createProject(projectName: string): Promise<any>
  deleteProject(projectName: string): Promise<any>
}

const client: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
})

client.interceptors.request.use((config) => {
  const token = getStoredAuthToken()
  if (token) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401) {
      clearStoredAuthToken()
    }
    return Promise.reject(error)
  },
)

export const apiClient: ApiClient = {
  async login(username: string, password: string) {
    const response = await client.post('/auth/login', { username, password })
    return response.data
  },

  async logout() {
    await client.post('/auth/logout')
    clearStoredAuthToken()
  },

  async getCurrentUser() {
    const response = await client.get('/auth/me')
    return response.data
  },

  async changePassword(currentPassword: string | null, newPassword: string) {
    const response = await client.post('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    })
    return response.data
  },

  async listUsers() {
    const response = await client.get('/admin/users')
    return response.data
  },

  async createUser(data) {
    const response = await client.post('/admin/users', data)
    return response.data
  },

  async updateUser(userId: number, data) {
    const response = await client.patch(`/admin/users/${userId}`, data)
    return response.data
  },

  async resetUserPassword(userId: number) {
    const response = await client.post(`/admin/users/${userId}/reset-password`)
    return response.data
  },

  async getProjects() {
    const response = await client.get('/projects')
    return response.data
  },

  async getAlerts() {
    const token = getStoredAuthToken()
    const controller = new AbortController()
    const timeoutId = window.setTimeout(() => controller.abort(), 60000)

    try {
      const response = await fetch(`${API_BASE_URL}/alerts/active`, {
        method: 'GET',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        signal: controller.signal,
      })

      if (!response.ok) {
        const errorBody = await response.json().catch(() => null)
        throw {
          response: {
            status: response.status,
            data: errorBody,
          },
        }
      }

      return response.json()
    } finally {
      window.clearTimeout(timeoutId)
    }
  },

  async triggerDebugScan() {
    const response = await client.post('/alerts/debug/scan')
    return response.data
  },

  async getSettings() {
    const response = await client.get('/settings')
    return response.data
  },

  async updateSettings(data: any) {
    const response = await client.put('/settings', data)
    return response.data
  },

  async testTelegram() {
    const response = await client.post('/settings/test-telegram')
    return response.data
  },

  async rotateProjectApiKey(projectName: string) {
    const response = await client.post(`/projects/${encodeURIComponent(projectName)}/api-key/rotate`)
    return response.data
  },

  async createProject(projectName: string) {
    const response = await client.post('/projects', {
      project_name: projectName,
    })
    return response.data
  },

  async deleteProject(projectName: string) {
    const response = await client.delete(`/projects/${encodeURIComponent(projectName)}`)
    return response.data
  },
}

export default client
