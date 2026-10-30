// Vue CLI configuration
const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
  transpileDependencies: true,
  lintOnSave: false,
  // Polling makes hot-reload work on WSL / mounted Windows drives (/mnt/c, /mnt/d)
  configureWebpack: {
    watchOptions: { poll: 1000, ignored: /node_modules/ },
    performance: { hints: false }
  },
  devServer: {
    port: 8080,
    // All /api calls are proxied to Flask -> no CORS problems in development
    proxy: {
      '/api': { target: 'http://127.0.0.1:5000', changeOrigin: true }
    },
    client: { overlay: { warnings: false, errors: true } }
  }
})
