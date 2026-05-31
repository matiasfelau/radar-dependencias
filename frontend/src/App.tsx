import { useEffect, useState } from 'react'
import { apiClient } from './services/apiClient'
import { clearStoredAuthToken, getStoredAuthToken, setStoredAuthToken } from './services/apiClient'
import { useProjects, useAlerts, useSettings } from './services/hooks'
import { Inventory } from './components/Inventory'
import { Alerts } from './components/Alerts'
import { Settings } from './components/Settings'
import { LoginScreen } from './components/LoginScreen'
import { AdminUsersPanel } from './components/AdminUsersPanel'
import type { AuthUser } from './services/hooks'
import './index.css'

type Tab = 'inventory' | 'alerts' | 'settings' | 'admin'

type AuthStatus = 'loading' | 'signed-out' | 'force-password' | 'signed-in'

function App() {
  const [authStatus, setAuthStatus] = useState<AuthStatus>('loading')
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null)
  const [loginError, setLoginError] = useState('')
  const [authLoading, setAuthLoading] = useState(false)

  useEffect(() => {
    const bootstrap = async () => {
      const token = getStoredAuthToken()
      if (!token) {
        setAuthStatus('signed-out')
        return
      }

      try {
        const user = await apiClient.getCurrentUser()
        setCurrentUser(user)
        setAuthStatus(user.must_change_password ? 'force-password' : 'signed-in')
      } catch {
        clearStoredAuthToken()
        setCurrentUser(null)
        setAuthStatus('signed-out')
      }
    }

    void bootstrap()
  }, [])

  const handleLogin = async (username: string, password: string) => {
    setAuthLoading(true)
    setLoginError('')
    try {
      const result = await apiClient.login(username, password)
      setStoredAuthToken(result.access_token)
      setCurrentUser(result.user)
      setAuthStatus(result.must_change_password ? 'force-password' : 'signed-in')
    } catch (error: any) {
      setLoginError(error?.response?.data?.detail || 'Invalid credentials')
    } finally {
      setAuthLoading(false)
    }
  }

  const handlePasswordChange = async (currentPassword: string | null, newPassword: string) => {
    setAuthLoading(true)
    setLoginError('')
    try {
      const updatedUser = await apiClient.changePassword(currentPassword, newPassword)
      setCurrentUser(updatedUser)
      setAuthStatus('signed-in')
    } catch (error: any) {
      setLoginError(error?.response?.data?.detail || 'Could not change password')
    } finally {
      setAuthLoading(false)
    }
  }

  const handleLogout = async () => {
    try {
      await apiClient.logout()
    } catch {
      clearStoredAuthToken()
    }
    clearStoredAuthToken()
    setCurrentUser(null)
    setAuthStatus('signed-out')
    setLoginError('')
  }

  if (authStatus === 'loading') {
    return <LoadingScreen />
  }

  if (authStatus === 'signed-out') {
    return <LoginScreen mode="login" onSubmitLogin={handleLogin} loading={authLoading} errorMessage={loginError} />
  }

  if (authStatus === 'force-password') {
    return (
      <LoginScreen
        mode="change-password"
        onSubmitChangePassword={handlePasswordChange}
        loading={authLoading}
        errorMessage={loginError}
        username={currentUser?.username}
      />
    )
  }

  return <Dashboard currentUser={currentUser} onLogout={handleLogout} />
}

type DashboardProps = {
  currentUser: AuthUser | null
  onLogout: () => void
}

