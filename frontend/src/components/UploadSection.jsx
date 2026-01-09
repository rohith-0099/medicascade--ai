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
        <div className="card-glass max-w-2xl mx-auto">
            <div className="text-center mb-8">
                <h2 className="text-2xl font-bold mb-2">Upload Patient Report</h2>
                <p className="text-slate-300">
                    Upload a PDF containing patient data (symptoms, lab results, imaging, clinical notes)
                </p>
            </div>

            {/* Upload Area */}
            <div
                className={`relative border-2 border-dashed rounded-xl p-12 text-center transition-all duration-300 ${isDragging
                        ? 'border-primary-500 bg-primary-500/10'
                        : 'border-slate-600 hover:border-slate-500'
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
                    <>
                        <svg
                            className="w-16 h-16 mx-auto mb-4 text-slate-400"
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
                        <p className="text-lg font-medium mb-2">
                            Drag & drop your PDF here
                        </p>
                        <p className="text-sm text-slate-400 mb-4">or click to browse</p>
                        <p className="text-xs text-slate-500">
                            Supports PDF files up to 50MB
                        </p>
                    </>
                ) : (
                    <div className="space-y-4">
                        <svg
                            className="w-16 h-16 mx-auto text-success-500"
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
                        <div>
                            <p className="text-lg font-medium text-success-500 mb-1">
                                File selected
                            </p>
                            <p className="text-sm text-slate-300">{selectedFile.name}</p>
                            <p className="text-xs text-slate-500 mt-1">
                                {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                            </p>
                        </div>
                        <button
                            onClick={(e) => {
                                e.stopPropagation()
                                setSelectedFile(null)
                            }}
                            className="text-sm text-slate-400 hover:text-slate-300 underline"
                        >
                            Change file
                        </button>
                    </div>
                )}
            </div>

            {/* Submit Button */}
            {selectedFile && (
                <div className="mt-8 flex justify-center">
                    <button onClick={handleSubmit} className="btn-primary">
                        <svg
                            className="w-5 h-5 mr-2 inline-block"
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
                        Start AI Diagnosis
                    </button>
                </div>
            )}

            {/* Info Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
                <div className="bg-slate-700/50 rounded-lg p-4 text-center">
                    <div className="text-2xl font-bold text-primary-400 mb-1">4</div>
                    <div className="text-xs text-slate-400">Processing Layers</div>
                </div>
                <div className="bg-slate-700/50 rounded-lg p-4 text-center">
                    <div className="text-2xl font-bold text-success-500 mb-1">5</div>
                    <div className="text-xs text-slate-400">AI Specialists</div>
                </div>
                <div className="bg-slate-700/50 rounded-lg p-4 text-center">
                    <div className="text-2xl font-bold text-yellow-500 mb-1">100%</div>
                    <div className="text-xs text-slate-400">Explainable</div>
                </div>
            </div>
        </div>
    )
}
