import React, { useEffect, useState, useMemo, useCallback, useRef } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import Message from '../components/Message'
import AutoPilotControls from '../components/AutoPilotControls'
import { listFeatureFlags } from '../actions/featureFlagActions'

// Map frontend action names to WF1 action names
const ACTION_MAP = {
  enable: 'enable',
  testing: 'test',
  disable: 'rollback',
  traffic: 'rollout',
}

const STATUS_OPTIONS = ['All', 'Enabled', 'Testing', 'Disabled']

const STATUS_ICONS = {
  Enabled: '✓',
  Testing: '▶',
  Disabled: '○',
}

const statusBadgeClass = (status) => {
  switch (status) {
    case 'Enabled': return 'feature-badge feature-badge--enabled'
    case 'Testing': return 'feature-badge feature-badge--testing'
    case 'Disabled': return 'feature-badge feature-badge--disabled'
    default: return 'feature-badge'
  }
}

const SkeletonRows = () => (
  <div className="feature-skeleton" aria-busy="true" aria-label="Loading features">
    {[...Array(6)].map((_, i) => (
      <div className="feature-skeleton__row" key={i}>
        <div className="feature-skeleton__bar" style={{ width: '12%', marginRight: 16 }} />
        <div className="feature-skeleton__bar" style={{ width: '24%', marginRight: 16 }} />
        <div className="feature-skeleton__bar" style={{ width: '10%', marginRight: 16 }} />
        <div className="feature-skeleton__bar" style={{ width: '20%', marginRight: 16 }} />
        <div className="feature-skeleton__bar" style={{ width: '10%' }} />
      </div>
    ))}
  </div>
)

const EmptyState = ({ hasFilters, onReset }) => (
  <div className="feature-empty" role="status">
    <div className="feature-empty__icon" aria-hidden="true">{'≡'}</div>
    <div className="feature-empty__title">
      {hasFilters ? 'No features match your filter' : 'No features found'}
    </div>
    <div className="feature-empty__desc">
      {hasFilters
        ? 'Try adjusting your search or filter criteria.'
        : 'Feature flags have not been configured yet.'}
    </div>
    {hasFilters && (
      <button
        className="btn btn-primary"
        onClick={onReset}
        aria-label="Reset all filters"
      >
        Reset Filters
      </button>
    )}
  </div>
)

const Toast = ({ message, type, onClose }) => {
  useEffect(() => {
    const timer = setTimeout(onClose, 4000)
    return () => clearTimeout(timer)
  }, [onClose])

  if (!message) return null

  return (
    <div className={`feature-toast feature-toast--${type}`} role="alert">
      <span className="feature-toast__icon">
        {type === 'success' ? '✓' : type === 'error' ? '✗' : 'ℹ'}
      </span>
      <span className="feature-toast__msg">{message}</span>
      <button className="feature-toast__close" onClick={onClose} aria-label="Close">
        {'×'}
      </button>
    </div>
  )
}

const ActionButtons = ({ featureId, status, onAction, loading }) => (
  <div className="feature-actions">
    {status !== 'Enabled' && (
      <button
        className="feature-action-btn feature-action-btn--enable"
        onClick={() => onAction(featureId, 'enable')}
        disabled={loading}
        title="Enable feature"
      >
        Enable
      </button>
    )}
    {status !== 'Testing' && (
      <button
        className="feature-action-btn feature-action-btn--testing"
        onClick={() => onAction(featureId, 'testing')}
        disabled={loading}
        title="Set to Testing"
      >
        Testing
      </button>
    )}
    {status !== 'Disabled' && (
      <button
        className="feature-action-btn feature-action-btn--disable"
        onClick={() => onAction(featureId, 'disable')}
        disabled={loading}
        title="Disable feature"
      >
        Disable
      </button>
    )}
  </div>
)

const TrafficControl = ({ featureId, percentage, status, onApply, loading }) => {
  const [value, setValue] = useState(percentage)

  useEffect(() => {
    setValue(percentage)
  }, [percentage])

  const canApply = status === 'Testing' && value !== percentage

  return (
    <div className="feature-traffic">
      <div className="feature-slider">
        <input
          type="range"
          min="0"
          max="100"
          value={value}
          onChange={(e) => setValue(Number(e.target.value))}
          style={{ backgroundSize: `${value}% 100%` }}
          aria-label={`Traffic percentage`}
          aria-valuenow={value}
          aria-valuemin="0"
          aria-valuemax="100"
          disabled={status !== 'Testing'}
        />
        <span className="feature-slider__value">{value}%</span>
      </div>
      {canApply && (
        <button
          className="feature-action-btn feature-action-btn--apply"
          onClick={() => onApply(featureId, value)}
          disabled={loading}
        >
          Apply
        </button>
      )}
      {status !== 'Testing' && (
        <span className="feature-traffic__hint">Set to Testing first</span>
      )}
    </div>
  )
}

