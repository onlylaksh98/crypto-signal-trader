// Backend returns Decimal/numeric fields as strings from SQLAlchemy/SQLite.
// All numeric helpers coerce inputs via Number() to safely handle both string and number.

type Numeric = number | string | null | undefined

function toNum(v: Numeric): number {
  if (v === null || v === undefined || v === '') return NaN
  return Number(v)
}

export function formatUSD(value: Numeric, minDecimals = 2, maxDecimals = 2): string {
  const n = toNum(value)
  if (isNaN(n)) return '$0.00'
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: minDecimals,
    maximumFractionDigits: maxDecimals,
  }).format(n)
}

export function formatCryptoPrice(price: Numeric): string {
  const n = toNum(price)
  if (isNaN(n)) return '—'
  if (n < 0.0001) return `$${n.toFixed(8)}`
  if (n < 1) return `$${n.toFixed(4)}`
  if (n < 100) return `$${n.toFixed(3)}`
  return formatUSD(n, 2, 2)
}

export function formatPercent(value: Numeric, includeSign = true): string {
  const n = toNum(value)
  if (isNaN(n)) return '0.00%'
  return `${n >= 0 && includeSign ? '+' : ''}${n.toFixed(2)}%`
}

export function formatNumber(value: Numeric, decimals = 2): string {
  const n = toNum(value)
  if (isNaN(n)) return '0'
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(n)
}

export function formatQuantity(value: Numeric, decimals = 4): string {
  const n = toNum(value)
  if (isNaN(n)) return '0'
  return n.toFixed(decimals)
}

export function formatDate(dateString: string | null | undefined): string {
  if (!dateString) return '—'
  try {
    const date = new Date(dateString)
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    }).format(date)
  } catch {
    return dateString
  }
}

export function formatShortDate(dateString: string | null | undefined): string {
  if (!dateString) return '—'
  try {
    const date = new Date(dateString)
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    }).format(date)
  } catch {
    return dateString
  }
}

export function truncateId(id: string | null | undefined, length = 8): string {
  if (!id) return ''
  return id.length > length ? `${id.slice(0, length)}...` : id
}

