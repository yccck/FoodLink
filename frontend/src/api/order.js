import request from './request'

export const createOrder = (payload) => request.post('/api/orders', payload)
export const getOrders = (params) => request.get('/api/orders', { params })