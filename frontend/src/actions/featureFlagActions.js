import axios from 'axios'
import {
  FEATURE_FLAGS_REQUEST,
  FEATURE_FLAGS_SUCCESS,
  FEATURE_FLAGS_FAIL,
} from '../constants/featureFlagConstants'

export const listFeatureFlags = () => async (dispatch) => {
  try {
    dispatch({ type: FEATURE_FLAGS_REQUEST })

    const { data } = await axios.get('/api/feature-flags')

    dispatch({
      type: FEATURE_FLAGS_SUCCESS,
      payload: data,
    })
  } catch (error) {
    dispatch({
      type: FEATURE_FLAGS_FAIL,
      payload:
        error.response && error.response.data.message
          ? error.response.data.message
          : error.message,
    })
  }
}
