import { useState } from 'react'
import { Activity, CircleDollarSign, Network, Users } from 'lucide-react'
import './App.css'
import { Header } from './components/Header'
import { IngestionPanel } from './components/IngestionPanel'
import { Sidebar } from './components/Sidebar'
import { StatCard } from './components/StatCard'
import { TradesTable } from './components/TradesTable'
import { useDashboardData } from './hooks/useDashboardData'

function formatCurrency(value) {
  if (value >= 10000000) return `₹${(value / 10000000).toFixed(2)} Cr`
  if (value >= 100000) return `₹${(value / 100000).toFixed(2)} L`
  return `₹${value.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`
}

function App() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)
  const [activePage, setActivePage] = useState('overview')
  const [showNotifications, setShowNotifications] = useState(false)
  const [search, setSearch] = useState('')
  const [symbol, setSymbol] = useState('')
  const [sortOrder, setSortOrder] = useState('latest')
  const {
    trades,
    stats,
    totalTrades,
    isLoading,
    isPulling,
    job,
    error,
    connectionStatus,
    searchTrades,
    startPull,
    actionMessage,
  } = useDashboardData()

  const updateSearch = (value) => {
    setSearch(value)
    searchTrades({ search: value, symbol })
  }

  const updateSymbol = (value) => {
    setSymbol(value)
    searchTrades({ search, symbol: value })
  }

  const navigate = (page) => {
    setActivePage(page)
    setIsSidebarOpen(false)
    setShowNotifications(false)
  }

  const sortedTrades = [...trades].sort((first, second) => {
    if (sortOrder === 'oldest') return new Date(first.timestamp) - new Date(second.timestamp)
    if (sortOrder === 'value-high') return (second.quantity * second.price) - (first.quantity * first.price)
    if (sortOrder === 'value-low') return (first.quantity * first.price) - (second.quantity * second.price)
    return new Date(second.timestamp) - new Date(first.timestamp)
  })

  const pageCopy = {
    'trade-monitor': ['Trade monitor', 'Review live exchange activity and filter persisted trades.'],
    portfolios: ['Portfolios', 'Portfolio views are not connected to a backend endpoint yet. Use Trade monitor to review exchange activity.'],
    help: ['Help centre', 'Use Start data pull to fetch trades in the background. The live connection indicator confirms SSE status.'],
    settings: ['Settings', 'Connection settings are managed through the frontend and backend environment files.'],
  }
  const currentPage = pageCopy[activePage]
  const showTradeWorkspace = activePage === 'overview' || activePage === 'trade-monitor'

  return (
    <div className="app-shell">
      <div className={`sidebar-overlay ${isSidebarOpen ? 'visible' : ''}`} onClick={() => setIsSidebarOpen(false)} />
      <div className={isSidebarOpen ? 'sidebar-mobile-open' : ''}><Sidebar activePage={activePage} onNavigate={navigate} /></div>
      <main className="main-content">
        <Header connectionStatus={connectionStatus} onMenuClick={() => setIsSidebarOpen(true)} onNotifications={() => setShowNotifications((visible) => !visible)} hasNotification={Boolean(job)} />
        {showNotifications && (
          <div className="notification-panel">
            <strong>Notifications</strong>
            <p>{job ? `Latest pull is ${job.status}.` : 'No ingestion jobs yet.'}</p>
            {job && <button type="button" onClick={() => { setShowNotifications(false); navigate('trade-monitor') }}>View trade monitor</button>}
          </div>
        )}
        <div className="content">
          {!showTradeWorkspace ? (
            <section className="panel page-placeholder">
              <p className="section-kicker">Workspace</p>
              <h2>{currentPage[0]}</h2>
              <p>{currentPage[1]}</p>
              {activePage === 'portfolios' && <button className="primary-button" type="button" onClick={() => navigate('trade-monitor')}>Open trade monitor</button>}
              {activePage === 'help' && <button className="primary-button" type="button" onClick={() => navigate('overview')}>Return to overview</button>}
              {activePage === 'settings' && <button className="primary-button" type="button" onClick={() => navigate('overview')}>Return to overview</button>}
            </section>
          ) : (
          <>
          <div className="welcome-row">
            <div>
              <p className="section-kicker">{activePage === 'trade-monitor' ? 'Trade monitor' : 'Market overview'}</p>
              <h2 className="page-title">{activePage === 'trade-monitor' ? 'Live exchange activity' : 'Trade activity at a glance'}</h2>
            </div>
            <p className="last-sync">Last sync <strong>{job?.completed_at ? new Date(job.completed_at).toLocaleTimeString() : 'Awaiting data'}</strong></p>
          </div>

          {error && <div className="error-banner" role="alert">{error}</div>}

          <div className="stats-grid">
            <StatCard label="Total trades" value={totalTrades.toLocaleString('en-IN')} detail="Across all collected sessions" icon={Activity} trend={{ positive: true, value: 'Live' }} />
            <StatCard label="Unique clients" value={stats.unique_clients.toLocaleString('en-IN')} detail="Active trading counterparties" icon={Users} tone="blue" />
            <StatCard label="Unique symbols" value={stats.unique_symbols.toLocaleString('en-IN')} detail="In the current trade universe" icon={Network} tone="purple" />
            <StatCard label="Total trade value" value={formatCurrency(stats.total_trade_value)} detail="Gross notional value tracked" icon={CircleDollarSign} tone="orange" />
          </div>

          <IngestionPanel job={job} isPulling={isPulling} onStart={startPull} connectionStatus={connectionStatus} actionMessage={actionMessage} />
          <TradesTable
            trades={sortedTrades}
            search={search}
            symbol={symbol}
            sortOrder={sortOrder}
            onSearchChange={updateSearch}
            onSymbolChange={updateSymbol}
            onSortChange={setSortOrder}
            isLoading={isLoading}
          />
          </>
          )}
          <footer className="footer-note">ARHAM Fintech · Transforming Finance with Technology</footer>
        </div>
      </main>
    </div>
  )
}

export default App
