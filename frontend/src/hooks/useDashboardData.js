import { useCallback, useEffect, useRef, useState } from 'react'
import {
  fetchJobStatus,
  fetchStats,
  fetchTrades,
  getStreamUrl,
  startTradePull,
} from '../services/api'

const initialStats = {
  total_trades: 0,
  unique_clients: 0,
  unique_symbols: 0,
  total_trade_value: 0,
}

export function useDashboardData() {
  const [trades, setTrades] = useState([])
  const [stats, setStats] = useState(initialStats)
  const [totalTrades, setTotalTrades] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [isPulling, setIsPulling] = useState(false)
  const [job, setJob] = useState(null)
  const [error, setError] = useState('')
  const [connectionStatus, setConnectionStatus] = useState('connecting')
  const [actionMessage, setActionMessage] = useState(null)
  const eventSourceRef = useRef(null)

  const loadDashboard = useCallback(async (filters = {}) => {
    setError('')
    try {
      const [tradeResponse, statsResponse] = await Promise.all([
        fetchTrades({ pageSize: 8, ...filters }),
        fetchStats(),
      ])
      setTrades(tradeResponse.records)
      setTotalTrades(tradeResponse.total)
      setStats(statsResponse)
    } catch (requestError) {
      setError(
        requestError.response?.data?.detail ||
          'Unable to load trading data. Check that the backend is running.',
      )
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    loadDashboard()
  }, [loadDashboard])

  useEffect(() => {
    const eventSource = new EventSource(getStreamUrl())
    eventSourceRef.current = eventSource
    eventSource.onopen = () => setConnectionStatus('live')
    const handleIngestionEvent = async (event) => {
      setConnectionStatus('live')
      try {
        const eventData = JSON.parse(event.data)
        const updatedJob = await fetchJobStatus(eventData.job_id)
        setJob(updatedJob)
        setActionMessage(
          updatedJob.status === 'completed'
            ? { type: 'success', text: `Pull complete: ${updatedJob.inserted_records} new records saved.` }
            : { type: 'error', text: updatedJob.error_message || 'The data pull failed.' },
        )
        await loadDashboard()
      } catch (requestError) {
        setError(
          requestError.response?.data?.detail ||
            'The live update arrived, but the latest data could not be loaded.',
        )
      }
    }
    eventSource.addEventListener('ingestion.completed', handleIngestionEvent)
    eventSource.addEventListener('ingestion.failed', handleIngestionEvent)
    eventSource.onerror = () => setConnectionStatus('reconnecting')

    return () => {
      eventSource.removeEventListener('ingestion.completed', handleIngestionEvent)
      eventSource.removeEventListener('ingestion.failed', handleIngestionEvent)
      eventSource.close()
      eventSourceRef.current = null
    }
  }, [loadDashboard])

  const searchTrades = useCallback(
    (filters) => loadDashboard(filters),
    [loadDashboard],
  )

  const startPull = useCallback(async () => {
    setIsPulling(true)
    setError('')
    try {
      const newJob = await startTradePull()
      setJob(newJob)
      setActionMessage({ type: 'success', text: `Pull started. Job #${newJob.id} is processing in the background.` })
      if (newJob.status === 'completed') {
        await loadDashboard()
      }
    } catch (requestError) {
      setError(
        requestError.response?.data?.detail || 'Unable to start the data pull.',
      )
      setActionMessage({ type: 'error', text: 'The data pull could not be started.' })
    } finally {
      setIsPulling(false)
    }
  }, [loadDashboard])

  const refreshJob = useCallback(async () => {
    if (!job?.id) return
    try {
      const updatedJob = await fetchJobStatus(job.id)
      setJob(updatedJob)
      if (updatedJob.status === 'completed') {
        await loadDashboard()
      }
    } catch (requestError) {
      setError(
        requestError.response?.data?.detail || 'Unable to read ingestion status.',
      )
    }
  }, [job, loadDashboard])

  return {
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
    refreshJob,
    actionMessage,
  }
}
