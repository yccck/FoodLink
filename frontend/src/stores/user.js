import { defineStore } from 'pinia'
import { login } from '../api/auth'
import { getProfile as fetchProfileApi } from '../api/user'

const TOKEN_KEY = 'shiyuan_token'
const USER_KEY = 'shiyuan_user'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem(TOKEN_KEY) || '',
    user: JSON.parse(localStorage.getItem(USER_KEY) || 'null')
  }),
  getters: {
    isLoggedIn: (s) => !!s.token,
    role: (s) => (s.user ? s.user.role : null)
  },
  actions: {
    persist() {
      if (this.token) localStorage.setItem(TOKEN_KEY, this.token)
      else localStorage.removeItem(TOKEN_KEY)
      if (this.user) localStorage.setItem(USER_KEY, JSON.stringify(this.user))
      else localStorage.removeItem(USER_KEY)
    },
    setSession(token, user) {
      this.token = token
      this.user = user
      this.persist()
    },
    async login(payload) {
      const data = await login(payload)
      this.setSession(data.token, data.user)
      return data.user
    },
    async refreshProfile() {
      const data = await fetchProfileApi()
      this.user = data
      this.persist()
      return data
    },
    logout() {
      this.token = ''
      this.user = null
      this.persist()
      if (window.location.origin) window.location.href = '/login'
    }
  }
})