function Dashboard({ currentUser, onLogout }: DashboardProps) {
  const [activeTab, setActiveTab] = useState<Tab>('inventory')
  const [scanRunning, setScanRunning] = useState(false)
  const [scanMessage, setScanMessage] = useState('')
  const projectsState = useProjects()
  const alertsState = useAlerts()
  const settingsState = useSettings()

  const handleRefresh = () => {
    // Trigger re-fetch by resetting state
    window.location.reload()
  }

  const handleManualScan = async () => {
    setScanRunning(true)
    setScanMessage('')
    try {
      const result = await apiClient.triggerDebugScan()
      setScanMessage(
        `Scan completed: ${result.activated ?? result.upserted ?? 0} activated, ${result.resolved ?? result.deleted ?? 0} resolved, ${result.scanned_pairs} packages scanned`
      )
      setTimeout(() => window.location.reload(), 800)
    } catch (error: any) {
      const detail = error?.response?.data?.detail || 'Could not run manual scan'
      setScanMessage(detail)
    } finally {
      setScanRunning(false)
    }
  }

  return (
    <main className="app-shell min-h-screen">
      <header className="mb-8 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-4xl font-bold text-blue-700 mb-2">Dependency Radar</h1>
          <p className="text-gray-600">Software Composition Analysis & Threat Intelligence</p>
          {currentUser && (
            <p className="mt-2 text-sm text-slate-500">
              Signed in as <span className="font-semibold text-slate-700">{currentUser.username}</span>
              {currentUser.is_admin ? ' · Admin' : ''}
            </p>
          )}
        </div>
        <button onClick={onLogout} className="btn-secondary text-sm">
          Log out
        </button>
      </header>

      <nav className="flex gap-2 mb-6 border-b">
        {(['inventory', 'alerts', 'settings', 'admin'] as const)
          .filter((tab) => tab !== 'admin' || currentUser?.is_admin)
          .map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 font-medium transition ${
              activeTab === tab
                ? 'border-b-2 border-blue-600 text-blue-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </nav>

      <div className="mb-4 text-right">
        <button onClick={handleRefresh} className="btn-secondary text-sm">
          🔄 Refresh
        </button>
      </div>

      <section>
        {activeTab === 'inventory' && (
          <div>
            <h2 className="text-2xl font-bold mb-4">Project Inventory</h2>
            {projectsState.loading ? (
              <div className="text-center text-gray-500">Loading...</div>
            ) : projectsState.error ? (
              <div className="text-center text-red-600">Error loading projects</div>
            ) : (
              <Inventory data={projectsState.data} />
            )}
          </div>
        )}

        {activeTab === 'alerts' && (
          <div>
            <div className="flex items-center justify-between gap-3 mb-4">
              <h2 className="text-2xl font-bold">Active Alerts</h2>
              <button
                type="button"
                className="btn-secondary text-sm"
                onClick={handleManualScan}
                disabled={scanRunning}
                title="Trigger a manual vulnerability scan"
              >
                {scanRunning ? 'Scanning...' : 'Run manual scan'}
              </button>
            </div>
            {scanMessage && <div className="mb-4 text-sm text-gray-600">{scanMessage}</div>}
            <div className="text-sm text-gray-600 mb-4">
              Total: {alertsState.data?.total || 0} dependency alerts
            </div>
            {alertsState.loading ? (
              <div className="text-center text-gray-500">Loading...</div>
            ) : alertsState.error ? (
              <div className="text-center text-red-600">Error loading alerts</div>
            ) : (
              <Alerts data={alertsState.data} />
            )}
          </div>
        )}

        {activeTab === 'settings' && (
          <div>
            <h2 className="text-2xl font-bold mb-4">Configuration</h2>
            {settingsState.loading ? (
              <div className="text-center text-gray-500">Loading...</div>
            ) : settingsState.error ? (
              <div className="text-center text-red-600">Error loading settings</div>
            ) : (
              <Settings data={settingsState.data} onRefresh={handleRefresh} />
            )}
          </div>
        )}

        {activeTab === 'admin' && currentUser?.is_admin && (
          <div>
            <h2 className="text-2xl font-bold mb-4">Admin Console</h2>
            <AdminUsersPanel />
          </div>
        )}
      </section>
    </main>
  )
}

function LoadingScreen() {
  return (
    <main className="auth-screen min-h-screen flex items-center justify-center px-4">
      <div className="rounded-3xl border border-white/10 bg-white/90 px-8 py-6 shadow-2xl">
        <div className="text-sm uppercase tracking-[0.3em] text-slate-500">Dependency Radar</div>
        <div className="mt-3 text-lg font-semibold text-slate-900">Loading session...</div>
      </div>
    </main>
  )
}

export default App
