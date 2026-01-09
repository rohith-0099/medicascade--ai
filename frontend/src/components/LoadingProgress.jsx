export default function LoadingProgress({ progress, currentLayer }) {
    const circumference = 2 * Math.PI * 80

    return (
        <div className="card-premium max-w-3xl mx-auto">
            <div className="text-center mb-10">
                {/* Animated Progress Circle */}
                <div className="relative inline-block mb-6">
                    <svg className="w-48 h-48" viewBox="0 0 200 200">
                        {/* Background circle */}
                        <circle
                            cx="100"
                            cy="100"
                            r="80"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="12"
                            className="text-slate-200"
                        />
                        {/* Progress circle */}
                        <circle
                            cx="100"
                            cy="100"
                            r="80"
                            fill="none"
                            stroke="url(#gradient)"
                            strokeWidth="12"
                            strokeLinecap="round"
                            strokeDasharray={circumference}
                            strokeDashoffset={circumference - (circumference * progress) / 100}
                            className="transition-all duration-500 ease-out transform -rotate-90"
                            style={{ transformOrigin: '50% 50%' }}
                        />
                        {/* Gradient definition */}
                        <defs>
                            <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                                <stop offset="0%" stopColor="#3b82f6" />
                                <stop offset="100%" stopColor="#6366f1" />
                            </linearGradient>
                        </defs>
                        {/* Center percentage */}
                        <text
                            x="100"
                            y="100"
                            textAnchor="middle"
                            dy=".3em"
                            className="text-5xl font-bold fill-slate-700"
                        >
                            {progress}%
                        </text>
                    </svg>

                    {/* Pulse effect */}
                    <div className="absolute inset-0 -z-10">
                        <div className="w-48 h-48 bg-blue-400 rounded-full opacity-20 animate-ping"></div>
                    </div>
                </div>

                <h2 className="text-3xl font-bold text-slate-800 mb-3">Analyzing Patient Data</h2>
                <p className="text-lg text-blue-600 font-medium mb-2">{currentLayer}</p>
                <p className="text-slate-500">Processing through multi-layer AI diagnostic system</p>
            </div>

            {/* Processing Steps */}
            <div className="space-y-5">
                <ProcessStep
                    number="1"
                    label="Layer 0: Data Extraction"
                    description="Extracting text, tables, images, and structured data from PDF"
                    isComplete={progress > 20}
                    isActive={progress <= 20}
                />
                <ProcessStep
                    number="2"
                    label="Layer 1: AI Specialists"
                    description="Running 5 specialist models in parallel (symptoms, labs, scans, notes, risk)"
                    isComplete={progress > 40}
                    isActive={progress > 20 && progress <= 40}
                />
                <ProcessStep
                    number="3"
                    label="Layer 2: Cross-Validation"
                    description="Major AI validator resolving conflicts and anomaly detection"
                    isComplete={progress > 65}
                    isActive={progress > 40 && progress <= 65}
                />
                <ProcessStep
                    number="4"
                    label="Layer 3: Explanation"
                    description="Generating annotated report with visual evidence markers"
                    isComplete={progress > 85}
                    isActive={progress > 65 && progress <= 85}
                />
            </div>

            {/* Info Box */}
            <div className="mt-10 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-6 border border-blue-100">
                <div className="flex items-start gap-4">
                    <div className="flex-shrink-0">
                        <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                            <svg
                                className="w-6 h-6 text-blue-600"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                            >
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                                />
                            </svg>
                        </div>
                    </div>
                    <div className="flex-1">
                        <h4 className="font-semibold text-slate-700 mb-2">Deep Analysis in Progress</h4>
                        <p className="text-sm text-slate-600 leading-relaxed">
                            Our advanced AI system is processing your data through multiple validation layers.
                            This comprehensive analysis typically takes 30-60 seconds to ensure maximum accuracy.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    )
}

function ProcessStep({ number, label, description, isComplete, isActive }) {
    return (
        <div className="flex items-start gap-4 group">
            <div className="flex-shrink-0">
                {isComplete ? (
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center shadow-lg">
                        <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                        </svg>
                    </div>
                ) : isActive ? (
                    <div className="relative w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-500 flex items-center justify-center shadow-lg">
                        <div className="absolute inset-0 rounded-xl bg-blue-400 animate-ping opacity-50"></div>
                        <span className="relative text-white font-bold text-lg">{number}</span>
                    </div>
                ) : (
                    <div className="w-12 h-12 rounded-xl bg-slate-200 flex items-center justify-center">
                        <span className="text-slate-500 font-bold text-lg">{number}</span>
                    </div>
                )}
            </div>
            <div className="flex-1 pt-1">
                <h3 className={`font-semibold text-lg mb-1 transition-colors ${isActive ? 'text-blue-600' : isComplete ? 'text-emerald-600' : 'text-slate-400'
                    }`}>
                    {label}
                </h3>
                <p className="text-sm text-slate-500 leading-relaxed">{description}</p>
            </div>
        </div>
    )
}
