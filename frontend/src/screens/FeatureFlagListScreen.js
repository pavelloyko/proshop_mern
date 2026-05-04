import React, { useEffect } from 'react'
import { Table, Badge, OverlayTrigger, Tooltip } from 'react-bootstrap'
import { useDispatch, useSelector } from 'react-redux'
import Message from '../components/Message'
import Loader from '../components/Loader'
import { listFeatureFlags } from '../actions/featureFlagActions'

const statusBadge = (status) => {
  switch (status) {
    case 'Enabled':
      return <Badge variant='success'>{status}</Badge>
    case 'Testing':
      return <Badge variant='warning'>{status}</Badge>
    case 'Disabled':
      return <Badge variant='secondary'>{status}</Badge>
    default:
      return <Badge variant='light'>{status}</Badge>
  }
}

const FeatureFlagListScreen = ({ history }) => {
  const dispatch = useDispatch()

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

  const flagEntries = Object.entries(flags)

  return (
    <>
      <h1>Dashboard Features</h1>
      {loading ? (
        <Loader />
      ) : error ? (
        <Message variant='danger'>{error}</Message>
      ) : (
        <Table striped bordered hover responsive className='table-sm'>
          <thead>
            <tr>
              <th>ID</th>
              <th>Feature</th>
              <th>Status</th>
              <th>Traffic %</th>
              <th>Last Modified</th>
              <th>Depends On</th>
              <th>Priority</th>
              <th>Description</th>
            </tr>
          </thead>
          <tbody>
            {flagEntries.map(([id, flag]) => (
              <tr key={id}>
                <td>
                  <code>{id}</code>
                </td>
                <td>{flag.name_ru || flag.name}</td>
                <td>{statusBadge(flag.status)}</td>
                <td>{flag.traffic_percentage}%</td>
                <td>{flag.last_modified}</td>
                <td>
                  {flag.dependencies && flag.dependencies.length > 0
                    ? flag.dependencies.map((dep) => (
                        <code key={dep}>{dep}</code>
                      ))
                    : '—'}
                </td>
                <td>{flag.priority || '—'}</td>
                <td>
                  <OverlayTrigger
                    overlay={
                      <Tooltip id={`tooltip-${id}`}>
                        {flag.description}
                      </Tooltip>
                    }
                  >
                    <span
                      style={{
                        cursor: 'pointer',
                        maxWidth: 200,
                        display: 'inline-block',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {flag.code_status || flag.description}
                    </span>
                  </OverlayTrigger>
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      )}
    </>
  )
}

export default FeatureFlagListScreen
