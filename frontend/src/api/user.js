import request from './request'

export const getProfile = () => request.get('/api/user/profile')
export const updateProfile = (payload) => request.put('/api/user/profile', payload)
export const getFavorites = () => request.get('/api/user/favorites')
export const recordBehavior = (payload) => request.post('/api/user/behavior', payload)
export const getSubsidyNotices = () => request.get('/api/user/subsidy/notices')
export const readSubsidyNotice = (id) => request.put(`/api/user/subsidy/notices/${id}/read`)
