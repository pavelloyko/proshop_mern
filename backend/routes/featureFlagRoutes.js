import express from 'express'
const router = express.Router()
import {
  getFeatureFlags,
  getFeatureFlagDescriptions,
  getFeatureFlagByName,
  setFeatureState,
  adjustTrafficRollout,
} from '../controllers/featureFlagController.js'
import { protect, admin } from '../middleware/authMiddleware.js'

router.route('/').get(getFeatureFlags)
router.route('/descriptions').get(getFeatureFlagDescriptions)
router.route('/:name').get(getFeatureFlagByName)
router.route('/:name/state').post(protect, admin, setFeatureState)
router.route('/:name/traffic').post(protect, admin, adjustTrafficRollout)

export default router
