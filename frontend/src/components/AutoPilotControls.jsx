import React, { useState } from 'react'

/**
 * AutoPilotControls — AI Agent panel for a single feature flag.
 * Sends actions through the backend proxy (/api/autopilot/feature-control)
 * which forwards to n8n webhook. Keeps API key server-side.
 *
 * Props:
 *   feature  — { id, name } (or { key, name } for card-based screens)
 *   onUpdate — callback after successful mutation
 *   onClose  — callback to dismiss the panel
 */
const AutoPilotControls = ({ feature, onUpdate, onClose }) => {
  const [loading, setLoading] = useState(null)
  const [feedback, setFeedback] = useState(null)

  const featureId = feature.id || feature.key

  const callAutoPilot = async (action, extras = {}) => {
    setLoading(action)
    setFeedback(null)

    try {
      const response = await fetch('/api/autopilot/feature-control', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          feature_id: featureId,
          action,
          ...extras,
        }),
      })

      let result = {}
      try {
        result = await response.json()
      } catch (_) {
        // non-JSON body
      }

      // n8n Respond node may wrap in array — unwrap
      const payload = Array.isArray(result) ? result[0] : result

      if (!response.ok || payload.success === false) {
        setFeedback({
          type: 'error',
          message: payload.message || `HTTP ${response.status}`,
          state: payload.current_state || null,
        })
        return
      }

      setFeedback({
        type: 'success',
        message: payload.message || 'Done',
        state: payload.current_state || null,
      })
      if (payload.current_state && onUpdate) onUpdate(payload.current_state)
    } catch (e) {
      setFeedback({
        type: 'error',
        message: `Network: ${e.message}`,
        state: null,
      })
    } finally {
      setLoading(null)
    }
  }

  const busy = loading !== null

  return (
    <section className="autopilot" aria-label="Auto-Pilot Controls">
      <div className="autopilot__header">
        <div style={{ minWidth: 0 }}>
          <h2 className="autopilot__title">Auto-Pilot</h2>
          <p className="autopilot__desc">
            Управление фичей <strong>{feature.name || featureId}</strong>
            {' '}через n8n AI Agent (WF1).
          </p>
          <div className="autopilot__key">{featureId}</div>
        </div>
        {onClose && (
          <button
            type="button"
            className="feature-action-btn"
            onClick={onClose}
            aria-label="Close Auto-Pilot panel"
          >
            Close
          </button>
        )}
      </div>

      {/* Agent Response */}
      {feedback && (
        <div
          className={`autopilot__feedback autopilot__feedback--${feedback.type}`}
          role="alert"
        >
          <div className="autopilot__feedback-msg">
            {feedback.type === 'success' ? '✅' : '⚠️'} {feedback.message}
          </div>
          {feedback.state && (
            <div className="autopilot__feedback-state">
              Status: <strong>{feedback.state.status}</strong> | Traffic:{' '}
              <strong>{feedback.state.traffic_percentage}%</strong>
            </div>
          )}
        </div>
      )}

      {/* Action Buttons */}
      <div className="autopilot__actions">
        <button
          className="feature-action-btn feature-action-btn--testing"
          onClick={() => callAutoPilot('check')}
          disabled={busy}
        >
          {loading === 'check' ? 'Проверяем…' : '🔍 Check Status'}
        </button>

        <button
          className="feature-action-btn feature-action-btn--enable"
          onClick={() => callAutoPilot('test', { target_state: 'Testing' })}
          disabled={busy}
        >
          {loading === 'test' ? 'Включаем…' : '▶ Testing Mode'}
        </button>

        <button
          className="feature-action-btn feature-action-btn--disable"
          onClick={() => callAutoPilot('rollback', { target_state: 'Disabled' })}
          disabled={busy}
        >
          {loading === 'rollback' ? 'Откатываем…' : '⏪ Rollback'}
        </button>
      </div>

      {/* Loading indicator */}
      {busy && (
        <div className="autopilot__loading" aria-live="polite">
          ⏳ AI Agent думает...
        </div>
      )}
    </section>
  )
}

export default AutoPilotControls
