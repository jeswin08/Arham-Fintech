import { ArrowDownRight, ArrowUpRight } from 'lucide-react'

export function StatCard({ label, value, detail, icon: Icon, tone = 'green', trend }) {
  return (
    <article className={`stat-card ${tone}`}>
      <div className="stat-card-top">
        <div className="stat-icon"><Icon size={19} strokeWidth={1.8} /></div>
        {trend && (
          <span className={`trend ${trend.positive ? 'positive' : 'negative'}`}>
            {trend.positive ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
            {trend.value}
          </span>
        )}
      </div>
      <p>{label}</p>
      <h2>{value}</h2>
      <span className="stat-detail">{detail}</span>
    </article>
  )
}
