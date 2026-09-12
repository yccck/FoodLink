import { onBeforeUnmount, onMounted, ref } from 'vue'

export function parseApiTime(value) {
  if (!value) return NaN
  if (value instanceof Date) return value.getTime()
  const normalized = String(value).trim().replace(' ', 'T')
  const timestamp = new Date(normalized).getTime()
  return Number.isFinite(timestamp) ? timestamp : NaN
}

export function pickupDeadlineMs(order) {
  const explicit = parseApiTime(order?.pickup_deadline)
  if (Number.isFinite(explicit)) return explicit
  return NaN
}

export function useOrderCountdown() {
  const now = ref(Date.now())
  let timer = null

  onMounted(() => {
    timer = window.setInterval(() => { now.value = Date.now() }, 1000)
  })
  onBeforeUnmount(() => {
    if (timer !== null) window.clearInterval(timer)
  })

  function remainingSeconds(order) {
    if (!order || Number(order.status) !== 0) return 0
    const deadline = pickupDeadlineMs(order)
    if (!Number.isFinite(deadline)) return Math.max(0, Number(order.remaining_seconds) || 0)
    return Math.max(0, Math.ceil((deadline - now.value) / 1000))
  }

  function countdownText(order) {
    const total = remainingSeconds(order)
    const hours = Math.floor(total / 3600)
    const minutes = Math.floor((total % 3600) / 60)
    const seconds = total % 60
    return [hours, minutes, seconds].map(value => String(value).padStart(2, '0')).join(':')
  }

  return { now, remainingSeconds, countdownText }
}

export function orderTotal(order) {
  const total = Number(order?.total_amount)
  if (Number.isFinite(total)) return total.toFixed(2)
  const unitPrice = Number(order?.price)
  const quantity = Number(order?.quantity || 1)
  return (Number.isFinite(unitPrice) ? unitPrice * quantity : 0).toFixed(2)
}

export function completionText(order) {
  return order?.completion_type === 'auto_timeout' ? '超时自动结算' : '取货完成'
}
