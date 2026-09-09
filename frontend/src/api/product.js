import request from './request'

export const getProduct = (id) => request.get(`/api/products/${id}`)
export const setFavorite = (id, favorite) => request.post(`/api/products/${id}/favorite`, { favorite })