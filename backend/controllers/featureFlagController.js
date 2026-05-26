import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'
import asyncHandler from 'express-async-handler'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
const FLAGS_PATH = path.join(__dirname, '..', 'features.json')
const DESCS_PATH = path.join(__dirname, '..', 'feature-descriptions.json')

// @desc    Get all feature flags (enriched with Russian descriptions)
// @route   GET /api/feature-flags
// @access  Public
const getFeatureFlags = asyncHandler(async (req, res) => {
  const raw = fs.readFileSync(FLAGS_PATH, 'utf-8')
  const flags = JSON.parse(raw)

  const descRaw = fs.readFileSync(DESCS_PATH, 'utf-8')
  const descriptions = JSON.parse(descRaw)

  const enriched = {}
  for (const [id, flag] of Object.entries(flags)) {
    enriched[id] = {
      ...flag,
      ...(descriptions[id] || {}),
    }
  }

  res.json(enriched)
})

// @desc    Get feature flag descriptions (Russian)
// @route   GET /api/feature-flags/descriptions
// @access  Public
const getFeatureFlagDescriptions = asyncHandler(async (req, res) => {
  const descRaw = fs.readFileSync(DESCS_PATH, 'utf-8')
  const descriptions = JSON.parse(descRaw)
  res.json(descriptions)
})

// @desc    Get a single feature flag by name
// @route   GET /api/feature-flags/:name
// @access  Public
const getFeatureFlagByName = asyncHandler(async (req, res) => {
  const raw = fs.readFileSync(FLAGS_PATH, 'utf-8')
  const flags = JSON.parse(raw)
  const flag = flags[req.params.name]

  if (!flag) {
    res.status(404)
    throw new Error(`Feature flag "${req.params.name}" not found`)
  }

  const descRaw = fs.readFileSync(DESCS_PATH, 'utf-8')
  const descriptions = JSON.parse(descRaw)

  res.json({
    [req.params.name]: {
      ...flag,
      ...(descriptions[req.params.name] || {}),
    },
  })
})

// @desc    Set feature flag state
// @route   POST /api/feature-flags/:name/state
// @access  Private/Admin
const setFeatureState = asyncHandler(async (req, res) => {
  const { state } = req.body
  const validStates = ['Enabled', 'Disabled', 'Testing']

  if (!validStates.includes(state)) {
    res.status(400)
    throw new Error(`Invalid state "${state}". Must be: ${validStates.join(', ')}`)
  }

  const raw = fs.readFileSync(FLAGS_PATH, 'utf-8')
  const flags = JSON.parse(raw)
  const name = req.params.name

  if (!flags[name]) {
    res.status(404)
    throw new Error(`Feature flag "${name}" not found`)
  }

  flags[name].status = state
  if (state === 'Disabled') flags[name].traffic_percentage = 0
  if (state === 'Enabled') flags[name].traffic_percentage = 100
  flags[name].last_modified = new Date().toISOString()

  fs.writeFileSync(FLAGS_PATH, JSON.stringify(flags, null, 2), 'utf-8')

  const descRaw = fs.readFileSync(DESCS_PATH, 'utf-8')
  const descriptions = JSON.parse(descRaw)

  res.json({
    success: true,
    message: `Feature "${name}" set to ${state}`,
    [name]: { ...flags[name], ...(descriptions[name] || {}) },
  })
})

// @desc    Adjust traffic rollout percentage
// @route   POST /api/feature-flags/:name/traffic
// @access  Private/Admin
const adjustTrafficRollout = asyncHandler(async (req, res) => {
  const { percentage } = req.body

  if (typeof percentage !== 'number' || percentage < 0 || percentage > 100) {
    res.status(400)
    throw new Error(`Invalid percentage "${percentage}". Must be 0-100.`)
  }

  const raw = fs.readFileSync(FLAGS_PATH, 'utf-8')
  const flags = JSON.parse(raw)
  const name = req.params.name

  if (!flags[name]) {
    res.status(404)
    throw new Error(`Feature flag "${name}" not found`)
  }

  if (flags[name].status !== 'Testing') {
    res.status(400)
    throw new Error(`Feature "${name}" must be in Testing state to adjust traffic. Current: ${flags[name].status}`)
  }

  flags[name].traffic_percentage = percentage
  flags[name].last_modified = new Date().toISOString()

  fs.writeFileSync(FLAGS_PATH, JSON.stringify(flags, null, 2), 'utf-8')

  const descRaw = fs.readFileSync(DESCS_PATH, 'utf-8')
  const descriptions = JSON.parse(descRaw)

  res.json({
    success: true,
    message: `Traffic for "${name}" set to ${percentage}%`,
    [name]: { ...flags[name], ...(descriptions[name] || {}) },
  })
})

export { getFeatureFlags, getFeatureFlagDescriptions, getFeatureFlagByName, setFeatureState, adjustTrafficRollout }
