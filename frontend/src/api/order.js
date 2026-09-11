import request from './request'

export const createOrder = (payload) => request.post('/api/orders', payload)
export const getOrders = (params) => request.get('/api/orders', { params })
export const getOrderSummary = () => request.get('/api/orders/summary')
export const refundOrder = (id) => request.put(`/api/orders/${id}/refund`)
export const getRefundRequests = () => request.get('/api/orders/refund-requests')
export const createRefundRequest = (id, payload) => request.post(`/api/orders/${id}/refund-request`, payload)
export const pickupOrder = (id) => request.put(`/api/orders/${id}/pickup`)
export const verifyOrder = (pickup_code) => request.post('/api/orders/verify', { pickup_code })
