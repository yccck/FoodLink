import axios from 'axios'
import { toast } from '../utils/toast'

const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '',
  timeout: 10000
})

// 请求拦截器：统一附加 Token
service.interceptors.request.use((config) => {
  const token = localStorage.getItem('shiyuan_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// 响应拦截器：解包统一封装 {code,message,data}，处理业务错误与 401
service.interceptors.response.use(
  (response) => {
    const res = response.data
    if (res && res.code === 0) return res.data
    const msg = (res && res.message) || '请求失败'
    toast(msg, 'error')
    return Promise.reject(new Error(msg))
  },
  (error) => {
    const status = error.response && error.response.status
    const msg = (error.response && error.response.data && error.response.data.message) || error.message || '网络异常'
    if (status === 401) {
      localStorage.removeItem('shiyuan_token')
      localStorage.removeItem('shiyuan_user')
      toast(msg, 'error')
      if (window.location.pathname !== '/login') window.location.href = '/login'
    } else {
      toast(msg, 'error')
    }
    return Promise.reject(error)
  }
)

export default service