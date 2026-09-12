import request from './request'

export const getMyProducts = () => request.get('/api/products/mine')
export const publishProduct = (payload) => request.post('/api/products', payload)
export const toggleOffline = (id) => request.put(`/api/products/${id}/offline`)

export const getMerchantProfile = () => request.get('/api/merchant/profile')
export const updateMerchantProfile = (payload) => request.put('/api/merchant/profile', payload)
