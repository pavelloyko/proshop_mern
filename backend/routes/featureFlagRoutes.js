import express from 'express'
const router = express.Router()
import {
  getFeatureFlags,
  getFeatureFlagDescriptions,
  getFeatureFlagByName,
  setFeatureState,
  adjustTrafficRollout,
} from '../controllers/featureFlagController.js'

router.route('/').get(getFeatureFlags)
router.route('/descriptions').get(getFeatureFlagDescriptions)
router.route('/:name').get(getFeatureFlagByName)
router.route('/:name/state').post(setFeatureState)
router.route('/:name/traffic').post(adjustTrafficRollout)

export default router
