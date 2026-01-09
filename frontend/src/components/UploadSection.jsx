import { useState, useRef } from 'react'

export default function UploadSection({ onFileUpload }) {
    const [isDragging, setIsDragging] = useState(false)
    const [selectedFile, setSelectedFile] = useState(null)
    const fileInputRef = useRef(null)

    const handleDragOver = (e) => {
        e.preventDefault()
        setIsDragging(true)
    }

    const handleDragLeave = () => {
        setIsDragging(false)
    }

    const handleDrop = (e) => {
        e.preventDefault()
        setIsDragging(false)

        const file = e.dataTransfer.files[0]
        handleFile(file)
    }

    const handleFileSelect = (e) => {
        const file = e.target.files[0]
        handleFile(file)
    }

    const handleFile = (file) => {
        if (file && file.type === 'application/pdf') {
            setSelectedFile(file)
        } else {
            alert('Please select a PDF file')
        }
    }

    const handleSubmit = () => {
        if (selectedFile) {
            onFileUpload(selectedFile)
        }
    }

    return (
        <div className="card-premium max-w-3xl mx-auto">
            <div className="text-center mb-8">
                <h2 className="text-3xl font-bold text-slate-800 mb-3">Upload Patient Report</h2>
                <p className="text-slate-600 text-lg">
                    Comprehensive analysis powered by 5 AI specialist models
                </p>
            </div>

            {/* Upload Area */}
            <div
                className={`relative border-2 border-dashed rounded-2xl p-12 text-center transition-all duration-300 cursor-pointer ${isDragging
                        ? 'border-blue-500 bg-blue-50 scale-105'
                        : 'border-slate-300 hover:border-blue-400 hover:bg-slate-50'
                    }`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
            >
                <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileSelect}
                    accept="application/pdf"
                    className="hidden"
                />

                {!selectedFile ? (
                    <div className="space-y-4">
                        <div className="inline-block p-6 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-2xl">
                            <svg
                                className="w-16 h-16 text-blue-600"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                            >
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                                />
                            </svg>
                        </div>
                        <div>
                            <p className="text-xl font-semibold text-slate-700 mb-2">
                                Drop patient PDF here
                            </p>
                            <p className="text-slate-500 mb-4">or click to browse files</p>
                            <p className="text-sm text-slate-400">
                                Supports comprehensive medical reports • Max 50MB
                            </p>
                        </div>
                    </div>
                ) : (
                    <div className="space-y-4">
                        <div className="inline-block p-6 bg-gradient-to-br from-emerald-100 to-teal-100 rounded-2xl">
                            <svg
                                className="w-16 h-16 text-emerald-600"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                            >
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                                />
                            </svg>
                        </div>
                        <div>
                            <p className="text-xl font-semibold text-emerald-700 mb-2">
                                Ready for analysis
                            </p>
                            <p className="text-slate-700 font-medium">{selectedFile.name}</p>
                            <p className="text-slate-500 text-sm mt-1">
                                {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                            </p>
                            <button
                                onClick={(e) => {
                                    e.stopPropagation()
                                    setSelectedFile(null)
                                }}
                                className="mt-3 text-sm text-blue-600 hover:text-blue-700 font-medium underline"
                            >
                                Change file
                            </button>
                        </div>
                    </div>
                )}
            </div>

            {/* Submit Button */}
            {selectedFile && (
                <div className="mt-8 flex justify-center">
                    <button onClick={handleSubmit} className="btn-primary group">
                        <div className="flex items-center gap-3">
                            <svg
                                className="w-6 h-6 group-hover:rotate-12 transition-transform"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                            >
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M13 10V3L4 14h7v7l9-11h-7z"
                                />
                            </svg>
                            <span className="text-lg">Start AI Analysis</span>
                        </div>
                    </button>
                </div>
            )}

            {/* Feature Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-10 pt-8 border-t border-slate-200">
                <div className="stat-card text-center group hover:scale-105 transition-transform">
                    <div className="text-3xl font-bold text-blue-600 mb-2">4</div>
                    <div className="text-sm font-medium text-slate-600">Processing Layers</div>
                    <div className="text-xs text-slate-400 mt-1">Sequential validation</div>
                </div>
                <div className="stat-card text-center group hover:scale-105 transition-transform">
                    <div className="text-3xl font-bold text-indigo-600 mb-2">5</div>
                    <div className="text-sm font-medium text-slate-600">AI Specialists</div>
                    <div className="text-xs text-slate-400 mt-1">Parallel analysis</div>
                </div>
                <div className="stat-card text-center group hover:scale-105 transition-transform">
                    <div className="text-3xl font-bold text-emerald-600 mb-2">100%</div>
                    <div className="text-sm font-medium text-slate-600">Explainable</div>
                    <div className="text-xs text-slate-400 mt-1">With evidence</div>
                </div>
            </div>
        </div>
    )
}
