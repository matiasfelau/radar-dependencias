import { useState } from 'react'
import { apiClient } from '../services/apiClient'

export function Settings({ data, onRefresh }: any) {
  const [intervalValue, setIntervalValue] = useState((data?.scan_interval_seconds || 43200).toString())
  const [intervalUnit, setIntervalUnit] = useState('seconds')
  const [webhookUrl, setWebhookUrl] = useState(data?.webhook_url || '')
  const [saving, setSaving] = useState(false)

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
      })
      onRefresh?.()
    } finally {
      setSaving(false)
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
        <button onClick={handleSave} disabled={saving} className="btn-primary w-full">
          {saving ? 'Saving...' : 'Save Settings'}
        </button>
      </div>
    </div>
  )
}
