import request from './request'

export const getProfile = () => request.get('/api/user/profile')
export const updateProfile = (payload) => request.put('/api/user/profile', payload)
export const getFavorites = () => request.get('/api/user/favorites')
export const recordBehavior = (payload) => request.post('/api/user/behavior', payload)
