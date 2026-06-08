import React, { useEffect, useState } from 'react'
import { Table, Row, Col, Card } from 'react-bootstrap'
import { useDispatch, useSelector } from 'react-redux'
import axios from 'axios'
import Message from '../components/Message'
import Loader from '../components/Loader'

const AIRouterDashboardScreen = ({ history }) => {
  const [logs, setLogs] = useState([])
  const [stats, setStats] = useState({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const userLogin = useSelector((state) => state.userLogin)
  const { userInfo } = userLogin

  useEffect(() => {
    if (userInfo && userInfo.isAdmin) {
      fetchLogs()
    } else {
      history.push('/login')
    }
  }, [history, userInfo])

  const fetchLogs = async () => {
    try {
      setLoading(true)
      const config = {
        headers: { Authorization: `Bearer ${userInfo.token}` },
      }
      const { data } = await axios.get('/api/assistant/logs', config)
      setLogs(data.logs)
      setStats(data.stats)
      setLoading(false)
    } catch (err) {
      setError(
        (err.response && err.response.data && err.response.data.message) || err.message
      )
      setLoading(false)
    }
  }

  const formatTime = (dateStr) => {
    if (!dateStr) return ''
    const d = new Date(dateStr)
    return d.toLocaleString()
  }

  const truncate = (str, len = 60) => {
    if (!str) return ''
    return str.length > len ? str.substring(0, len) + '…' : str
  }

  return (
    <>
      <h1>🤖 AI Router Dashboard</h1>
      <p className='text-muted'>
        Privacy-routed AI assistant logs — PII requests go local, clean
        requests go cloud.
      </p>

      {loading ? (
        <Loader />
      ) : error ? (
        <Message variant='danger'>{error}</Message>
      ) : (
        <>
          {/* Summary Cards */}
          <Row className='mb-4'>
            <Col md={3}>
              <Card
                className='text-center p-3'
                style={{
                  backgroundColor: '#1a1a2e',
                  color: '#e0e0e0',
                  border: '1px solid #333',
                }}
              >
                <h5 style={{ color: '#adb5bd', fontSize: '13px' }}>
                  Total Queries
                </h5>
                <h2 style={{ color: '#ffffff' }}>{stats.total || 0}</h2>
              </Card>
            </Col>
            <Col md={3}>
              <Card
                className='text-center p-3'
                style={{
                  backgroundColor: '#0d2818',
                  color: '#c8e6c9',
                  border: '1px solid #1b5e20',
                }}
              >
                <h5 style={{ color: '#81c784', fontSize: '13px' }}>
                  🔒 Local (PII)
                </h5>
                <h2 style={{ color: '#4caf50' }}>
                  {stats.localCount || 0}
                </h2>
              </Card>
            </Col>
            <Col md={3}>
              <Card
                className='text-center p-3'
                style={{
                  backgroundColor: '#0a1929',
                  color: '#bbdefb',
                  border: '1px solid #0d47a1',
                }}
              >
                <h5 style={{ color: '#64b5f6', fontSize: '13px' }}>
                  ☁️ Cloud
                </h5>
                <h2 style={{ color: '#42a5f5' }}>
                  {stats.cloudCount || 0}
                </h2>
              </Card>
            </Col>
            <Col md={3}>
              <Card
                className='text-center p-3'
                style={{
                  backgroundColor: '#2e1a0e',
                  color: '#ffe0b2',
                  border: '1px solid #e65100',
                }}
              >
                <h5 style={{ color: '#ffb74d', fontSize: '13px' }}>
                  💰 Saved by Local
                </h5>
                <h2 style={{ color: '#ff9800' }}>
                  ${stats.savedByLocal || 0}
                </h2>
              </Card>
            </Col>
          </Row>

          {/* Logs Table */}
          <Table
            striped
            bordered
            hover
            responsive
            className='table-sm'
          >
            <thead>
              <tr>
                <th>Time</th>
                <th>User</th>
                <th>Message</th>
                <th>PII</th>
                <th>Route</th>
                <th>Model</th>
                <th>Reply</th>
                <th>Latency</th>
                <th>Cost</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr
                  key={log._id}
                  style={{
                    backgroundColor:
                      log.route === 'local'
                        ? 'rgba(46, 125, 50, 0.05)'
                        : 'rgba(21, 101, 192, 0.05)',
                  }}
                >
                  <td style={{ whiteSpace: 'nowrap', fontSize: '12px' }}>
                    {formatTime(log.createdAt)}
                  </td>
                  <td>
                    {(log.userId && log.userId.name) || log.userName || '—'}
                  </td>
                  <td title={log.message}>
                    {truncate(log.message, 50)}
                  </td>
                  <td>
                    {log.piiEntities && log.piiEntities.length > 0 ? (
                      log.piiEntities.map((e, i) => (
                        <span
                          key={i}
                          className='badge badge-danger mr-1'
                          style={{ fontSize: '10px' }}
                        >
                          {e}
                        </span>
                      ))
                    ) : (
                      <span className='text-muted'>—</span>
                    )}
                  </td>
                  <td>
                    <span
                      className='badge'
                      style={{
                        backgroundColor:
                          log.route === 'local'
                            ? '#2e7d32'
                            : '#1565c0',
                        color: '#fff',
                      }}
                    >
                      {log.route === 'local' ? '🔒 Local' : '☁️ Cloud'}
                    </span>
                  </td>
                  <td style={{ fontSize: '11px' }}>
                    {log.model ? log.model.split('/').pop() : '—'}
                  </td>
                  <td title={log.reply}>
                    {truncate(log.reply, 50)}
                  </td>
                  <td>{log.latencyMs}ms</td>
                  <td>
                    <span
                      style={{
                        color:
                          log.costUsd === 0
                            ? '#2e7d32'
                            : '#333',
                        fontWeight:
                          log.costUsd === 0 ? '600' : '400',
                      }}
                    >
                      ${(log.costUsd || 0).toFixed(4)}
                    </span>
                  </td>
                </tr>
              ))}
              {logs.length === 0 && (
                <tr>
                  <td colSpan={9} className='text-center text-muted py-4'>
                    No AI assistant queries yet. Start chatting!
                  </td>
                </tr>
              )}
            </tbody>
          </Table>
        </>
      )}
    </>
  )
}

export default AIRouterDashboardScreen
