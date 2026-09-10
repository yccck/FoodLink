import request from './request'

export const getPendingMerchants = () => request.get('/api/admin/merchants/pending')
export const auditMerchant = (id, audit_status, reason) => request.put(`/api/admin/merchants/${id}/audit`, { audit_status, reason })
export const getRiskLogs = (params) => request.get('/api/admin/risk-logs', { params })
export const resolveRiskLog = (id, restore = true) => request.put(`/api/admin/risk-logs/${id}/resolve`, { restore })
export const getStatistics = () => request.get('/api/admin/statistics')