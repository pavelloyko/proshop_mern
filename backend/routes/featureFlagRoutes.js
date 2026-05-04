import express from 'express'
const router = express.Router()
import {
  getFeatureFlags,
  getFeatureFlagDescriptions,
  getFeatureFlagByName,
} from '../controllers/featureFlagController.js'

router.route('/').get(getFeatureFlags)
router.route('/descriptions').get(getFeatureFlagDescriptions)
router.route('/:name').get(getFeatureFlagByName)

export default router
