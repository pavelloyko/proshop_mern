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

export { getFeatureFlags, getFeatureFlagDescriptions, getFeatureFlagByName }
