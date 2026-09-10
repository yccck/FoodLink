import request from './request'

export const createOrder = (payload) => request.post('/api/orders', payload)
export const getOrders = (params) => request.get('/api/orders', { params })
export const getOrderSummary = () => request.get('/api/orders/summary')
export const pickupOrder = (id) => request.put(`/api/orders/${id}/pickup`)
export const verifyOrder = (pickup_code) => request.post('/api/orders/verify', { pickup_code })