const FeatureRow = ({
  id,
  flag,
  onAction,
  onTrafficApply,
  onSelectAutoPilot,
  isSelected,
  flashId,
  loading,
}) => {
  const isFlashing = flashId === id
  return (
    <tr className={isFlashing ? 'feature-row--success' : ''}>
      <td>
        <span className="feature-dashboard__id">{id}</span>
      </td>
      <td>
        <span className="feature-dashboard__name">{flag.name_ru || flag.name}</span>
      </td>
      <td>
        <span className={statusBadgeClass(flag.status)}>
          <span className="feature-badge__icon" aria-hidden="true">{STATUS_ICONS[flag.status]}</span>
          {flag.status}
        </span>
      </td>
      <td>
        <TrafficControl
          featureId={id}
          percentage={flag.traffic_percentage}
          status={flag.status}
          onApply={onTrafficApply}
          loading={loading}
        />
      </td>
      <td>
        <ActionButtons
          featureId={id}
          status={flag.status}
          onAction={onAction}
          loading={loading}
        />
      </td>
      <td>
        <button
          className={`feature-action-btn feature-action-btn--autopilot${isSelected ? ' is-active' : ''}`}
          onClick={() => onSelectAutoPilot(id)}
          disabled={loading}
          aria-pressed={!!isSelected}
          title="Open AI Agent control panel"
        >
          {isSelected ? 'Auto-Pilot ✓' : '🤖 Auto-Pilot'}
        </button>
      </td>
      <td>{flag.last_modified}</td>
    </tr>
  )
}

