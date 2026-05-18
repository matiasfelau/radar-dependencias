import { useEffect, useState } from 'react'
import { apiClient } from '../services/apiClient'

// 1. Definimos las estructuras de datos (Interfaces)
export interface Project {
  id: number;
  name: string;
  api_key: string;
}

export interface AlertsResponse {
  total: number;
  items: PackageHealthItem[];
}

export interface PackageHealthItem {
  project_name: string;
  environment_name: string;
  package_name: string;
  installed_version: string;
  has_vulnerability: boolean;
  has_update: boolean;
  latest_version: string | null;
  max_severity: string | null;
  updated_at: string;
}

export interface SettingsResponse {
  scan_interval_seconds: number;
  webhook_url: string;
}

// 2. Aplicamos los tipos genéricos en los Hooks

export function useProjects() {
  // Le indicamos a TS que data puede ser un array de proyectos o null
  const [data, setData] = useState<Project[] | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<any>(null)

  useEffect(() => {
    apiClient
      .getProjects()
      .then(setData)
      .catch(setError)
      .finally(() => setLoading(false))
  }, [])

  return { data, loading, error }
}

export function useAlerts() {
  // Aquí le indicamos que data tendrá la propiedad .total
  const [data, setData] = useState<AlertsResponse | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<any>(null)

  useEffect(() => {
    apiClient
      .getAlerts()
      .then(setData)
      .catch(setError)
      .finally(() => setLoading(false))
  }, [])

  return { data, loading, error }
}

export function useSettings() {
  // Le indicamos la estructura de las configuraciones
  const [data, setData] = useState<SettingsResponse | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<any>(null)

  useEffect(() => {
    apiClient
      .getSettings()
      .then(setData)
      .catch(setError)
      .finally(() => setLoading(false))
  }, [])

  return { data, loading, error }
}