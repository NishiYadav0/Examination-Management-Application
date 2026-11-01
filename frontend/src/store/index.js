// Vuex store – auth, UI (toasts / confirm / theme) and notifications
import { createStore } from 'vuex'
import api from '@/services/api'

let toastId = 0

const auth = {
  namespaced: true,
  state: () => ({
    token: localStorage.getItem('emp-token') || null,
    user: JSON.parse(localStorage.getItem('emp-user') || 'null')
  }),
  getters: {
    isLoggedIn: (s) => !!s.token && !!s.user,
    role: (s) => (s.user ? s.user.role : null),
    home: (s) => (s.user ? `/${s.user.role}` : '/login')
  },
  mutations: {
    setAuth (s, { token, user }) {
      s.token = token; s.user = user
      localStorage.setItem('emp-token', token)
      localStorage.setItem('emp-user', JSON.stringify(user))
    },
    setUser (s, user) { s.user = user; localStorage.setItem('emp-user', JSON.stringify(user)) },
    clear (s) {
      s.token = null; s.user = null
      localStorage.removeItem('emp-token'); localStorage.removeItem('emp-user')
    }
  },
  actions: {
    async login ({ commit }, payload) {
      const { data } = await api.post('/auth/login', payload)
      commit('setAuth', data.data)
      return data.data.user
    },
    async register ({ commit }, payload) {
      const { data } = await api.post('/auth/register', payload)
      commit('setAuth', data.data)
      return data.data.user
    },
    async fetchMe ({ commit, state }) {
      if (!state.token) return null
      const { data } = await api.get('/auth/me')
      commit('setUser', data.data)
      return data.data
    },
    async logout ({ commit }) {
      try { await api.post('/auth/logout') } catch (e) { /* token may already be invalid */ }
      commit('clear')
    }
  }
}

const ui = {
  namespaced: true,
  state: () => ({
    toasts: [],
    confirm: null,
    theme: document.documentElement.getAttribute('data-bs-theme') || 'light',
    sidebarOpen: false
  }),
  mutations: {
    addToast (s, t) { s.toasts.push(t) },
    removeToast (s, id) { s.toasts = s.toasts.filter((t) => t.id !== id) },
    setConfirm (s, c) { s.confirm = c },
    setTheme (s, theme) {
      s.theme = theme
      document.documentElement.setAttribute('data-bs-theme', theme)
      try { localStorage.setItem('emp-theme', theme) } catch (e) { /* ignore */ }
    },
    setSidebar (s, v) { s.sidebarOpen = v }
  },
  actions: {
    toast ({ commit }, { message, type = 'success', title = null, timeout = 4000 }) {
      const id = ++toastId
      commit('addToast', { id, message, type, title })
      setTimeout(() => commit('removeToast', id), timeout)
    },
    confirm ({ commit }, opts) {
      return new Promise((resolve) => {
        commit('setConfirm', { ...opts, resolve: (v) => { commit('setConfirm', null); resolve(v) } })
      })
    }
  }
}

const notif = {
  namespaced: true,
  state: () => ({ items: [], unread: 0 }),
  mutations: { set (s, d) { s.items = d.items; s.unread = d.unread } },
  actions: {
    async load ({ commit, rootGetters }) {
      if (!rootGetters['auth/isLoggedIn']) return
      try { const { data } = await api.get('/notifications'); commit('set', data.data) } catch (e) { /* silent */ }
    },
    async readAll ({ dispatch }) { await api.post('/notifications/read-all'); dispatch('load') },
    async read ({ dispatch }, id) { await api.post(`/notifications/${id}/read`); dispatch('load') }
  }
}

export default createStore({ modules: { auth, ui, notif } })
