// ── Portfolio ──────────────────────────────────────────────────────────────

export interface Portfolio {
  id: string
  name: string
  currency: string
  initial_balance: number
  cash_balance: number
  total_equity: number
  realized_pnl: number
  unrealized_pnl: number
  daily_pnl: number
  max_drawdown: number
  peak_equity: number
  total_trades: number
  winning_trades: number
  losing_trades: number
  win_rate: number
  created_at: string
  updated_at: string
}

// ── Signal ─────────────────────────────────────────────────────────────────

export type SignalStatus = 'PENDING' | 'VALIDATED' | 'EXECUTED' | 'REJECTED' | 'EXPIRED'
export type SignalDirection = 'BUY' | 'SELL'

export interface Signal {
  id: string
  symbol: string
  exchange: string
  direction: SignalDirection
  order_type: string
  entry_price: number | null
  stop_loss: number | null
  take_profit_1: number | null
  take_profit_2: number | null
  take_profit_3: number | null
  risk_reward_ratio: number | null
  confidence_score: number | null
  status: SignalStatus
  validation_errors: string | null
  raw_text: string | null
  notes: string | null
  created_at: string
  updated_at: string
}

export interface SignalCreate {
  symbol: string
  direction: string
  order_type?: string
  entry_price?: number
  stop_loss?: number
  take_profit_1?: number
  take_profit_2?: number
  take_profit_3?: number
  notes?: string
}

// ── Position ───────────────────────────────────────────────────────────────

export type PositionStatus = 'OPEN' | 'CLOSED' | 'LIQUIDATED'
export type PositionDirection = 'LONG' | 'SHORT'

export interface Position {
  id: string
  symbol: string
  direction: PositionDirection
  status: PositionStatus
  entry_price: number
  exit_price: number | null
  quantity: number
  notional_value: number
  stop_loss: number | null
  take_profit_1: number | null
  take_profit_2: number | null
  take_profit_3: number | null
  unrealized_pnl: number
  realized_pnl: number
  fees_paid: number
  opened_at: string | null
  closed_at: string | null
  close_reason: string | null
  created_at: string
}

// ── Order ──────────────────────────────────────────────────────────────────

export interface Order {
  id: string
  symbol: string
  side: string
  order_type: string
  status: string
  execution_mode: 'PAPER'  // Always PAPER
  requested_quantity: number
  filled_quantity: number
  requested_price: number | null
  filled_price: number | null
  slippage_bps: number
  fee: number
  notes: string | null
  created_at: string
}

// ── Telegram Channel ───────────────────────────────────────────────────────

export interface TelegramChannel {
  id: string
  channel_id: string
  channel_username: string | null
  channel_title: string | null
  is_active: boolean
  is_monitored: boolean
  messages_received: number
  messages_processed: number
  messages_rejected: number
  signals_parsed: number
  last_message_at: string | null
  last_error: string | null
  created_at: string
}

export interface TelegramMessage {
  id: string
  channel_id: string
  message_id: number
  sender_name: string | null
  raw_text: string
  processed: boolean
  signal_parsed: boolean
  parse_error: string | null
  created_at: string
}

// ── Dashboard ──────────────────────────────────────────────────────────────

export interface EquitySnapshot {
  id: string
  timestamp: string
  equity: number
  cash: number
  unrealized_pnl: number
  realized_pnl: number
}

export interface DashboardStats {
  portfolio: Portfolio
  open_positions_count: number
  recent_signals: Signal[]
  recent_orders: Order[]
  equity_curve: EquitySnapshot[]
  telegram_connected: boolean
  market_data_connected: boolean
  is_paper_trading: boolean
}

// ── Analytics ──────────────────────────────────────────────────────────────

export interface PerformanceMetrics {
  win_rate: number
  total_trades: number
  winning_trades: number
  losing_trades: number
  realized_pnl: number
  unrealized_pnl: number
  max_drawdown: number
  initial_balance: number
  current_equity: number
  total_return_pct: number
}

// ── API ────────────────────────────────────────────────────────────────────

export interface ApiError {
  detail: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}

// ── RAG & AI Copilot ──────────────────────────────────────────────────────────

export interface RagSource {
  id: string
  title: string
  doc_type: string
  score: number
  match_type: string
  snippet: string
  metadata: Record<string, any>
}

export interface RagQueryResponse {
  query: string
  answer: string
  sources: RagSource[]
  provider_used: string
  metrics: {
    retrieval_time_ms: number
    generation_time_ms: number
    total_time_ms: number
    sources_retrieved: number
  }
}

export interface SimilarTrade {
  signal_id: string
  symbol: string
  direction: string
  entry_price: number | null
  stop_loss: number | null
  take_profit: number | null
  outcome: string
  realized_pnl: number | null
  realized_pnl_pct: number | null
  similarity_score: number
  channel_name: string
  created_at: string
  notes: string
}

export interface SignalEvaluationResponse {
  symbol: string
  direction: string
  recommended_action: 'EXECUTE' | 'CAUTION' | 'REJECT'
  confidence_score: number
  risk_score: number
  historical_win_rate_similar: number
  sample_size_similar: number
  evaluation_summary: string
  similar_trades: SimilarTrade[]
  matched_strategies: string[]
  actionable_advice: string[]
  provider_used: string
  timestamp: string
}

export interface RagStatus {
  provider: string
  gemini_configured: boolean
  openai_configured: boolean
  total_documents: number
  documents_by_type: Record<string, number>
}

export interface KnowledgeDoc {
  id: string
  title: string
  doc_type: string
  text: string
  metadata: Record<string, any>
  created_at: string
  has_embedding: boolean
}

// ── Stock Market Hours & Global Sessions ─────────────────────────────────────

export type MarketStatus = 'OPEN' | 'CLOSED' | 'PRE_MARKET' | 'AFTER_HOURS' | 'WEEKEND'

export interface ExchangeHours {
  id: string
  name: string
  short_name: string
  region: string
  flag: string
  timezone: string
  tz_label: string
  local_date: string
  local_time: string
  local_time_short: string
  status: MarketStatus
  status_label: string
  badge_variant: 'success' | 'danger' | 'warning' | 'purple' | 'secondary'
  is_open: boolean
  open_time: string
  close_time: string
  has_pre_market: boolean
  pre_market_open: string | null
  has_after_hours: boolean
  after_hours_close: string | null
  countdown: string
  countdown_label: string
  next_event_time: string
  progress_pct: number
  crypto_impact: string
}

export interface CryptoMarketInfo {
  status: string
  status_label: string
  active_sessions: string[]
  is_peak_volatility: boolean
  volatility_tag: string
  description: string
}

export interface MarketHoursResponse {
  current_utc: string
  current_date: string
  open_count: number
  total_exchanges: number
  crypto_market: CryptoMarketInfo
  exchanges: ExchangeHours[]
}

