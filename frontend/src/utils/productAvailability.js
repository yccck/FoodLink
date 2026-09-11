export function productExpiryTime(value) {
  if (!value) return NaN
  return new Date(String(value).replace(' ', 'T')).getTime()
}

export function isProductExpired(product, now = Date.now()) {
  const expiryTime = productExpiryTime(product?.expire_time)
  return Number.isFinite(expiryTime) && expiryTime <= now
}
