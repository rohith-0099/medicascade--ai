import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'

export default function ResultsDashboard({ results, onReset }) {
    const diagnosis = results.layer2_diagnosis
    const layer1 = results.layer1_output
    const layer3 = results.layer3_report
    const patient = results.patient_data

    // Prepare confidence data
    const confidenceData = [
        { name: 'Primary', value: diagnosis.confidence * 100, color: '#3b82f6' },
        ...(diagnosis.secondary_diagnoses || []).map((sec, i) => ({
            name: `Alt ${i + 1}`,
            value: sec.confidence * 100,
            color: ['#8b5cf6', '#ec4899', '#f59e0b'][i] || '#64748b'
        }))
    ]

    const getConfidenceColor = (conf) => {
        if (conf >= 0.8) return 'text-emerald-600'
        if (conf >= 0.6) return 'text-blue-600'
        return 'text-amber-600'
    }

    const getConfidenceBadge = (conf) => {
        if (conf >= 0.8) return 'badge-success'
        if (conf >= 0.6) return 'badge-info'
        return 'badge-warning'
    }

    return (
        <div className="space-y-6">
            {/* Header Actions */}
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div>
                    <h2 className="text-4xl font-bold text-slate-800">Diagnosis Report</h2>
                    <p className="text-slate-500 mt-1">AI-powered multi-layer analysis complete</p>
                </div>
                <div className="flex gap-3">
                    {layer3.annotated_pdf_path && (
                        <a
                            href={`/api/report/diagnosis_report.pdf`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="btn-secondary inline-flex items-center gap-2"
                        >
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            Download Report
                        </a>
                    )}
                    <button onClick={onReset} className="btn-primary">
                        New Analysis
                    </button>
                </div>
            </div>

            {/* Primary Diagnosis Card */}
            <div className="card-premium bg-gradient-to-br from-blue-50 via-white to-indigo-50 border-blue-200">
                <div className="flex items-start justify-between mb-6">
                    <div className="flex items-center gap-4">
                        <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-indigo-500 rounded-2xl flex items-center justify-center shadow-lg">
                            <svg className="w-9 h-9 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                        </div>
                        <div>
                            <span className={`medical-badge ${getConfidenceBadge(diagnosis.confidence)} text-base`}>
                                Primary Diagnosis
                            </span>
                        </div>
                    </div>
                    <div className="text-right">
                        <div className={`text-5xl font-bold ${getConfidenceColor(diagnosis.confidence)}`}>
                            {(diagnosis.confidence * 100).toFixed(0)}%
                        </div>
                        <div className="text-sm text-slate-500 font-medium mt-1">Confidence</div>
                    </div>
                </div>

                <h3 className="text-4xl font-bold text-slate-800 mb-4">{diagnosis.primary_diagnosis}</h3>
                <p className="text-slate-600 leading-relaxed text-lg">{diagnosis.reasoning}</p>

                {/* Anomaly Warning */}
                {diagnosis.anomaly_detected && (
                    <div className="mt-6 bg-amber-50 border-2 border-amber-200 rounded-xl p-5">
                        <div className="flex items-start gap-3">
                            <svg className="w-7 h-7 text-amber-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                            </svg>
                            <div>
                                <h4 className="font-bold text-amber-900 mb-1">Anomaly Detected</h4>
                                <p className="text-amber-800">{diagnosis.anomaly_description}</p>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="stat-card">
                    <div className="text-3xl font-bold text-blue-600 mb-1">{layer1.specialist_opinions.length}</div>
                    <div className="text-sm font-medium text-slate-600">AI Specialists</div>
                    <div className="text-xs text-slate-400 mt-1">Parallel analysis</div>
                </div>
                <div className="stat-card">
                    <div className="text-3xl font-bold text-indigo-600 mb-1">{(diagnosis.cross_validation_score * 100).toFixed(0)}%</div>
                    <div className="text-sm font-medium text-slate-600">Cross-Validation</div>
                    <div className="text-xs text-slate-400 mt-1">Agreement score</div>
                </div>
                <div className="stat-card">
                    <div className="text-3xl font-bold text-emerald-600 mb-1">{results.total_processing_time.toFixed(1)}s</div>
                    <div className="text-sm font-medium text-slate-600">Processing Time</div>
                    <div className="text-xs text-slate-400 mt-1">Total duration</div>
                </div>
            </div>

            {/* Two Column Layout */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Left Column */}
                <div className="space-y-6">
                    {/* Specialist Opinions */}
                    <div className="card">
                        <h3 className="text-2xl font-bold text-slate-800 mb-5 flex items-center gap-2">
                            <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                            </svg>
                            AI Specialist Opinions
                        </h3>
                        <div className="space-y-3">
                            {layer1.specialist_opinions.map((opinion, idx) => (
                                <div key={idx} className="bg-gradient-to-r from-slate-50 to-blue-50 rounded-xl p-5 border border-slate-200 hover:border-blue-300 transition-all">
                                    <div className="flex justify-between items-start mb-3">
                                        <span className="medical-badge badge-info text-xs">
                                            {opinion.model_name.replace('_analyzer', '').replace('_', ' ').toUpperCase()}
                                        </span>
                                        <span className="text-lg font-bold text-blue-600">
                                            {(opinion.confidence * 100).toFixed(0)}%
                                        </span>
                                    </div>
                                    <p className="text-slate-700 font-medium mb-2">{opinion.diagnosis}</p>
                                    {opinion.detected_conditions && opinion.detected_conditions.length > 0 && (
                                        <div className="flex flex-wrap gap-2 mt-3">
                                            {opinion.detected_conditions.slice(0, 3).map((cond, i) => (
                                                <span key={i} className="px-3 py-1 bg-white rounded-lg text-xs font-medium text-slate-600 border border-slate-200">
                                                    {cond}
                                                </span>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Right Column */}
                <div className="space-y-6">
                    {/* Evidence */}
                    <div className="card">
                        <h3 className="text-2xl font-bold text-slate-800 mb-5 flex items-center gap-2">
                            <svg className="w-6 h-6 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            Supporting Evidence
                        </h3>
                        <div className="space-y-3">
                            {layer3.evidence_items && layer3.evidence_items.map((evidence, idx) => (
                                <div key={idx} className="bg-gradient-to-r from-amber-50 to-yellow-50 border border-amber-200 rounded-xl p-4">
                                    <div className="flex items-start gap-3">
                                        <svg className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                                            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                                        </svg>
                                        <div className="flex-1">
                                            <div className="text-xs text-amber-700 font-bold mb-1 uppercase tracking-wide">
                                                {evidence.location}
                                            </div>
                                            <p className="text-sm text-slate-700 leading-relaxed">{evidence.text}</p>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Patient Info */}
                    {patient.patient_info && Object.keys(patient.patient_info).length > 0 && (
                        <div className="card">
                            <h3 className="text-2xl font-bold text-slate-800 mb-5">Patient Information</h3>
                            <div className="grid grid-cols-2 gap-4">
                                {Object.entries(patient.patient_info).map(([key, value]) => (
                                    value && (
                                        <div key={key} className="bg-slate-50 rounded-lg p-3">
                                            <div className="text-xs text-slate-500 uppercase tracking-wide mb-1">
                                                {key.replace('_', ' ')}
                                            </div>
                                            <div className="font-semibold text-slate-700">{value}</div>
                                        </div>
                                    )
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Full Explanation */}
            <div className="card-premium">
                <h3 className="text-2xl font-bold text-slate-800 mb-5 flex items-center gap-2">
                    <svg className="w-6 h-6 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    Clinical Explanation
                </h3>
                <div className="prose prose-slate max-w-none">
                    <p className="text-slate-700 whitespace-pre-line leading-relaxed text-lg">
                        {layer3.explanation_text}
                    </p>
                </div>
            </div>

            {/* Disclaimer */}
            <div className="card bg-slate-50 border-slate-300">
                <div className="flex items-start gap-4">
                    <svg className="w-6 h-6 text-amber-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    <div>
                        <h4 className="font-bold text-slate-800 mb-2">Medical Disclaimer</h4>
                        <p className="text-sm text-slate-600 leading-relaxed">
                            This AI-generated analysis should be reviewed by qualified medical professionals.
                            It is not a substitute for professional medical advice, diagnosis, or treatment.
                            Always consult with a healthcare provider for medical decisions.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    )
}
