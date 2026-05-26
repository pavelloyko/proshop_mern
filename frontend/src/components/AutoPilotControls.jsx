import React, { useState } from 'react'

const N8N_URL = process.env.REACT_APP_N8N_WEBHOOK_URL || 'http://localhost:5678/webhook'
const N8N_API_KEY = process.env.REACT_APP_N8N_API_KEY || 'proshop-secret'

const AutoPilotControls = ({ feature, onUpdate }) => {
  const [loading, setLoading] = useState(null)
  const [feedback, setFeedback] = useState(null)

  async function callAutoPilot(action, extras = {}) {
    setLoading(action)
    setFeedback(null)

    try {
      const response = await fetch(`${N8N_URL}/feature-control`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': N8N_API_KEY,
        },
        body: JSON.stringify({
          feature_id: feature.id,
          action,
          ...extras,
        }),
      })

      const result = await response.json()

      if (!response.ok || result.success === false) {
        setFeedback({ type: 'error', message: result.message || `HTTP ${response.status}` })
        return
      }

      setFeedback({ type: 'success', message: result.message })
      if (onUpdate) onUpdate(result.current_state)
    } catch (e) {
      setFeedback({ type: 'error', message: `Сеть: ${e.message}` })
    } finally {
      setLoading(null)
    }
  }

  return (
    <section className="autopilot" aria-labelledby="autopilot-title">
      <h2 className="autopilot__title" id="autopilot-title">
        Auto-Pilot Controls
      </h2>
      <p className="autopilot__desc">
        Управление фичей {feature.name || feature.id} через n8n AI Agent (WF1).
      </p>

      <div className="autopilot__status-row">
        <div className="autopilot__field">
          <span className="autopilot__label">loading</span>
          <span className="autopilot__value">{loading !== null ? 'true' : 'false'}</span>
        </div>
        <div className="autopilot__field">
          <span className="autopilot__label">error</span>
          <span className="autopilot__value">
            {feedback && feedback.type === 'error' ? feedback.message : 'null'}
          </span>
        </div>
        <div className="autopilot__field">
          <span className="autopilot__label">result</span>
          <span className="autopilot__value">
            {feedback && feedback.type === 'success' ? feedback.message : '—'}
          </span>
        </div>
      </div>

      <div className="autopilot__actions">
        <button
          className="feature-action-btn feature-action-btn--testing"
          onClick={() => callAutoPilot('check')}
          disabled={loading !== null}
        >
          {loading === 'check' ? 'Проверяем…' : 'Запустить проверку'}
        </button>

        <button
          className="feature-action-btn feature-action-btn--enable"
          onClick={() => callAutoPilot('test', { target_state: 'Testing' })}
          disabled={loading !== null}
        >
          {loading === 'test' ? 'Включаем…' : 'Тестовый режим'}
        </button>

        <button
          className="feature-action-btn feature-action-btn--disable"
          onClick={() => callAutoPilot('rollback', { target_state: 'Disabled' })}
          disabled={loading !== null}
        >
          {loading === 'rollback' ? 'Откатываем…' : 'Откатить фичу'}
        </button>
      </div>

      {feedback && (
        <div
          className={`autopilot__feedback autopilot__feedback--${feedback.type}`}
          role="alert"
        >
          {feedback.type === 'success' ? '✅' : '⚠️'} {feedback.message}
        </div>
      )}
    </section>
  )
}

export default AutoPilotControls
