import React, { useEffect, useState, useMemo, useCallback, useRef } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import Message from '../components/Message'
import { listFeatureFlags } from '../actions/featureFlagActions'

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

const nextStatus = (current) => {
  if (current === 'Enabled') return 'Disabled'
  if (current === 'Testing') return 'Enabled'
  return 'Enabled'
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

const ToggleSwitch = ({ checked, onChange, label }) => (
  <label className="feature-toggle" title={`Toggle ${label}`}>
    <span className="feature-toggle__sr-label">Toggle {label}</span>
    <input
      type="checkbox"
      role="switch"
      aria-checked={checked}
      checked={checked}
      onChange={onChange}
    />
    <span className="feature-toggle__track" />
    <span className="feature-toggle__thumb" />
  </label>
)

const FeatureRow = ({ id, flag, onToggle, onTrafficChange, flashId }) => {
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
        <div className="feature-slider">
          <input
            type="range"
            min="0"
            max="100"
            value={flag.traffic_percentage}
            onChange={(e) => onTrafficChange(id, Number(e.target.value))}
            aria-label={`Traffic percentage for ${flag.name}`}
            aria-valuenow={flag.traffic_percentage}
            aria-valuemin="0"
            aria-valuemax="100"
          />
          <span className="feature-slider__value">{flag.traffic_percentage}%</span>
        </div>
      </td>
      <td>
        <ToggleSwitch
          checked={flag.status !== 'Disabled'}
          onChange={() => onToggle(id)}
          label={flag.name}
        />
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
  const flashTimer = useRef(null)

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

  const handleToggle = useCallback((id) => {
    setLocalFlags((prev) => {
      const next = { ...prev }
      next[id] = { ...next[id], status: nextStatus(next[id].status) }
      return next
    })
    triggerFlash(id)
  }, [triggerFlash])

  const handleTrafficChange = useCallback((id, value) => {
    setLocalFlags((prev) => {
      const next = { ...prev }
      next[id] = { ...next[id], traffic_percentage: value }
      return next
    })
  }, [])

  const handleReset = () => {
    setSearchTerm('')
    setStatusFilter('All')
  }

  const totalCount = Object.keys(localFlags).length
  const hasFilters = searchTerm !== '' || statusFilter !== 'All'

  return (
    <section className="feature-dashboard" aria-labelledby="feature-dashboard-title">
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
                  <th scope="col">Toggle</th>
                  <th scope="col">Modified</th>
                </tr>
              </thead>
              <tbody>
                {filteredFlags.map(([id, flag]) => (
                  <FeatureRow
                    key={id}
                    id={id}
                    flag={flag}
                    onToggle={handleToggle}
                    onTrafficChange={handleTrafficChange}
                    flashId={flashId}
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
    </section>
  )
}

export default FeatureFlagListScreen
