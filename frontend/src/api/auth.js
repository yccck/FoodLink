import request from './request'

export const login = (payload) => request.post('/api/auth/login', payload)
export const register = (payload) => request.post('/api/auth/register', payload)
export const resetPassword = (payload) => request.post('/api/auth/reset-password', payload)
export const getProfile = () => request.get('/api/user/profile')
export const updateProfile = (payload) => request.put('/api/user/profile', payload)