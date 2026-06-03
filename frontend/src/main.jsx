import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }
  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }
  componentDidCatch(error, info) {
    console.error('[MediCascade] React render error:', error, info)
  }
  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          minHeight: '100vh', background: '#f2eee3', color: '#9c1d0b',
          display: 'flex', flexDirection: 'column', alignItems: 'center',
          justifyContent: 'center', fontFamily: "'JetBrains Mono', monospace", padding: 40, textAlign: 'center',
        }}>
          <div style={{ fontSize: 40, marginBottom: 16 }}>⚠</div>
          <div style={{ fontSize: 18, fontWeight: 700, marginBottom: 12, color: '#18140d' }}>Render Error</div>
          <div style={{ maxWidth: 600, fontSize: 13, color: '#9c1d0b', marginBottom: 20, whiteSpace: 'pre-wrap' }}>
            {String(this.state.error)}
          </div>
          <button
            onClick={() => { this.setState({ hasError: false, error: null }) }}
            style={{
              padding: '10px 24px', background: '#c8341f', color: '#fff',
              border: '1px solid #a4250f', borderRadius: 2, fontWeight: 700, cursor: 'pointer',
            }}
          >
            Retry
          </button>
        </div>
      )
    }
    return this.props.children
  }
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>,
)
