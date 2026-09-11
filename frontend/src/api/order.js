import request from './request'

export const createOrder = (payload) => request.post('/api/orders', payload)
export const getOrders = (params) => request.get('/api/orders', { params })
export const getOrderSummary = () => request.get('/api/orders/summary')
export const rechargeWallet = (payload) => request.post('/api/orders/wallet/recharge', payload)
export const withdrawWallet = (payload) => request.post('/api/orders/wallet/withdraw', payload)
export const pickupOrder = (id) => request.put(`/api/orders/${id}/pickup`)
export const verifyOrder = (pickup_code) => request.post('/api/orders/verify', { pickup_code })
