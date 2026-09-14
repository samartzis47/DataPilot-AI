import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { Badge, StatusMessage } from './Common'

export function Header({ onRefresh }: { onRefresh: () => void }) {
  const [online, setOnline] = useState<boolean | null>(null)
  const [checking, setChecking] = useState(false)

  async function checkHealth() {
    setChecking(true)
    try { await api.health(); setOnline(true) } catch { setOnline(false) } finally { setChecking(false) }
  }

  useEffect(() => { void checkHealth() }, [])

  return <header className="app-header">
    <div className="header-row">
      <div className="brand-lockup">
        <div className="brand-mark" aria-hidden="true">DP</div>
        <div><div className="brand-name">DataPilot <span>AI</span></div><p>Dataset intelligence workspace</p></div>
      </div>
      <div className="header-actions">
        <div className="connection" role="status">
          <span>Backend</span>
          <Badge value={checking || online === null ? 'checking' : online ? 'online' : 'offline'} tone={checking ? undefined : online ? 'online' : online === false ? 'offline' : undefined} />
        </div>
        <button className="icon-button" type="button" onClick={() => { void checkHealth(); onRefresh() }} disabled={checking} aria-label="Refresh backend and datasets" title="Refresh backend and datasets">
          {checking ? <span className="spinner" aria-hidden="true" /> : <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M20 7v5h-5M4 17v-5h5" /><path d="M6.1 6.1A8 8 0 0 1 19.5 10M4.5 14A8 8 0 0 0 17.9 17.9" /></svg>}
        </button>
      </div>
    </div>
    {online === false && <StatusMessage title="Backend unavailable" detail="The data service could not be reached. Check that the application is running, then refresh to reconnect." tone="error" />}
  </header>
}