const FeatureFlagListScreen = ({ history }) => {
  const dispatch = useDispatch()

  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('All')
  const [localFlags, setLocalFlags] = useState({})
  const [flashId, setFlashId] = useState(null)
  const [toast, setToast] = useState({ message: '', type: 'info' })
  const [actionLoading, setActionLoading] = useState(null)
  const [selectedAutoPilot, setSelectedAutoPilot] = useState(null)
  const flashTimer = useRef(null)
  const pollingRef = useRef(null)

  const featureFlags = useSelector((state) => state.featureFlags)
  const { loading, error, flags } = featureFlags

  const userLogin = useSelector((state) => state.userLogin)
  const { userInfo } = userLogin

  useEffect(() => {
    if (userInfo && userInfo.isAdmin) {
      dispatch(listFeatureFlags())
    } else {
      history.push('/login')
    }
  }, [dispatch, history, userInfo])

  useEffect(() => {
    if (flags && Object.keys(flags).length > 0) {
      setLocalFlags(JSON.parse(JSON.stringify(flags)))
    }
  }, [flags])

  useEffect(() => {
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current)
    }
  }, [])

  const filteredFlags = useMemo(() => {
    return Object.entries(localFlags).filter(([id, flag]) => {
      const name = (flag.name_ru || flag.name || '').toLowerCase()
      const matchesSearch =
        name.includes(searchTerm.toLowerCase()) ||
        id.toLowerCase().includes(searchTerm.toLowerCase())
      const matchesStatus =
        statusFilter === 'All' || flag.status === statusFilter
      return matchesSearch && matchesStatus
    })
  }, [localFlags, searchTerm, statusFilter])

  const triggerFlash = useCallback((id) => {
    if (flashTimer.current) clearTimeout(flashTimer.current)
    setFlashId(id)
    flashTimer.current = setTimeout(() => setFlashId(null), 600)
  }, [])

  const startPolling = useCallback(() => {
    if (pollingRef.current) clearInterval(pollingRef.current)
    pollingRef.current = setInterval(() => {
      dispatch(listFeatureFlags())
    }, 2000)
    setTimeout(() => {
      if (pollingRef.current) clearInterval(pollingRef.current)
    }, 10000)
  }, [dispatch])

  const sendWebhookAction = useCallback(async (featureId, action, trafficPercentage) => {
    setActionLoading(featureId)
    try {
      let response

      // Map action to WF1 AI Agent format and send to n8n webhook
      const agentAction = ACTION_MAP[action] || action
      const body = { feature_id: featureId, action: agentAction }
      if (trafficPercentage !== undefined) {
        body.traffic_percentage = trafficPercentage
      }
      if (agentAction === 'test') body.target_state = 'Testing'
      if (agentAction === 'rollback') body.target_state = 'Disabled'

      try {
        // Use backend proxy to keep API key server-side
        const n8nRes = await fetch('/api/autopilot/feature-control', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        })
        if (n8nRes.ok) {
          response = await n8nRes.json()
        } else {
          throw new Error(`n8n returned ${n8nRes.status}`)
        }
      } catch (n8nError) {
        // Fallback: direct backend API (bypasses AI Agent)
        const stateMap = { enable: 'Enabled', disable: 'Disabled', testing: 'Testing' }
        const endpoint = action === 'traffic'
          ? `/api/feature-flags/${featureId}/traffic`
          : `/api/feature-flags/${featureId}/state`
        const payload = action === 'traffic'
          ? { percentage: trafficPercentage }
          : { state: stateMap[action] }

        const res = await fetch(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        })
        response = await res.json()
        if (!res.ok) {
          throw new Error(response.message || response.error || 'Request failed')
        }
      }

      // n8n Respond node may return array — unwrap first item
      const payload = Array.isArray(response) ? response[0] : response

      if (payload.error || payload.success === false) {
        setToast({ message: payload.message || payload.error || 'Action failed', type: 'error' })
      } else {
        // Show AI Agent's response message
        const agentMessage = payload.message || payload.alert_message || `Status: ${payload.status || 'updated'}`
        setToast({ message: agentMessage, type: 'success' })
        triggerFlash(featureId)
        startPolling()
      }
    } catch (err) {
      setToast({ message: `Error: ${err.message}`, type: 'error' })
    } finally {
      setActionLoading(null)
    }
  }, [triggerFlash, startPolling])

  const handleAction = useCallback((featureId, action) => {
    sendWebhookAction(featureId, action)
  }, [sendWebhookAction])

  const handleTrafficApply = useCallback((featureId, percentage) => {
    sendWebhookAction(featureId, 'traffic', percentage)
  }, [sendWebhookAction])

  const handleSelectAutoPilot = useCallback((id) => {
    setSelectedAutoPilot((cur) => (cur === id ? null : id))
  }, [])

  const handleAutoPilotUpdate = useCallback(() => {
    dispatch(listFeatureFlags())
  }, [dispatch])

  const handleReset = () => {
    setSearchTerm('')
    setStatusFilter('All')
  }

  const totalCount = Object.keys(localFlags).length
  const hasFilters = searchTerm !== '' || statusFilter !== 'All'

  // Find the selected feature data for AutoPilotControls
  const selectedFlag = selectedAutoPilot && localFlags[selectedAutoPilot]
    ? { id: selectedAutoPilot, name: localFlags[selectedAutoPilot].name || selectedAutoPilot }
    : null

  return (
    <section className="feature-dashboard" aria-labelledby="feature-dashboard-title">
      <Toast message={toast.message} type={toast.type} onClose={() => setToast({ message: '', type: 'info' })} />

      <div className="feature-dashboard__header">
        <h1 className="feature-dashboard__title" id="feature-dashboard-title">Feature Dashboard</h1>
      </div>

      <div className="feature-dashboard__controls">
        <div className="feature-dashboard__search-wrap">
          <label htmlFor="feature-search" className="feature-dashboard__search-label">Search</label>
          <input
            id="feature-search"
            type="text"
            className="feature-dashboard__search"
            placeholder="Search features..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <div className="feature-dashboard__filter-group" role="group" aria-label="Filter by status">
          {STATUS_OPTIONS.map((status) => (
            <button
              key={status}
              className={`feature-dashboard__filter-btn ${
                statusFilter === status ? 'feature-dashboard__filter-btn--active' : ''
              }`}
              onClick={() => setStatusFilter(status)}
              aria-pressed={statusFilter === status}
            >
              {status}
            </button>
          ))}
        </div>
      </div>

      <div aria-live="polite" aria-busy={loading}>
        {loading ? (
          <SkeletonRows />
        ) : error ? (
          <Message variant="danger">{error}</Message>
        ) : totalCount === 0 ? (
          <EmptyState hasFilters={false} onReset={handleReset} />
        ) : filteredFlags.length === 0 ? (
          <EmptyState hasFilters={hasFilters} onReset={handleReset} />
        ) : (
          <div className="feature-dashboard__table-wrap">
            <table className="feature-dashboard__table" role="table">
              <thead>
                <tr>
                  <th scope="col">ID</th>
                  <th scope="col">Feature</th>
                  <th scope="col">Status</th>
                  <th scope="col">Traffic</th>
                  <th scope="col">Actions</th>
                  <th scope="col">AI Agent</th>
                  <th scope="col">Modified</th>
                </tr>
              </thead>
              <tbody>
                {filteredFlags.map(([id, flag]) => (
                  <FeatureRow
                    key={id}
                    id={id}
                    flag={flag}
                    onAction={handleAction}
                    onTrafficApply={handleTrafficApply}
                    onSelectAutoPilot={handleSelectAutoPilot}
                    isSelected={selectedAutoPilot === id}
                    flashId={flashId}
                    loading={actionLoading === id}
                  />
                ))}
              </tbody>
            </table>
            <div className="feature-dashboard__footer" role="status">
              Showing {filteredFlags.length} of {totalCount} features
            </div>
          </div>
        )}
      </div>

      {/* Auto-Pilot Panel — appears when a feature is selected */}
      {selectedFlag && (
        <div className="autopilot-panel">
          <AutoPilotControls
            feature={selectedFlag}
            onUpdate={handleAutoPilotUpdate}
            onClose={() => setSelectedAutoPilot(null)}
          />
        </div>
      )}
    </section>
  )
}

export default FeatureFlagListScreen
