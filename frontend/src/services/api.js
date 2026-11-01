// Central Axios instance – every request goes to Flask through the /api proxy
import axios from 'axios'

const api = axios.create({ baseURL: process.env.VUE_APP_API_URL || '/api', timeout: 20000 })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('emp-token')
  if (token) config.headers['Authentication-Token'] = token
  return config
})

api.interceptors.response.use(
  (res) => res,
  (error) => {
    const res = error.response
    if (!res) {
      error.userMessage = 'Cannot reach the server. Is the Flask API running on port 5000?'
    } else {
      error.userMessage = (res.data && res.data.message) || `Request failed (${res.status})`
      error.fieldErrors = (res.data && res.data.errors) || {}
      if (res.status === 401 && !error.config.url.includes('/auth/login')) {
        window.dispatchEvent(new CustomEvent('emp:unauthorized', { detail: error.userMessage }))
      }
    }
    return Promise.reject(error)
  }
)

export default api
