import { ArrowDownUp, Search } from 'lucide-react'

function formatPrice(value) {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 2,
  }).format(value)
}

function formatTime(value) {
  return new Intl.DateTimeFormat('en-IN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  }).format(new Date(value))
}

export function TradesTable({ trades, search, symbol, sortOrder, onSearchChange, onSymbolChange, onSortChange, isLoading }) {
  const symbols = [...new Set(trades.map((trade) => trade.symbol))].sort()

  return (
    <section className="panel trades-panel">
      <div className="panel-heading table-heading">
        <div>
          <p className="section-kicker">Live ledger</p>
          <h2>Recent trades</h2>
        </div>
        <span className="record-count">{trades.length} displayed</span>
      </div>
      <div className="table-filters">
        <label className="search-field">
          <Search size={16} />
          <input
            type="search"
            value={search}
            onChange={(event) => onSearchChange(event.target.value)}
            placeholder="Search trades, clients..."
            aria-label="Search trades"
          />
        </label>
        <select value={symbol} onChange={(event) => onSymbolChange(event.target.value)} aria-label="Filter by symbol">
          <option value="">All symbols</option>
          {symbols.map((item) => <option key={item} value={item}>{item}</option>)}
        </select>
        <label className="sort-button">
          <ArrowDownUp size={15} />
          <select value={sortOrder} onChange={(event) => onSortChange(event.target.value)} aria-label="Sort trades">
            <option value="latest">Latest</option>
            <option value="oldest">Oldest</option>
            <option value="value-high">Value high</option>
            <option value="value-low">Value low</option>
          </select>
        </label>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Trade ID</th>
              <th>Client</th>
              <th>Symbol</th>
              <th>Quantity</th>
              <th>Price</th>
              <th>Time</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr><td className="table-message" colSpan="6">Loading trade activity...</td></tr>
            ) : trades.length === 0 ? (
              <tr><td className="table-message" colSpan="6">No trades match the current filters.</td></tr>
            ) : trades.map((trade) => (
              <tr key={trade.trade_id}>
                <td className="trade-id">{trade.trade_id}</td>
                <td>{trade.client}</td>
                <td><span className="symbol-badge">{trade.symbol}</span></td>
                <td>{trade.quantity.toLocaleString('en-IN')}</td>
                <td className="price">{formatPrice(trade.price)}</td>
                <td className="muted">{formatTime(trade.timestamp)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}
