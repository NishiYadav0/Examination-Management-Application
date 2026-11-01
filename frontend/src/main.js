import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'
import plugins from './utils/plugins'

import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap-icons/font/bootstrap-icons.css'
import * as bootstrap from 'bootstrap'
import './assets/main.css'

window.bootstrap = bootstrap

// Session expired / blocked -> back to login
window.addEventListener('emp:unauthorized', () => {
  if (store.getters['auth/isLoggedIn']) {
    store.commit('auth/clear')
    store.dispatch('ui/toast', { message: 'Your session ended. Please log in again.', type: 'warning' })
    router.push({ path: '/login', query: { redirect: router.currentRoute.value.fullPath } })
  }
})

// "Add to desktop" – register the service worker (production build / localhost)
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => navigator.serviceWorker.register('/sw.js').catch(() => {}))
}

createApp(App).use(store).use(router).use(plugins).mount('#app')

// Keep the browser's install prompt so we can show our own "Install app" button
window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault()
  window.__empInstallPrompt = e
  window.dispatchEvent(new Event('emp:installable'))
})
