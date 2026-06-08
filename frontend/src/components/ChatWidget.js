import React, { useState, useRef, useEffect } from 'react'
import { useSelector } from 'react-redux'
import axios from 'axios'

const ChatWidget = () => {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef(null)

  const userLogin = useSelector((state) => state.userLogin)
  const { userInfo } = userLogin

  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Only show for logged-in users — hooks must come before any return
  if (!userInfo) return null

  const toggleChat = () => {
    setIsOpen(!isOpen)
  }

  const sendMessage = async (e) => {
    e.preventDefault()
    const text = input.trim()
    if (!text || loading) return

    const userMsg = { role: 'user', content: text }
    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      const config = {
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${userInfo.token}`,
        },
      }

      const { data } = await axios.post(
        '/api/assistant/chat',
        { message: text },
        config
      )

      const botMsg = {
        role: 'assistant',
        content: data.reply,
        route: data.route,
        model: data.model,
        piiEntities: data.piiEntities,
        latencyMs: data.latencyMs,
        costUsd: data.costUsd,
      }
      setMessages((prev) => [...prev, botMsg])
    } catch (error) {
      const errMsg = {
        role: 'assistant',
        content: 'Sorry, something went wrong. Please try again.',
        isError: true,
      }
      setMessages((prev) => [...prev, errMsg])
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      {/* Chat bubble button */}
      <div
        onClick={toggleChat}
        style={{
          position: 'fixed',
          bottom: '24px',
          right: '24px',
          width: '56px',
          height: '56px',
          borderRadius: '50%',
          backgroundColor: isOpen ? '#6c757d' : '#007bff',
          color: '#fff',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: 'pointer',
          boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
          zIndex: 9999,
          fontSize: '24px',
          transition: 'background-color 0.2s',
        }}
        title={isOpen ? 'Close chat' : 'Open AI Assistant'}
      >
        {isOpen ? '✕' : '💬'}
      </div>

      {/* Chat panel */}
      {isOpen && (
        <div
          style={{
            position: 'fixed',
            bottom: '92px',
            right: '24px',
            width: '380px',
            maxHeight: '520px',
            display: 'flex',
            flexDirection: 'column',
            backgroundColor: '#fff',
            borderRadius: '12px',
            boxShadow: '0 8px 32px rgba(0,0,0,0.2)',
            zIndex: 9998,
            overflow: 'hidden',
          }}
        >
          {/* Header */}
          <div
            style={{
              backgroundColor: '#333',
              color: '#fff',
              padding: '12px 16px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <span style={{ fontWeight: '600', fontSize: '14px' }}>
              🤖 AI Assistant
            </span>
            <span style={{ fontSize: '11px', opacity: 0.7 }}>
              {userInfo.name}
            </span>
          </div>

          {/* Messages area */}
          <div
            style={{
              flex: 1,
              overflowY: 'auto',
              padding: '12px',
              maxHeight: '360px',
              minHeight: '200px',
              backgroundColor: '#f8f9fa',
            }}
          >
            {messages.length === 0 && (
              <div style={{ textAlign: 'center', color: '#999', padding: '24px 0', fontSize: '13px' }}>
                👋 Hi {userInfo.name}! Ask me about products, orders, or your profile.
              </div>
            )}
            {messages.map((msg, idx) => (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  justifyContent:
                    msg.role === 'user' ? 'flex-end' : 'flex-start',
                  marginBottom: '8px',
                }}
              >
                <div
                  style={{
                    maxWidth: '80%',
                    padding: '8px 12px',
                    borderRadius:
                      msg.role === 'user'
                        ? '12px 12px 2px 12px'
                        : '12px 12px 12px 2px',
                    backgroundColor:
                      msg.role === 'user'
                        ? '#007bff'
                        : msg.isError
                        ? '#f8d7da'
                        : '#fff',
                    color:
                      msg.role === 'user'
                        ? '#fff'
                        : msg.isError
                        ? '#721c24'
                        : '#333',
                    fontSize: '13px',
                    lineHeight: '1.4',
                    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                  }}
                >
                  {msg.content}
                  {msg.route && (
                    <div
                      style={{
                        fontSize: '10px',
                        marginTop: '4px',
                        opacity: 0.6,
                        borderTop: '1px solid rgba(0,0,0,0.1)',
                        paddingTop: '4px',
                      }}
                    >
                      {msg.route === 'local' ? '🔒' : '☁️'} {msg.model} · {msg.latencyMs}ms
                      {msg.piiEntities && msg.piiEntities.length > 0 && (
                        <span> · PII: {msg.piiEntities.join(', ')}</span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'flex-start',
                  marginBottom: '8px',
                }}
              >
                <div
                  style={{
                    padding: '8px 16px',
                    borderRadius: '12px 12px 12px 2px',
                    backgroundColor: '#fff',
                    color: '#666',
                    fontSize: '13px',
                    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                  }}
                >
                  <span className='spinner-border spinner-border-sm mr-1' />
                  Thinking...
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input area */}
          <form
            onSubmit={sendMessage}
            style={{
              display: 'flex',
              padding: '8px',
              borderTop: '1px solid #dee2e6',
              backgroundColor: '#fff',
            }}
          >
            <input
              type='text'
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder='Ask about products, orders…'
              disabled={loading}
              style={{
                flex: 1,
                border: '1px solid #dee2e6',
                borderRadius: '20px',
                padding: '8px 16px',
                fontSize: '13px',
                outline: 'none',
                marginRight: '8px',
              }}
            />
            <button
              type='submit'
              disabled={loading || !input.trim()}
              style={{
                borderRadius: '50%',
                width: '36px',
                height: '36px',
                border: 'none',
                backgroundColor:
                  loading || !input.trim() ? '#ccc' : '#007bff',
                color: '#fff',
                cursor: loading ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '16px',
              }}
            >
              ➤
            </button>
          </form>
        </div>
      )}
    </>
  )
}

export default ChatWidget
