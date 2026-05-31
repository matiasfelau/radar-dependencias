import { useState } from 'react'
import { apiClient } from '../services/apiClient'

export function Inventory({ data }: any) {
  type ProjectStateMap = Record<string, string>
  type ProjectLoadingMap = Record<string, boolean>

  const [loadingByProject, setLoadingByProject] = useState<ProjectLoadingMap>({})
  const [keyByProject, setKeyByProject] = useState<ProjectStateMap>({})
  const [errorByProject, setErrorByProject] = useState<ProjectStateMap>({})
  const [deleteLoadingByProject, setDeleteLoadingByProject] = useState<ProjectLoadingMap>({})
  const [deleteErrorByProject, setDeleteErrorByProject] = useState<ProjectStateMap>({})

  const handleGenerateApiKey = async (projectName: string) => {
    setLoadingByProject((prev: ProjectLoadingMap) => ({ ...prev, [projectName]: true }))
    setErrorByProject((prev: ProjectStateMap) => ({ ...prev, [projectName]: '' }))
    try {
      const response = await apiClient.rotateProjectApiKey(projectName)
      setKeyByProject((prev: ProjectStateMap) => ({ ...prev, [projectName]: response.api_key }))
    } catch (error: any) {
      const detail = error?.response?.data?.detail || 'Could not generate API key'
      setErrorByProject((prev: ProjectStateMap) => ({ ...prev, [projectName]: detail }))
    } finally {
      setLoadingByProject((prev: ProjectLoadingMap) => ({ ...prev, [projectName]: false }))
    }
  }

  const handleDeleteProject = async (projectName: string) => {
    const confirmed = window.confirm(`Delete project "${projectName}" and all its data?`)
    if (!confirmed) return
    setDeleteLoadingByProject((prev) => ({ ...prev, [projectName]: true }))
    setDeleteErrorByProject((prev) => ({ ...prev, [projectName]: '' }))
    try {
      await apiClient.deleteProject(projectName)
      // Refresh to reload inventory after deletion
      setTimeout(() => window.location.reload(), 300)
    } catch (error: any) {
      const detail = error?.response?.data?.detail || 'Could not delete project'
      setDeleteErrorByProject((prev) => ({ ...prev, [projectName]: detail }))
    } finally {
      setDeleteLoadingByProject((prev) => ({ ...prev, [projectName]: false }))
    }
  }

  const handleCopy = async (projectName: string) => {
    const key = keyByProject[projectName]
    if (!key) return
    await navigator.clipboard.writeText(key)
  }

  // Project creation state
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [newProjectName, setNewProjectName] = useState('')
  const [createLoading, setCreateLoading] = useState(false)
  const [createError, setCreateError] = useState('')
  const [createdProject, setCreatedProject] = useState<any>(null)

  const refreshAfterCopy = async (key: string) => {
    await navigator.clipboard.writeText(key)
    window.location.reload()
  }

  const handleCreateProject = async () => {
    if (!newProjectName.trim()) {
      setCreateError('Project name is required')
      return
    }
    setCreateLoading(true)
    setCreateError('')
    try {
      const response = await apiClient.createProject(newProjectName)
      setCreatedProject(response)
      setNewProjectName('')
      setShowCreateForm(false)
    } catch (error: any) {
      setCreateError(error?.response?.data?.detail || 'Failed to create project')
    } finally {
      setCreateLoading(false)
    }
  }

  if (!data) {
    if (showCreateForm) {
      return (
        <div className="space-y-4">
          <div className="p-4 rounded bg-blue-50 border border-blue-200">
            <h3 className="font-bold mb-3">Create New Project</h3>
            <div className="flex gap-2 mb-2">
              <input
                type="text"
                placeholder="Project name (e.g., my-app)"
                className="flex-1 px-3 py-2 border rounded"
                value={newProjectName}
                onChange={(e) => setNewProjectName(e.target.value)}
                disabled={createLoading}
              />
              <button
                className="btn-primary"
                onClick={handleCreateProject}
                disabled={createLoading}
              >
                {createLoading ? 'Creating...' : 'Create'}
              </button>
              <button
                className="btn-secondary"
                onClick={() => setShowCreateForm(false)}
                disabled={createLoading}
              >
                Cancel
              </button>
            </div>
            {createError && <div className="text-sm text-red-600">{createError}</div>}
          </div>
        </div>
      )
    }
    return (
      <div className="text-center space-y-4">
        <p className="text-gray-500">No projects found</p>
        <button className="btn-primary" onClick={() => setShowCreateForm(true)}>
          + Create New Project
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {showCreateForm ? (
        <div className="p-4 rounded bg-blue-50 border border-blue-200">
          <h3 className="font-bold mb-3">Create New Project</h3>
          <div className="flex gap-2 mb-2">
            <input
              type="text"
              placeholder="Project name (e.g., my-app)"
              className="flex-1 px-3 py-2 border rounded"
              value={newProjectName}
              onChange={(e) => setNewProjectName(e.target.value)}
              disabled={createLoading}
            />
            <button
              className="btn-primary"
              onClick={handleCreateProject}
              disabled={createLoading}
            >
              {createLoading ? 'Creating...' : 'Create'}
            </button>
            <button
              className="btn-secondary"
              onClick={() => setShowCreateForm(false)}
              disabled={createLoading}
            >
              Cancel
            </button>
          </div>
          {createError && <div className="text-sm text-red-600">{createError}</div>}
        </div>
      ) : (
        <button className="btn-primary mb-2" onClick={() => setShowCreateForm(true)}>
          + Create New Project
        </button>
      )}

      {createdProject && (
        <div className="p-4 rounded bg-green-50 border border-green-200">
          <h3 className="font-bold text-green-800 mb-2">✓ Project Created!</h3>
          <div className="text-sm mb-2">
            <strong>Project:</strong> {createdProject.project_name}
          </div>
          <div className="bg-white p-2 rounded border mb-2">
            <div className="text-xs text-gray-500 mb-1">API Key (copy now):</div>
            <div className="flex gap-2">
              <input className="w-full px-2 py-1 text-sm border rounded" readOnly value={createdProject.api_key} />
              <button
                className="btn-primary text-sm"
                onClick={() => refreshAfterCopy(createdProject.api_key)}
              >
                Copy
              </button>
            </div>
          </div>
          <button className="btn-secondary text-sm" onClick={() => setCreatedProject(null)}>
            Close
          </button>
        </div>
      )}

      {data.projects?.map((project: any) => (
        <div key={project.name} className="card">
          <div className="flex items-center justify-between gap-3 mb-4">
            <h3 className="text-lg font-bold">{project.name}</h3>
            <div className="flex gap-2">
              {!project.is_internal && (
                <>
                  <button
                    type="button"
                    className="btn-secondary text-sm"
                    onClick={() => handleGenerateApiKey(project.name)}
                    disabled={!!loadingByProject[project.name]}
                    title="Genera una nueva key para CI/CD"
                  >
                    {loadingByProject[project.name] ? 'Generating...' : 'Generate API key'}
                  </button>
                  <button
                    type="button"
                    className="btn-danger text-sm"
                    onClick={() => handleDeleteProject(project.name)}
                    disabled={!!deleteLoadingByProject[project.name]}
                    title="Delete project and all data"
                  >
                    {deleteLoadingByProject[project.name] ? 'Deleting...' : 'Delete'}
                  </button>
                </>
              )}
            </div>
          </div>

          {project.is_internal && (
            <div className="mb-4 text-xs font-semibold uppercase tracking-wide text-amber-700">
              Internal radar project: read-only
            </div>
          )}

          {keyByProject[project.name] && (
            <div className="mb-4 p-3 rounded bg-blue-50 border border-blue-200">
              <div className="text-xs font-semibold text-blue-800 mb-1">New API key (copy now)</div>
              <div className="flex gap-2">
                <input
                  className="w-full px-2 py-1 text-sm border rounded bg-white"
                  readOnly
                  value={keyByProject[project.name]}
                />
                <button
                  type="button"
                  className="btn-primary text-sm"
                  onClick={() => refreshAfterCopy(keyByProject[project.name])}
                >
                  Copy
                </button>
              </div>
            </div>
          )}

          {errorByProject[project.name] && (
            <div className="mb-4 text-sm text-red-600">{errorByProject[project.name]}</div>
          )}
          {deleteErrorByProject[project.name] && (
            <div className="mb-4 text-sm text-red-600">{deleteErrorByProject[project.name]}</div>
          )}

          <div className="space-y-3">
            {project.environments?.map((env: any) => (
              <div key={env.name} className="bg-gray-50 p-3 rounded">
                <div className="font-semibold text-sm text-gray-700">{env.name}</div>
                <div className="text-xs text-gray-500 mb-2">
                  {new Date(env.updated_at).toLocaleString()}
                </div>
                <div className="text-sm">
                  {env.dependencies.length} dependencies:
                  <ul className="mt-1 list-disc list-inside text-gray-600">
                    {env.dependencies.slice(0, 5).map((dep: any) => (
                      <li key={dep.package_name}>
                        {dep.package_name}@{dep.installed_version}
                      </li>
                    ))}
                    {env.dependencies.length > 5 && (
                      <li>... and {env.dependencies.length - 5} more</li>
                    )}
                  </ul>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
