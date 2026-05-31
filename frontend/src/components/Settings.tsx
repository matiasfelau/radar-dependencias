import { useState } from 'react'
import { apiClient } from '../services/apiClient'

export function Settings({ data, onRefresh }: any) {
  const [intervalValue, setIntervalValue] = useState((data?.scan_interval_seconds || 43200).toString())
  const [intervalUnit, setIntervalUnit] = useState('seconds')
  const [webhookUrl, setWebhookUrl] = useState(data?.webhook_url || '')
  const [telegramBotToken, setTelegramBotToken] = useState(data?.telegram_bot_token || '')
  const [telegramChatId, setTelegramChatId] = useState(data?.telegram_chat_id || '')
  const [saving, setSaving] = useState(false)
  const [testingTelegram, setTestingTelegram] = useState(false)
  const [telegramTestMessage, setTelegramTestMessage] = useState('')

  const formatIntervalDisplay = () => {
    const seconds = parseInt(intervalValue) || 0
    if (seconds < 60) return `${seconds}s`
    const minutes = Math.round(seconds / 60)
    if (minutes < 60) return `${minutes}m`
    const hours = Math.round(minutes / 60)
    return `${hours}h`
  }

  const convertToSeconds = () => {
    const value = parseInt(intervalValue) || 0
    if (intervalUnit === 'minutes') return value * 60
    if (intervalUnit === 'hours') return value * 3600
    return value
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      await apiClient.updateSettings({
        scan_interval_seconds: convertToSeconds(),
        webhook_url: webhookUrl,
        telegram_bot_token: telegramBotToken,
        telegram_chat_id: telegramChatId,
      })
      onRefresh?.()
    } finally {
      setSaving(false)
    }
  }

  const handleTestTelegram = async () => {
    setTestingTelegram(true)
    setTelegramTestMessage('')
    try {
      await apiClient.updateSettings({
        scan_interval_seconds: convertToSeconds(),
        webhook_url: webhookUrl,
        telegram_bot_token: telegramBotToken,
        telegram_chat_id: telegramChatId,
      })
      const result = await apiClient.testTelegram()
      setTelegramTestMessage(result.detail || 'Mensaje de prueba enviado.')
      onRefresh?.()
    } catch (error: any) {
      const detail = error?.response?.data?.detail
      setTelegramTestMessage(typeof detail === 'string' ? detail : 'No se pudo enviar la prueba a Telegram.')
    } finally {
      setTestingTelegram(false)
    }
  }

  return (
    <div className="card max-w-md">
      <h3 className="text-lg font-bold mb-4">Scanner Settings</h3>
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">Scan Interval</label>
          <div className="flex gap-2">
            <input
              type="number"
              value={intervalValue}
              onChange={(e) => setIntervalValue(e.target.value)}
              className="flex-1 px-3 py-2 border rounded"
              min="1"
            />
            <select
              value={intervalUnit}
              onChange={(e) => setIntervalUnit(e.target.value)}
              className="px-3 py-2 border rounded bg-white"
            >
              <option value="seconds">Seconds</option>
              <option value="minutes">Minutes</option>
              <option value="hours">Hours</option>
            </select>
          </div>
          <div className="text-xs text-gray-500 mt-1">Current: {formatIntervalDisplay()}</div>
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Webhook URL</label>
          <input
            type="url"
            value={webhookUrl}
            onChange={(e) => setWebhookUrl(e.target.value)}
            placeholder="https://example.com/webhooks"
            className="w-full px-3 py-2 border rounded"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Telegram Bot Token</label>
          <input
            type="password"
            value={telegramBotToken}
            onChange={(e) => setTelegramBotToken(e.target.value)}
            placeholder="123456789:ABCdefGHI..."
            className="w-full px-3 py-2 border rounded"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Telegram Chat ID</label>
          <input
            type="text"
            value={telegramChatId}
            onChange={(e) => setTelegramChatId(e.target.value)}
            placeholder="-1001234567890"
            className="w-full px-3 py-2 border rounded"
          />
          <div className="text-xs text-gray-500 mt-1">
            Usa el id del grupo tal como aparece en getUpdates (ej. -5169712985).
          </div>
          <button
            type="button"
            onClick={handleTestTelegram}
            disabled={testingTelegram || !telegramBotToken || !telegramChatId}
            className="mt-2 w-full px-3 py-2 border rounded text-sm hover:bg-gray-50 disabled:opacity-50"
          >
            {testingTelegram ? 'Enviando prueba...' : 'Probar Telegram'}
          </button>
          {telegramTestMessage && (
            <div className="text-xs mt-2 text-gray-600">{telegramTestMessage}</div>
          )}
        </div>
        <button onClick={handleSave} disabled={saving} className="btn-primary w-full">
          {saving ? 'Saving...' : 'Save Settings'}
        </button>
      </div>
    </div>
  )
}
