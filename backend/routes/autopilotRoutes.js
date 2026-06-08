import express from 'express'
import https from 'https'
import http from 'http'
import asyncHandler from 'express-async-handler'
import { protect, admin } from '../middleware/authMiddleware.js'

const router = express.Router()

function nodeFetch(url, options = {}) {
  return new Promise((resolve, reject) => {
    const parsed = new URL(url)
    const mod = parsed.protocol === 'https:' ? https : http

    const reqOpts = {
      hostname: parsed.hostname,
      port: parsed.port,
      path: parsed.pathname + parsed.search,
      method: options.method || 'GET',
      headers: options.headers || {},
      timeout: options.timeout || 110000,
    }

    const req = mod.request(reqOpts, (res) => {
      let body = ''
      res.on('data', (chunk) => (body += chunk))
      res.on('end', () => {
        res.text = body
        res.ok = res.statusCode >= 200 && res.statusCode < 300
        res.json = () => JSON.parse(body)
        resolve(res)
      })
    })

    req.on('error', reject)
    req.on('timeout', () => {
      req.destroy()
      reject(new Error('Request timeout'))
    })

    if (options.body) {
      req.write(options.body)
    }
    req.end()
  })
}

// @desc    Proxy autopilot requests to n8n AI Agent workflow
// @route   POST /api/autopilot/feature-control
// @access  Private (should be admin in production)
router.post(
  '/feature-control',
  protect,
  admin,
  asyncHandler(async (req, res) => {
    const base = process.env.N8N_WEBHOOK_URL
    const apiKey = process.env.N8N_API_KEY

    if (!base) {
      res.status(500)
      throw new Error('N8N_WEBHOOK_URL is not configured on the server')
    }

    const target = `${base.replace(/\/+$/, '')}/feature-control`

    let upstream
    try {
      upstream = await nodeFetch(target, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(apiKey ? { 'X-API-Key': apiKey } : {}),
        },
        body: JSON.stringify(req.body || {}),
        timeout: 110000,
      })
    } catch (e) {
      const status = e.message === 'Request timeout' ? 504 : 502
      res.status(status).json({
        success: false,
        message: `Upstream error: ${e.message}`,
      })
      return
    }

    const text = upstream.text
    let payload
    try {
      payload = text ? JSON.parse(text) : {}
    } catch (_) {
      payload = {
        success: upstream.ok,
        message: text || `HTTP ${upstream.statusCode}`,
      }
    }

    res.status(upstream.statusCode).json(payload)
  })
)

export default router
