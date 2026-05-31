import { useEffect, useMemo, useState } from 'react'
import { apiClient } from '../services/apiClient'
import type { UserSummary } from '../services/hooks'

const AVAILABLE_PERMISSIONS = ['view_dashboard', 'view_alerts', 'view_settings', 'manage_projects', 'manage_settings', 'run_scans', 'manage_users']

type UserDraft = {
  is_admin: boolean
  permissions: string[]
}

export function AdminUsersPanel() {
  const [users, setUsers] = useState<UserSummary[]>([])
  const [drafts, setDrafts] = useState<Record<number, UserDraft>>({})
  const [loading, setLoading] = useState(true)
  const [savingByUser, setSavingByUser] = useState<Record<number, boolean>>({})
  const [resetByUser, setResetByUser] = useState<Record<number, boolean>>({})
  const [error, setError] = useState('')
  const [createUsername, setCreateUsername] = useState('')
  const [createIsAdmin, setCreateIsAdmin] = useState(false)
  const [createPermissions, setCreatePermissions] = useState<string[]>([])
  const [creating, setCreating] = useState(false)
  const [createdTempPassword, setCreatedTempPassword] = useState('')

  const loadUsers = async () => {
    setLoading(true)
    setError('')
    try {
      const response = await apiClient.listUsers()
      setUsers(response)
      setDrafts((current) => {
        const next: Record<number, UserDraft> = { ...current }
        for (const user of response) {
          if (!next[user.id]) {
            next[user.id] = {
              is_admin: user.is_admin,
              permissions: user.permissions,
            }
          }
        }
        return next
      })
    } catch (fetchError: any) {
      setError(fetchError?.response?.data?.detail || 'Could not load users')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadUsers()
  }, [])

  const canCreate = useMemo(() => createUsername.trim().length > 1, [createUsername])

  const toggleCreatePermission = (permission: string) => {
    setCreatePermissions((current) =>
      current.includes(permission) ? current.filter((item) => item !== permission) : [...current, permission],
    )
  }

  const togglePermission = (userId: number, permission: string) => {
    setDrafts((current) => {
      const draft = current[userId] || { is_admin: false, permissions: [] }
      const permissions = draft.permissions.includes(permission)
        ? draft.permissions.filter((item) => item !== permission)
        : [...draft.permissions, permission]
      return { ...current, [userId]: { ...draft, permissions } }
    })
  }

  const toggleAdmin = (userId: number) => {
    setDrafts((current) => {
      const draft = current[userId] || { is_admin: false, permissions: [] }
      return { ...current, [userId]: { ...draft, is_admin: !draft.is_admin } }
    })
  }

  const handleCreateUser = async () => {
    if (!canCreate) {
      setError('Username is required')
      return
    }

    setCreating(true)
    setError('')
    setCreatedTempPassword('')
    try {
      const response = await apiClient.createUser({
        username: createUsername.trim(),
        is_admin: createIsAdmin,
        permissions: createPermissions,
      })
      setCreatedTempPassword(response.temp_password)
      setCreateUsername('')
      setCreateIsAdmin(false)
      setCreatePermissions([])
      await loadUsers()
    } catch (createError: any) {
      setError(createError?.response?.data?.detail || 'Could not create user')
    } finally {
      setCreating(false)
    }
  }

  const handleSaveUser = async (user: UserSummary) => {
    const draft = drafts[user.id]
    if (!draft) return

    setSavingByUser((current) => ({ ...current, [user.id]: true }))
    setError('')
    try {
      await apiClient.updateUser(user.id, {
        is_admin: draft.is_admin,
        permissions: draft.permissions,
      })
      await loadUsers()
    } catch (saveError: any) {
      setError(saveError?.response?.data?.detail || 'Could not update user')
    } finally {
      setSavingByUser((current) => ({ ...current, [user.id]: false }))
    }
  }

  const handleResetPassword = async (userId: number) => {
    setResetByUser((current) => ({ ...current, [userId]: true }))
    setError('')
    try {
      const response = await apiClient.resetUserPassword(userId)
      setCreatedTempPassword(response.temp_password)
    } catch (resetError: any) {
      setError(resetError?.response?.data?.detail || 'Could not reset password')
    } finally {
      setResetByUser((current) => ({ ...current, [userId]: false }))
    }
  }

  return (
    <div className="space-y-6">
      <section className="card border border-slate-200">
        <div className="mb-4 flex items-center justify-between gap-3">
          <div>
            <h3 className="text-lg font-bold text-slate-900">Admin users</h3>
            <p className="text-sm text-slate-500">Create users, assign permissions, and reset passwords.</p>
          </div>
          <button type="button" className="btn-secondary text-sm" onClick={() => void loadUsers()}>
            Refresh
          </button>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <h4 className="font-semibold text-slate-800">Create user</h4>
            <div>
              <label className="mb-2 block text-sm font-medium text-slate-700">Username</label>
              <input
                value={createUsername}
                onChange={(event) => setCreateUsername(event.target.value)}
                className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                placeholder="new.user"
              />
            </div>
            <label className="flex items-center gap-2 text-sm text-slate-700">
              <input type="checkbox" checked={createIsAdmin} onChange={(event) => setCreateIsAdmin(event.target.checked)} />
              Admin user
            </label>
            <div>
              <div className="mb-2 text-sm font-medium text-slate-700">Permissions</div>
              <div className="grid gap-2 sm:grid-cols-2">
                {AVAILABLE_PERMISSIONS.map((permission) => (
                  <label key={permission} className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm">
                    <input
                      type="checkbox"
                      checked={createPermissions.includes(permission)}
                      onChange={() => toggleCreatePermission(permission)}
                    />
                    {permission}
                  </label>
                ))}
              </div>
            </div>
            <button type="button" className="btn-primary w-full" onClick={() => void handleCreateUser()} disabled={creating}>
              {creating ? 'Creating...' : 'Create user'}
            </button>
          </div>

          <div className="space-y-4 rounded-2xl border border-dashed border-slate-300 bg-white p-4">
            <h4 className="font-semibold text-slate-800">Temporary password</h4>
            {createdTempPassword ? (
              <div className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
                Copy it now and share it securely. The user must change it on first login.
                <div className="mt-2 flex gap-2">
                  <input className="w-full rounded-lg border border-amber-200 bg-white px-3 py-2 font-mono text-sm" readOnly value={createdTempPassword} />
                  <button type="button" className="btn-secondary text-sm" onClick={() => navigator.clipboard.writeText(createdTempPassword)}>
                    Copy
                  </button>
                </div>
              </div>
            ) : (
              <p className="text-sm text-slate-500">A temporary password appears here after creating or resetting a user.</p>
            )}
          </div>
        </div>

        {error && <div className="mt-4 text-sm font-medium text-red-600">{error}</div>}
      </section>

      <section className="card border border-slate-200">
        <h4 className="mb-4 text-lg font-bold text-slate-900">Existing users</h4>
        {loading ? (
          <div className="text-sm text-slate-500">Loading users...</div>
        ) : users.length === 0 ? (
          <div className="text-sm text-slate-500">No users found.</div>
        ) : (
          <div className="space-y-4">
            {users.map((user) => {
              const draft = drafts[user.id] || { is_admin: user.is_admin, permissions: user.permissions }
              return (
                <div key={user.id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                    <div>
                      <div className="font-semibold text-slate-900">{user.username}</div>
                      <div className="text-sm text-slate-500">
                        {user.is_admin ? 'Admin' : 'User'} · {user.must_change_password ? 'Must change password' : 'Password set'} · Created {new Date(user.created_at).toLocaleString()}
                      </div>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <button type="button" className="btn-secondary text-sm" onClick={() => void handleResetPassword(user.id)} disabled={!!resetByUser[user.id]}>
                        {resetByUser[user.id] ? 'Resetting...' : 'Reset password'}
                      </button>
                      <button type="button" className="btn-primary text-sm" onClick={() => void handleSaveUser(user)} disabled={!!savingByUser[user.id]}>
                        {savingByUser[user.id] ? 'Saving...' : 'Save'}
                      </button>
                    </div>
                  </div>

                  <div className="mt-4 space-y-3">
                    <label className="flex items-center gap-2 text-sm text-slate-700">
                      <input type="checkbox" checked={draft.is_admin} onChange={() => toggleAdmin(user.id)} />
                      Admin user
                    </label>

                    <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                      {AVAILABLE_PERMISSIONS.map((permission) => (
                        <label key={permission} className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm">
                          <input
                            type="checkbox"
                            checked={draft.permissions.includes(permission)}
                            onChange={() => togglePermission(user.id, permission)}
                          />
                          {permission}
                        </label>
                      ))}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </section>
    </div>
  )
}