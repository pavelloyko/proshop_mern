const proxy = require('http-proxy-middleware')

const target = process.env.REACT_APP_API_URL || 'http://127.0.0.1:5001'

const opts = {
  target,
  changeOrigin: true,
  // n8n AI Agent calls can take 30-60s — default CRA proxy timeout is too short
  proxyTimeout: 120000,
  timeout: 120000,
}

module.exports = function (app) {
  app.use('/api', proxy(opts))
  app.use('/uploads', proxy(opts))
}
