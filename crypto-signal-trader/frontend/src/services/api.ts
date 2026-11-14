import axios from 'axios'
import type {
  DashboardStats,
  Signal,
  SignalCreate,
  Position,
  Order,
  Portfolio,
  TelegramChannel,
  TelegramMessage,
  EquitySnapshot,
  PerformanceMetrics,
  RagStatus,
  RagQueryResponse,
  SignalEvaluationResponse,
  KnowledgeDoc,
} from '../types'

const apiClient = axios.create({
  baseURL: '',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
})

// Response error interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.detail || error.message || 'An error occurred'
    console.error(`[API Error] ${error.config?.url}:`, message)
    return Promise.reject(new Error(message))
  }
)

export const api = {
  // ── Dashboard ────────────────────────────────────────────────────────────
  async getDashboard(): Promise<DashboardStats> {
    const res = await apiClient.get<DashboardStats>('/api/v1/dashboard')
    return res.data
  },

  // ── Signals ──────────────────────────────────────────────────────────────
  async getSignals(status?: string, limit = 50, offset = 0): Promise<Signal[]> {
    const params = new URLSearchParams()
    if (status) params.append('status', status)
    params.append('limit', limit.toString())
    params.append('offset', offset.toString())
    const res = await apiClient.get<Signal[]>(`/api/v1/signals?${params.toString()}`)
    return res.data
  },

  async getSignal(id: string): Promise<Signal> {
    const res = await apiClient.get<Signal>(`/api/v1/signals/${id}`)
    return res.data
  },

  async createSignal(data: SignalCreate): Promise<Signal> {
    const res = await apiClient.post<Signal>('/api/v1/signals', data)
    return res.data
  },

  // ── Positions ────────────────────────────────────────────────────────────
  async getPositions(status?: string, limit = 50): Promise<Position[]> {
    const params = new URLSearchParams()
    if (status) params.append('status', status)
    params.append('limit', limit.toString())
    const res = await apiClient.get<Position[]>(`/api/v1/positions?${params.toString()}`)
    return res.data
  },

  async getPosition(id: string): Promise<Position> {
    const res = await apiClient.get<Position>(`/api/v1/positions/${id}`)
    return res.data
  },

  async closePosition(id: string): Promise<Position> {
    const res = await apiClient.post<Position>(`/api/v1/positions/${id}/close`)
    return res.data
  },

  // ── Orders ───────────────────────────────────────────────────────────────
  async getOrders(limit = 100, offset = 0): Promise<Order[]> {
    const res = await apiClient.get<Order[]>(`/api/v1/orders?limit=${limit}&offset=${offset}`)
    return res.data
  },

  // ── Portfolio ────────────────────────────────────────────────────────────
  async getPortfolio(): Promise<Portfolio> {
    const res = await apiClient.get<Portfolio>('/api/v1/portfolio')
    return res.data
  },

  // ── Channels ─────────────────────────────────────────────────────────────
  async getChannels(): Promise<TelegramChannel[]> {
    const res = await apiClient.get<TelegramChannel[]>('/api/v1/channels')
    return res.data
  },

  async addChannel(identifier: string): Promise<TelegramChannel> {
    const res = await apiClient.post<TelegramChannel>('/api/v1/channels', {
      channel_identifier: identifier,
    })
    return res.data
  },

  async updateChannel(
    id: string,
    updates: { is_active?: boolean; is_monitored?: boolean }
  ): Promise<TelegramChannel> {
    const res = await apiClient.patch<TelegramChannel>(`/api/v1/channels/${id}`, updates)
    return res.data
  },

  async deleteChannel(id: string): Promise<void> {
    await apiClient.delete(`/api/v1/channels/${id}`)
  },

  async getChannelMessages(channelId: string, limit = 50): Promise<TelegramMessage[]> {
    const res = await apiClient.get<TelegramMessage[]>(
      `/api/v1/channels/${channelId}/messages?limit=${limit}`
    )
    return res.data
  },

  // ── Analytics ────────────────────────────────────────────────────────────
  async getEquityCurve(days = 30): Promise<EquitySnapshot[]> {
    const res = await apiClient.get<EquitySnapshot[]>(`/api/v1/analytics/equity-curve?days=${days}`)
    return res.data
  },

  async getPerformance(): Promise<PerformanceMetrics> {
    const res = await apiClient.get<PerformanceMetrics>('/api/v1/analytics/performance')
    return res.data
  },

  // ── Health ───────────────────────────────────────────────────────────────
  async getHealth(): Promise<{
    status: string
    paper_trading: boolean
    telegram_connected: boolean
    market_data_connected: boolean
    version: string
  }> {
    const res = await apiClient.get('/health')
    return res.data
  },

  // ── RAG & AI Copilot ──────────────────────────────────────────────────────
  async getRagStatus(): Promise<RagStatus> {
    const res = await apiClient.get<RagStatus>('/api/v1/rag/status')
    return res.data
  },

  async queryRag(
    query: string,
    top_k = 5,
    doc_type?: string,
    symbol?: string
  ): Promise<RagQueryResponse> {
    const res = await apiClient.post<RagQueryResponse>('/api/v1/rag/query', {
      query,
      top_k,
      doc_type,
      symbol,
    })
    return res.data
  },

  async evaluateSignal(params: {
    signal_id?: string
    symbol?: string
    direction?: string
    order_type?: string
    entry_price?: number
    stop_loss?: number
    take_profit_1?: number
    take_profit_2?: number
    take_profit_3?: number
    notes?: string
  }): Promise<SignalEvaluationResponse> {
    const res = await apiClient.post<SignalEvaluationResponse>('/api/v1/rag/evaluate', params)
    return res.data
  },

  async getKnowledgeBase(doc_type?: string): Promise<KnowledgeDoc[]> {
    const params = new URLSearchParams()
    if (doc_type) params.append('doc_type', doc_type)
    const res = await apiClient.get<KnowledgeDoc[]>(`/api/v1/rag/knowledge-base?${params.toString()}`)
    return res.data
  },

  async addKnowledgeDoc(data: {
    title: string
    doc_type: string
    text: string
    metadata?: Record<string, any>
  }): Promise<{ message: string; document_id: string }> {
    const res = await apiClient.post<{ message: string; document_id: string }>(
      '/api/v1/rag/knowledge-base',
      data
    )
    return res.data
  },

  async reindexRag(): Promise<{
    message: string
    signals_indexed: number
    total_documents: number
  }> {
    const res = await apiClient.post<{
      message: string
      signals_indexed: number
      total_documents: number
    }>('/api/v1/rag/reindex')
    return res.data
  },

  // ── Stock Market Hours ─────────────────────────────────────────────────────
  async getMarketHours(): Promise<import('../types').MarketHoursResponse> {
    const res = await apiClient.get<import('../types').MarketHoursResponse>('/api/v1/analytics/market-hours')
    return res.data
  },
}
