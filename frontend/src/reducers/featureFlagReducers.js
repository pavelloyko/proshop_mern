import {
  FEATURE_FLAGS_REQUEST,
  FEATURE_FLAGS_SUCCESS,
  FEATURE_FLAGS_FAIL,
} from '../constants/featureFlagConstants'

export const featureFlagsReducer = (
  state = { flags: {}, loading: false, error: null },
  action
) => {
  switch (action.type) {
    case FEATURE_FLAGS_REQUEST:
      return { ...state, loading: true }
    case FEATURE_FLAGS_SUCCESS:
      return { loading: false, flags: action.payload, error: null }
    case FEATURE_FLAGS_FAIL:
      return { loading: false, flags: {}, error: action.payload }
    default:
      return state
  }
}
