export default function LoadingProgress({ progress, currentLayer }) {
    return (
        <div className="card-glass max-w-2xl mx-auto">
            <div className="text-center mb-8">
                <div className="inline-block relative">
                    <div className="w-24 h-24 relative">
                        {/* Spinning loader */}
                        <svg className="animate-spin" viewBox="0 0 100 100">
                            <circle
                                cx="50"
                                cy="50"
                                r="45"
                                fill="none"
                                stroke="currentColor"
                                strokeWidth="8"
                                strokeLinecap="round"
                                className="text-slate-700"
                            />
                            <circle
                                cx="50"
                                cy="50"
                                r="45"
                                fill="none"
                                stroke="currentColor"
                                strokeWidth="8"
                                strokeLinecap="round"
                                strokeDasharray="283"
                                strokeDashoffset={283 - (283 * progress) / 100}
                                className="text-primary-500"
                                style={{ transition: 'stroke-dashoffset 0.5s ease' }}
                            />
                        </svg>
                        {/* Percentage in center */}
                        <div className="absolute inset-0 flex items-center justify-center">
                            <span className="text-2xl font-bold">{progress}%</span>
                        </div>
                    </div>
                </div>

                <h2 className="text-2xl font-bold mt-6 mb-2">Processing Patient Data</h2>
                <p className="text-slate-300 mb-6">{currentLayer}</p>
            </div>

            {/* Progress Steps */}
            <div className="space-y-4">
                <ProgressStep
                    label="Layer 0: PDF Processing"
                    description="Extracting text, images, and structured data"
                    isComplete={progress > 25}
                    isActive={progress <= 25}
                />
                <ProgressStep
                    label="Layer 1: AI Specialists"
                    description="Running 5 specialist models in parallel"
                    isComplete={progress > 50}
                    isActive={progress > 25 && progress <= 50}
                />
                <ProgressStep
                    label="Layer 2: Validation"
                    description="Cross-validating and resolving conflicts"
                    isComplete={progress > 75}
                    isActive={progress > 50 && progress <= 75}
                />
                <ProgressStep
                    label="Layer 3: Explanation"
                    description="Generating annotated report with evidence"
                    isComplete={progress > 90}
                    isActive={progress > 75 && progress <= 90}
                />
            </div>

            <div className="mt-8 bg-slate-700/30 rounded-lg p-4">
                <div className="flex items-start">
                    <svg
                        className="w-5 h-5 text-primary-400 mr-3 flex-shrink-0 mt-0.5"
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
                    <p className="text-sm text-slate-300">
                        This may take 30-60 seconds depending on the complexity of the patient data and AI model availability.
                    </p>
                </div>
            </div>
        </div>
    )
}

function ProgressStep({ label, description, isComplete, isActive }) {
    return (
        <div className="flex items-start">
            <div className="flex-shrink-0 mr-4">
                {isComplete ? (
                    <div className="w-8 h-8 rounded-full bg-success-500 flex items-center justify-center">
                        <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                    </div>
                ) : isActive ? (
                    <div className="w-8 h-8 rounded-full bg-primary-500 animate-pulse-slow flex items-center justify-center">
                        <div className="w-3 h-3 rounded-full bg-white"></div>
                    </div>
                ) : (
                    <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center">
                        <div className="w-3 h-3 rounded-full bg-slate-600"></div>
                    </div>
                )}
            </div>
            <div className="flex-1">
                <h3 className={`font-semibold ${isActive ? 'text-primary-400' : isComplete ? 'text-success-500' : 'text-slate-400'}`}>
                    {label}
                </h3>
                <p className="text-sm text-slate-500 mt-1">{description}</p>
            </div>
        </div>
    )
}
