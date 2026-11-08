import { BarChart3, BriefcaseBusiness, ChevronRight, CircleHelp, LayoutDashboard, Settings } from 'lucide-react'

const navigation = [
  { label: 'Overview', icon: LayoutDashboard, active: true },
  { label: 'Trade monitor', icon: BarChart3 },
  { label: 'Portfolios', icon: BriefcaseBusiness },
]

export function Sidebar({ activePage, onNavigate }) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">A</div>
        <div>
          <strong>ARHAM</strong>
          <span>FINTECH</span>
        </div>
      </div>

      <div className="sidebar-section-label">Workspace</div>
      <nav className="navigation" aria-label="Main navigation">
        {navigation.map(({ label, icon: Icon }) => {
          const page = label === 'Trade monitor' ? 'trade-monitor' : label.toLowerCase()
          return (
          <button className={`nav-item ${activePage === page ? 'active' : ''}`} key={label} type="button" onClick={() => onNavigate(page)}>
            <Icon size={18} strokeWidth={1.8} />
            <span>{label}</span>
            {activePage === page && <ChevronRight className="nav-chevron" size={15} />}
          </button>
          )
        })}
      </nav>

      <div className="sidebar-bottom">
        <button className={`nav-item ${activePage === 'help' ? 'active' : ''}`} type="button" onClick={() => onNavigate('help')}>
          <CircleHelp size={18} strokeWidth={1.8} />
          <span>Help centre</span>
        </button>
        <button className={`nav-item ${activePage === 'settings' ? 'active' : ''}`} type="button" onClick={() => onNavigate('settings')}>
          <Settings size={18} strokeWidth={1.8} />
          <span>Settings</span>
        </button>
        <div className="profile">
          <div className="avatar">JC</div>
          <div>
            <strong>Jeswin Chacko</strong>
            <span>Administrator</span>
          </div>
        </div>
      </div>
    </aside>
  )
}
