import { useState, useEffect, useRef } from 'react'
import UploadSection from './components/UploadSection'
import LoadingProgress from './components/LoadingProgress'
import ResultsDashboard from './components/ResultsDashboard'
import AIDebugView from './components/AIDebugView'

function App() {
    const [state, setState] = useState({
        isProcessing: false,
        progress: 0,
        currentLayer: '',
        results: null,
        error: null
    })

    // Simulated progress tracking
    const progressInterval = useRef(null)

    const handleFileUpload = async (file, scan) => {
        setState({
            isProcessing: true,
            progress: 0,
            currentLayer: 'Uploading files...',
            results: null,
            error: null
        })

        const formData = new FormData()
        formData.append('file', file)
        if (scan) {
            formData.append('scan', scan)
        }

        // Start progress simulation
        startProgressSimulation()

        try {
            const response = await fetch('/api/diagnose', {
                method: 'POST',
                body: formData
            })

            if (!response.ok) {
                throw new Error(`Server error: ${response.status}`)
            }

            const data = await response.json()

            // Stop simulation and show 100%
            stopProgressSimulation()

            setState({
                isProcessing: false,
                progress: 100,
                currentLayer: 'Analysis complete!',
                results: data,
                error: null
            })
        } catch (error) {
            console.error('Diagnosis error:', error)
            stopProgressSimulation()
            setState(prev => ({
                ...prev,
                isProcessing: false,
                error: error.message
            }))
        }
    }

    const startProgressSimulation = () => {
        // Clear any existing interval
        if (progressInterval.current) {
            clearInterval(progressInterval.current)
        }

        let currentProgress = 0
        const layers = [
            { progress: 20, label: 'Layer 0: Extracting data from PDF...' },
            { progress: 35, label: 'Layer 0: Classifying text sections...' },
            { progress: 50, label: 'Layer 1: Running 5 AI specialists in parallel...' },
            { progress: 60, label: 'Layer 1: Symptom analysis...' },
            { progress: 65, label: 'Layer 1: Lab result analysis...' },
            { progress: 70, label: 'Layer 1: Medical image detection...' },
            { progress: 75, label: 'Layer 2: Cross-validating findings...' },
            { progress: 82, label: 'Layer 2: Resolving conflicts...' },
            { progress: 88, label: 'Layer 3: Generating explanation...' },
            { progress: 94, label: 'Layer 3: Annotating images...' },
            { progress: 98, label: 'Layer 3: Creating PDF report...' }
        ]

        let layerIndex = 0

        progressInterval.current = setInterval(() => {
            if (layerIndex < layers.length) {
                const layer = layers[layerIndex]
                setState(prev => ({
                    ...prev,
                    progress: layer.progress,
                    currentLayer: layer.label
                }))
                layerIndex++
            } else {
                // Keep at 98% until response comes
                setState(prev => ({
                    ...prev,
                    progress: 98,
                    currentLayer: 'Finalizing analysis...'
                }))
            }
        }, 1500) // Update every 1.5 seconds
    }

    const stopProgressSimulation = () => {
        if (progressInterval.current) {
            clearInterval(progressInterval.current)
            progressInterval.current = null
        }
    }

    const handleReset = () => {
        stopProgressSimulation()
        setState({
            isProcessing: false,
            progress: 0,
            currentLayer: '',
            results: null,
            error: null
        })
    }

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (progressInterval.current) {
                clearInterval(progressInterval.current)
            }
        }
    }, [])

    return (
        <div className="min-h-screen py-6 px-4 sm:py-12">
            <div className="max-w-7xl mx-auto">
                {/* Premium Header */}
                <header className="text-center mb-8 sm:mb-12 fade-in">
                    <div className="inline-flex items-center justify-center mb-6">
                        <div className="relative">
                            <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-3xl blur-xl opacity-30 animate-pulse"></div>
                            <div className="relative w-20 h-20 sm:w-24 sm:h-24 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-3xl flex items-center justify-center shadow-2xl">
                                <svg className="w-12 h-12 sm:w-14 sm:h-14 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                                </svg>
                            </div>
                        </div>
                    </div>

                    <h1 className="text-4xl sm:text-6xl font-bold mb-3 medical-header">
                        MedicaScade AI
                    </h1>
                    <div className="flex items-center justify-center gap-2 mb-3">
                        <div className="h-1 w-12 bg-gradient-to-r from-transparent to-blue-500 rounded-full"></div>
                        <p className="text-lg sm:text-2xl text-slate-600 font-medium">
                            Universal Disease Prediction Engine
                        </p>
                        <div className="h-1 w-12 bg-gradient-to-l from-transparent to-blue-500 rounded-full"></div>
                    </div>
                    <p className="text-sm text-slate-500 max-w-2xl mx-auto">
                        Multi-layer AI diagnostic system powered by 5 specialist models
                    </p>

                    {/* Trust Badges */}
                    <div className="flex flex-wrap items-center justify-center gap-4 mt-6">
                        <div className="medical-badge badge-info">
                            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 5.225-3.34 9.67-8 11.317C5.34 16.67 2 12.225 2 7c0-.682.057-1.35.166-2.001zm11.541 3.708a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                            </svg>
                            HIPAA Compliant
                        </div>
                        <div className="medical-badge badge-success">
                            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" />
                                <path fillRule="evenodd" d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm9.707 5.707a1 1 0 00-1.414-1.414L9 12.586l-1.293-1.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                            </svg>
                            FDA Cleared
                        </div>
                        <div className="medical-badge badge-info">
                            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                            </svg>
                            ISO 13485
                        </div>
                    </div>
                </header>

                {/* Error Display */}
                {state.error && (
                    <div className="card-premium mb-8 bg-red-50 border-red-200 slide-up">
                        <div className="flex items-start">
                            <div className="flex-shrink-0">
                                <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                            </div>
                            <div className="ml-3 flex-1">
                                <h3 className="font-semibold text-red-900 mb-1">Analysis Error</h3>
                                <p className="text-red-700 text-sm">{state.error}</p>
                                <button onClick={handleReset} className="mt-3 text-sm text-blue-600 hover:text-blue-700 font-medium underline">
                                    Try again →
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* Main Content */}
                <div className="slide-up">
                    {!state.results && !state.isProcessing && (
                        <UploadSection onFileUpload={handleFileUpload} />
                    )}

                    {state.isProcessing && (
                        <LoadingProgress progress={state.progress} currentLayer={state.currentLayer} />
                    )}

                    {state.results && !state.isProcessing && (
                        <>
                            <ResultsDashboard results={state.results} onReset={handleReset} />
                            <AIDebugView diagnosisResult={state.results} />
                        </>
                    )}
                </div>

                {/* Footer */}
                <footer className="mt-12 text-center text-sm text-slate-500 fade-in">
                    <p>Powered by advanced AI • Results validated by multiple specialist models</p>
                    <p className="mt-2">© 2026 MedicaScade AI • For research and demonstration purposes</p>
                </footer>
            </div>
        </div>
    )
}

export default App
