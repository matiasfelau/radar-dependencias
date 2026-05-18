export function Alerts({ data }: any) {
  if (!data?.items?.length) return <div className="text-center text-gray-500">No active alerts</div>

  const getSeverityBadgeClass = (severity: string) => {
    switch (severity) {
      case 'Critical':
        return 'badge-critical'
      case 'High':
        return 'badge-high'
      case 'Medium':
        return 'badge-medium'
      case 'Low':
        return 'badge-low'
      default:
        return 'badge-low'
    }
  }

  return (
    <div className="space-y-3">
      {data.items.map((alert: any) => {
        const severityLabel = alert.max_severity || 'Unknown'
        const statusLabel = alert.has_vulnerability
          ? 'Vulnerable'
          : alert.has_update
            ? 'Update available'
            : 'Healthy'

        return (
          <div key={`${alert.project_name}-${alert.environment_name}-${alert.package_name}`} className="card border-l-4 border-red-500">
            <div className="flex justify-between items-start mb-2">
              <div>
                <div className="font-bold text-red-700">{alert.package_name}</div>
                <div className="text-sm text-gray-600">
                  {alert.project_name} / {alert.environment_name}
                </div>
                <div className="text-xs text-gray-500">
                  Installed: {alert.installed_version}
                  {alert.latest_version ? ` · Latest: ${alert.latest_version}` : ''}
                </div>
              </div>
              <div className="text-right space-y-1">
                <span className={getSeverityBadgeClass(severityLabel)}>{severityLabel}</span>
                <div className={`text-xs font-semibold ${alert.has_vulnerability ? 'text-red-700' : alert.has_update ? 'text-amber-700' : 'text-green-700'}`}>
                  {statusLabel}
                </div>
              </div>
            </div>
            <div className="flex gap-2 flex-wrap text-xs text-gray-600">
              <span className="inline-block px-2 py-1 bg-gray-100 rounded">Vulnerability: {alert.has_vulnerability ? 'Yes' : 'No'}</span>
              <span className="inline-block px-2 py-1 bg-gray-100 rounded">Update: {alert.has_update ? 'Yes' : 'No'}</span>
              {alert.latest_version && (
                <span className="inline-block px-2 py-1 bg-gray-100 rounded">Latest: {alert.latest_version}</span>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}
