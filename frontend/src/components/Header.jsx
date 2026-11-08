import { Bell, Menu, Wifi } from 'lucide-react'

const currentDate = new Intl.DateTimeFormat('en-GB', {
  day: '2-digit',
  month: 'short',
  year: 'numeric',
}).format(new Date())

export function Header({ connectionStatus, onMenuClick, onNotifications, hasNotification }) {
  return (
    <header className="topbar">
      <button className="mobile-menu" type="button" onClick={onMenuClick} aria-label="Open navigation">
        <Menu size={21} />
      </button>
      <div>
        <p className="breadcrumb">Workspace / Overview</p>
        <h1>Good morning, Jeswin <span>✦</span></h1>
      </div>
      <div className="topbar-actions">
        <span className={`connection-badge ${connectionStatus}`}>
          <Wifi size={14} />
          {connectionStatus === 'live'
            ? 'Live connection'
            : connectionStatus === 'reconnecting'
              ? 'Reconnecting'
              : 'Connection unavailable'}
        </span>
        <button className="icon-button" type="button" aria-label="Notifications" onClick={onNotifications}>
          <Bell size={18} />
          {hasNotification && <span className="notification-dot" />}
        </button>
        <div className="date-label">{currentDate}</div>
      </div>
    </header>
  )
}
