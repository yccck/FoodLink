import axios from 'axios'
import { handleMockRequest } from '../../mock/vite-mock.js'
import { toast } from '../utils/toast'

const USE_BROWSER_MOCK = import.meta.env.VITE_BROWSER_MOCK === 'true'

const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '',
  timeout: 10000
})

// ---- 浏览器端内嵌 Mock（GitHub Pages 纯静态演示用） ----
// 当 VITE_BROWSER_MOCK=true 时，所有 /api 请求改走本地内存 mock，无需后端。
async function browserMockAdapter(config) {
  try {
    const url = config.url || '/'
    const [p, q1] = url.split('?')
    const path = p || '/'
    const qs = (q1 !== undefined) ? q1 : new URLSearchParams(config.params || {}).toString()
    let body
    if (config.data != null) {
      try { body = typeof config.data === 'string' ? JSON.parse(config.data) : config.data }
      catch { body = {} }
    }
    let raw = {}
    const h = config.headers
    if (h && typeof h.toJSON === 'function') raw = h.toJSON()
    else if (h) raw = { ...h }
    const headers = {}
    for (const k in raw) headers[k] = raw[k]
    const out = await handleMockRequest({ method: (config.method || 'get').toUpperCase(), path, query: qs, headers, body })
    return { data: out.payload, status: (out && out.status) || 200, statusText: 'OK', headers: {}, config, request: {} }
  } catch (err) {
    return { data: { code: 500, message: '本地演示服务异常', data: null }, status: 200, statusText: 'OK', headers: {}, config, request: {} }
  }
}
if (USE_BROWSER_MOCK) service.defaults.adapter = browserMockAdapter

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
      if (window.location.hash !== '#/login') window.location.hash = '#/login'
    } else {
      toast(msg, 'error')
    }
    return Promise.reject(error)
  }
)

export default service
