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
    <div className="brand-lockup"><div className="brand-mark">DP</div><div><div className="brand-name">DataPilot <span>AI</span></div><p>Dataset intelligence workspace</p></div></div>
    <div className="header-actions">
      <div className="connection"><span className={`connection-dot ${online ? 'is-online' : online === false ? 'is-offline' : ''}`} /> <span>Backend</span> <Badge value={online ? 'online' : online === false ? 'offline' : 'checking'} tone={online ? 'online' : online === false ? 'offline' : undefined} /></div>
      <button className="icon-button" type="button" onClick={() => { void checkHealth(); onRefresh() }} disabled={checking} aria-label="Refresh backend and datasets" title="Refresh"><span aria-hidden="true">↻</span></button>
    </div>
    {online === false && <StatusMessage title="Backend unavailable" detail="Start the FastAPI service at 127.0.0.1:8000 to load datasets." tone="error" />}
  </header>
}
