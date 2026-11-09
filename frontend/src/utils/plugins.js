// Global helpers: this.$toast(...), this.$confirm(...), this.$f (formatters)
import store from '@/store'
import * as f from '@/utils/format'

export default {
  install (app) {
    app.config.globalProperties.$toast = (message, type = 'success', title = null) =>
      store.dispatch('ui/toast', { message, type, title })
    app.config.globalProperties.$error = (err, fallback = 'Something went wrong') =>
      store.dispatch('ui/toast', { message: (err && err.userMessage) || fallback, type: 'danger', timeout: 6000 })
    app.config.globalProperties.$confirm = (opts) =>
      store.dispatch('ui/confirm', typeof opts === 'string' ? { message: opts } : opts)
    app.config.globalProperties.$f = f
  }
}
