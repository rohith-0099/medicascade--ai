export default function ResultsDashboard({ results, onReset }) {
    return (
        <div className="space-y-6">
            {/* Diagnosis Card */}
            <div className="card-premium bg-gradient-to-br from-blue-50 to-indigo-50">
                <div className="flex items-start justify-between mb-6">
                    <div className="flex-1">
                        <div className="flex items-center gap-3 mb-3">
                            <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center">
                                <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                            </div>
                            <div>
                                <h2 className="text-2xl font-bold text-slate-800">Diagnosis Complete</h2>
                                <p className="text-sm text-slate-600">AI Analysis Results</p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Primary Diagnosis */}
                <div className="bg-white rounded-xl p-6 mb-4 border border-blue-100">
                    <div className="flex items-start justify-between">
                        <div className="flex-1">
                            <p className="text-sm font-medium text-blue-600 mb-2">PRIMARY DIAGNOSIS</p>
                            <h3 className="text-3xl font-bold text-slate-800 mb-3">
                                {results.primary_diagnosis || 'No diagnosis provided'}
                            </h3>
                            <div className="flex items-center gap-4">
                                <div className="flex items-center gap-2">
                                    <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
                                    <span className="text-sm font-semibold text-emerald-600">
                                        {Math.round((results.confidence || 0) * 100)}% Confidence
                                    </span>
                                </div>
                            </div>
                        </div>
                        <div className="flex-shrink-0">
                            <ConfidenceGauge confidence={results.confidence || 0} />
                        </div>
                    </div>
                </div>

                {/* Reasoning */}
                {results.reasoning && (
                    <div className="bg-white rounded-xl p-6 border border-blue-100">
                        <p className="text-sm font-medium text-slate-600 mb-2">ANALYSIS REASONING</p>
                        <p className="text-slate-700 leading-relaxed">{results.reasoning}</p>
                    </div>
                )}
            </div>

            {/* Secondary Diagnoses */}
            {results.secondary_diagnoses && results.secondary_diagnoses.length > 0 && (
                <div className="card-premium">
                    <h3 className="text-xl font-bold text-slate-800 mb-4">Alternative Diagnoses</h3>
                    <div className="space-y-3">
                        {results.secondary_diagnoses.map((sec, idx) => (
                            <div key={idx} className="bg-slate-50 rounded-lg p-4 border border-slate-200">
                                <div className="flex items-center justify-between">
                                    <span className="font-medium text-slate-700">{sec.diagnosis}</span>
                                    <span className="text-sm text-slate-600">
                                        {Math.round((sec.confidence || 0) * 100)}% confidence
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* PDF Report Download */}
            <div className="card-premium bg-gradient-to-br from-emerald-50 to-teal-50 border-emerald-200">
                <div className="flex items-start gap-4">
                    <div className="flex-shrink-0">
                        <div className="w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center">
                            <svg className="w-6 h-6 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                            </svg>
                        </div>
                    </div>
                    <div className="flex-1">
                        <h4 className="font-semibold text-slate-800 mb-2">Detailed Report Available</h4>
                        <p className="text-sm text-slate-600 mb-4">
                            Download the complete annotated medical report with evidence markers and AI analysis
                        </p>
                        <a
                            href="/api/report/diagnosis_report.pdf"
                            download
                            className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-emerald-600 to-teal-600 text-white font-semibold rounded-xl hover:from-emerald-700 hover:to-teal-700 transition-all duration-200 shadow-lg hover:shadow-xl"
                        >
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            Download PDF Report
                        </a>
                    </div>
                </div>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-4">
                <button
                    onClick={onReset}
                    className="flex-1 px-6 py-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-semibold rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all duration-200 shadow-lg hover:shadow-xl"
                >
                    Analyze Another Patient
                </button>
            </div>

            {/* Disclaimer */}
            <div className="card-premium bg-amber-50 border-amber-200">
                <div className="flex items-start gap-3">
                    <svg className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    <div className="flex-1">
                        <h4 className="font-semibold text-amber-900 mb-1">Medical Disclaimer</h4>
                        <p className="text-sm text-amber-800 leading-relaxed">
                            This AI-assisted diagnosis is for research and educational purposes only. It should not replace professional medical advice, diagnosis, or treatment. Always consult with a qualified healthcare provider for medical decisions.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    )
}

function ConfidenceGauge({ confidence }) {
    const percentage = Math.round(confidence * 100)
    const circumference = 2 * Math.PI * 40
    const offset = circumference - (circumference * confidence)

    return (
        <div className="relative w-32 h-32">
            <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                {/* Background circle */}
                <circle
                    cx="50"
                    cy="50"
                    r="40"
                    fill="none"
                    stroke="#e2e8f0"
                    strokeWidth="8"
                />
                {/* Progress circle */}
                <circle
                    cx="50"
                    cy="50"
                    r="40"
                    fill="none"
                    stroke="url(#gaugeGradient)"
                    strokeWidth="8"
                    strokeLinecap="round"
                    strokeDasharray={circumference}
                    strokeDashoffset={offset}
                    className="transition-all duration-1000 ease-out"
                />
                <defs>
                    <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stopColor="#10b981" />
                        <stop offset="100%" stopColor="#059669" />
                    </linearGradient>
                </defs>
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-2xl font-bold text-slate-800">{percentage}%</span>
            </div>
        </div>
    )
}
