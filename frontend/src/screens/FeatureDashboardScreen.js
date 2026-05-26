import React, { useState, useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { listFeatureFlags } from '../actions/featureFlagActions'
import FeatureFlagListScreen from './FeatureFlagListScreen'
import AutoPilotControls from '../components/AutoPilotControls'

const FeatureDashboardScreen = (props) => {
  const dispatch = useDispatch()
  const [selectedFeatureId, setSelectedFeatureId] = useState('search_v2')

  const featureFlags = useSelector((state) => state.featureFlags)
  const { flags } = featureFlags

  const flagsList = flags ? Object.entries(flags).map(([id, f]) => ({ id, ...f })) : []

  const selectedFeature = flagsList.find((f) => f.id === selectedFeatureId) || {
    id: selectedFeatureId,
    name: selectedFeatureId,
    status: 'Unknown',
    traffic_percentage: 0,
  }

  const handleFeatureUpdate = (newState) => {
    if (newState) {
      dispatch(listFeatureFlags())
    }
  }

  return (
    <div className="feature-dashboard-page">
      <FeatureFlagListScreen {...props} />

      <div className="feature-dashboard-page__selector" aria-labelledby="ap-selector-title">
        <h2 className="feature-dashboard-page__subtitle" id="ap-selector-title">
          Auto-Pilot Controls
        </h2>
        <div className="feature-dashboard-page__field">
          <label className="feature-dashboard-page__label" htmlFor="ap-feature-select">
            Выберите фичу
          </label>
          <select
            id="ap-feature-select"
            className="feature-dashboard-page__select"
            value={selectedFeatureId}
            onChange={(e) => setSelectedFeatureId(e.target.value)}
          >
            {flagsList.map((f) => (
              <option key={f.id} value={f.id}>
                {f.name_ru || f.name || f.id} — {f.status}
              </option>
            ))}
          </select>
        </div>

        <AutoPilotControls
          feature={selectedFeature}
          onUpdate={handleFeatureUpdate}
        />
      </div>
    </div>
  )
}

export default FeatureDashboardScreen
