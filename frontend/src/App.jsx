import { useState } from 'react'
import UploadSection from './components/UploadSection'
import LoadingProgress from './components/LoadingProgress'
import ResultsDashboard from './components/ResultsDashboard'

function App() {
    const [state, setState] = useState({
        isProcessing: false,
        progress: 0,
        currentLayer: '',
        results: null,
        error: null
    })

    const handleFileUpload = async (file) => {
        setState({
            isProcessing: true,
            progress: 0,
            currentLayer: 'Uploading...',
            results: null,
            error: null
        })

        const formData = new FormData()
        formData.append('file', file)

        try {
            // Simulate progress updates
            updateProgress(25, 'Layer 0: Processing PDF...')

            const response = await fetch('/api/diagnose', {
                method: 'POST',
                body: formData
            })

            if (!response.ok) {
                throw new Error(`Server error: ${response.status}`)
            }

            updateProgress(50, 'Layer 1: Running AI Specialists...')
            await sleep(500)

            updateProgress(75, 'Layer 2: Validating...')
            await sleep(500)

            updateProgress(90, 'Layer 3: Generating Report...')

            const data = await response.json()

            updateProgress(100, 'Complete!')
            await sleep(500)

            setState({
                isProcessing: false,
                progress: 100,
                currentLayer: '',
                results: data,
                error: null
            })
        } catch (error) {
            console.error('Diagnosis error:', error)
            setState(prev => ({
                ...prev,
                isProcessing: false,
                error: error.message
            }))
        }
    }

    const updateProgress = (progress, layer) => {
        setState(prev => ({
            ...prev,
            progress,
            currentLayer: layer
        }))
    }

    const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms))

    const handleReset = () => {
        setState({
            isProcessing: false,
            progress: 0,
            currentLayer: '',
            results: null,
            error: null
        })
    }

    return (
        <div className="min-h-screen py-8 px-4">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <header className="text-center mb-12">
                    <div className="inline-block mb-4">
                        <div className="w-20 h-20 bg-gradient-to-br from-primary-500 to-primary-700 rounded-2xl flex items-center justify-center shadow-2xl">
                            <svg className="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                        </div>
                    </div>

                    <h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-primary-400 to-primary-600 bg-clip-text text-transparent">
                        MedicaScade AI
                    </h1>
                    <p className="text-xl text-slate-300 max-w-2xl mx-auto">
                        Universal AI Disease Prediction Engine
                    </p>
                    <p className="text-sm text-slate-400 mt-2">
                        Multi-layer AI diagnostic system with explainable results
                    </p>
                </header>

                {/* Error Display */}
                {state.error && (
                    <div className="card mb-8 bg-danger-500/10 border-danger-500/30">
                        <div className="flex items-start">
                            <svg className="w-6 h-6 text-danger-500 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            <div>
                                <h3 className="font-semibold text-danger-500 mb-1">Processing Error</h3>
                                <p className="text-slate-300 text-sm">{state.error}</p>
                                <button onClick={handleReset} className="mt-3 text-sm text-primary-400 hover:text-primary-300 underline">
                                    Try again
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* Main Content */}
                {!state.results && !state.isProcessing && (
                    <UploadSection onFileUpload={handleFileUpload} />
                )}

                {state.isProcessing && (
                    <LoadingProgress progress={state.progress} currentLayer={state.currentLayer} />
                )}

                {state.results && !state.isProcessing && (
                    <ResultsDashboard results={state.results} onReset={handleReset} />
                )}
            </div>
        </div>
    )
}

export default App
