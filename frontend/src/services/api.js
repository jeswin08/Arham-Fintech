import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
})

export async function fetchTrades({ page = 1, pageSize = 8, search = '', symbol = '' } = {}) {
  const { data } = await api.get('/api/trades', {
    params: {
      page,
      page_size: pageSize,
      ...(search ? { search } : {}),
      ...(symbol ? { symbol } : {}),
    },
  })
  return data
}

export async function fetchStats() {
  const { data } = await api.get('/api/trades/stats')
  return data
}

export async function startTradePull() {
  const { data } = await api.post('/api/trades/pull', null, {
    params: {
      record_count: 2000,
      delay_seconds: 15,
    },
  })
  return data
}

export async function fetchJobStatus(jobId) {
  const { data } = await api.get(`/api/trades/pull/${jobId}`)
  return data
}

export function getStreamUrl() {
  return `${api.defaults.baseURL}/api/trades/stream`
}
