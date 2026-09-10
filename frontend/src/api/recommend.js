import request from './request'

export const getRecommend = (params) => request.get('/api/products/recommend', { params })
export const getGuessYouLike = (params) => request.get('/api/products/guess-you-like', { params })