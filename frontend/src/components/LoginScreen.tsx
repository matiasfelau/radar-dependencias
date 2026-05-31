import { useState, type FormEvent } from 'react'

type LoginScreenProps = {
  mode: 'login' | 'change-password'
  onSubmitLogin?: (username: string, password: string) => Promise<void> | void
  onSubmitChangePassword?: (currentPassword: string | null, newPassword: string) => Promise<void> | void
  loading?: boolean
  errorMessage?: string
  username?: string
}

export function LoginScreen({
  mode,
  onSubmitLogin,
  onSubmitChangePassword,
  loading,
  errorMessage,
  username,
}: LoginScreenProps) {
  const [loginUsername, setLoginUsername] = useState(username || '')
  const [password, setPassword] = useState('')
  const [currentPassword, setCurrentPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (mode === 'login') {
      void onSubmitLogin?.(loginUsername, password)
      return
    }

    if (password !== confirmPassword) {
      return
    }

    void onSubmitChangePassword?.(currentPassword || null, password)
  }

  const isPasswordMismatch = mode === 'change-password' && password.length > 0 && confirmPassword.length > 0 && password !== confirmPassword

  return (
    <main className="auth-screen min-h-screen flex items-center justify-center px-4">
      <div className="absolute inset-0 -z-10 bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800" />
      <div className="absolute inset-0 -z-10 opacity-40 bg-[radial-gradient(circle_at_top,_rgba(59,130,246,0.35),_transparent_36%),radial-gradient(circle_at_bottom_right,_rgba(16,185,129,0.18),_transparent_30%)]" />

      <section className="w-full max-w-md rounded-3xl border border-white/10 bg-white/95 p-8 shadow-2xl backdrop-blur">
        <div className="mb-8">
          <p className="text-sm uppercase tracking-[0.3em] text-slate-500">Dependency Radar</p>
          <h1 className="mt-3 text-3xl font-bold text-slate-900">
            {mode === 'login' ? 'Sign in to continue' : 'Change your password'}
          </h1>
          <p className="mt-2 text-sm text-slate-600">
            {mode === 'login'
              ? 'Access the dashboard, inventory, and vulnerability alerts.'
              : 'This account must change the password before continuing.'}
          </p>
        </div>

        <form className="space-y-5" onSubmit={handleSubmit}>
          {mode === 'login' && (
            <div>
              <label className="mb-2 block text-sm font-medium text-slate-700" htmlFor="username">
                Username
              </label>
              <input
                id="username"
                type="text"
                value={loginUsername}
                onChange={(event) => setLoginUsername(event.target.value)}
                className="w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-slate-900 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                placeholder="Enter your username"
                autoComplete="username"
                autoFocus
              />
            </div>
          )}

          {mode === 'change-password' && (
            <div>
              <label className="mb-2 block text-sm font-medium text-slate-700" htmlFor="current-password">
                Current password
              </label>
              <input
                id="current-password"
                type="password"
                value={currentPassword}
                onChange={(event) => setCurrentPassword(event.target.value)}
                className="w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-slate-900 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                placeholder="Current password"
                autoComplete="current-password"
                autoFocus
              />
            </div>
          )}

          <div>
            <label className="mb-2 block text-sm font-medium text-slate-700" htmlFor="password">
              {mode === 'login' ? 'Password' : 'New password'}
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-slate-900 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
              placeholder={mode === 'login' ? 'Enter your password' : 'Enter a new password'}
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
            />
          </div>

          {mode === 'change-password' && (
            <div>
              <label className="mb-2 block text-sm font-medium text-slate-700" htmlFor="confirm-password">
                Confirm new password
              </label>
              <input
                id="confirm-password"
                type="password"
                value={confirmPassword}
                onChange={(event) => setConfirmPassword(event.target.value)}
                className="w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-slate-900 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                placeholder="Repeat the new password"
                autoComplete="new-password"
              />
            </div>
          )}

          {errorMessage && <p className="text-sm font-medium text-red-600">{errorMessage}</p>}
          {isPasswordMismatch && <p className="text-sm font-medium text-red-600">Passwords do not match</p>}

          <button type="submit" className="btn-primary w-full py-3 text-base" disabled={loading}>
            {loading ? 'Working...' : mode === 'login' ? 'Enter dashboard' : 'Update password'}
          </button>
        </form>
      </section>
    </main>
  )
}