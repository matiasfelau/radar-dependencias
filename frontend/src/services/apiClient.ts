import axios, { AxiosInstance } from 'axios'
import type { AlertsResponse } from './hooks'

const API_BASE_URL = (import.meta as any).env.VITE_API_URL || 'http://localhost:8000/api/v1'

export interface ApiClient {
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
  rotateProjectApiKey(projectName: string): Promise<any>
  createProject(projectName: string): Promise<any>
  deleteProject(projectName: string): Promise<any>
}

const client: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
})

export const apiClient: ApiClient = {
  async getProjects() {
    const response = await client.get('/projects')
    return response.data
  },

  async getAlerts() {
    const response = await client.get('/alerts/active')
    return response.data
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
