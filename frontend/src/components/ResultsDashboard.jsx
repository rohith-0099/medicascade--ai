import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'

export default function ResultsDashboard({ results, onReset }) {
    const diagnosis = results.layer2_diagnosis
    const layer1 = results.layer1_output
    const layer3 = results.layer3_report
    const patient = results.patient_data

    // Prepare confidence data for chart
    const confidenceData = [
        { name: 'Primary', value: diagnosis.confidence * 100, color: '#0ea5e9' },
        ...(diagnosis.secondary_diagnoses || []).map((sec, i) => ({
            name: `Alt ${i + 1}`,
            value: sec.confidence * 100,
            color: ['#6366f1', '#8b5cf6', '#ec4899'][i] || '#6b7280'
        }))
    ]

    // Specialist opinions data
    const specialistData = layer1.specialist_opinions.map(op => ({
        name: op.model_name.replace('_analyzer', '').replace('_', ' '),
        confidence: op.confidence * 100
    }))

    return (
        <div className="space-y-6">
            {/* Header with Actions */}
            <div className="flex justify-between items-center">
                <h2 className="text-3xl font-bold">Diagnosis Report</h2>
                <div className="flex gap-3">
                    {layer3.annotated_pdf_path && (
                        <a
                            href={`/api/report/diagnosis_report.pdf`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="btn-secondary"
                        >
                            <svg className="w-5 h-5 mr-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            Download PDF
                        </a>
                    )}
                    <button onClick={onReset} className="btn-secondary">
                        New Diagnosis
                    </button>
                </div>
            </div>

            {/* Primary Diagnosis Card */}
            <div className="card bg-gradient-to-r from-primary-900/50 to-primary-800/50 border-primary-500/30">
                <div className="flex items-start justify-between">
                    <div>
                        <div className="flex items-center gap-3 mb-3">
                            <span className="badge badge-success text-lg px-4 py-2">
                                Primary Diagnosis
                            </span>
                            <span className="text-3xl font-bold">
                                {(diagnosis.confidence * 100).toFixed(0)}%
                            </span>
                        </div>
                        <h3 className="text-3xl font-bold mb-4">{diagnosis.primary_diagnosis}</h3>
                        <p className="text-slate-300 leading-relaxed max-w-3xl">
                            {diagnosis.reasoning}
                        </p>
                    </div>
                </div>

                {/* Anomaly Warning */}
                {diagnosis.anomaly_detected && (
                    <div className="mt-6 bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
                        <div className="flex items-start">
                            <svg className="w-6 h-6 text-yellow-500 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                            </svg>
                            <div>
                                <h4 className="font-semibold text-yellow-500 mb-1">Anomaly Detected</h4>
                                <p className="text-sm text-yellow-200">{diagnosis.anomaly_description}</p>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* Two Column Layout */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Left Column */}
                <div className="space-y-6">
                    {/* Confidence Breakdown */}
                    <div className="card">
                        <h3 className="text-xl font-bold mb-4">Confidence Breakdown</h3>
                        <ResponsiveContainer width="100%" height={200}>
                            <BarChart data={confidenceData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                <XAxis dataKey="name" stroke="#94a3b8" />
                                <YAxis stroke="#94a3b8" />
                                <Tooltip
                                    contentStyle={{
                                        backgroundColor: '#1e293b',
                                        border: '1px solid #475569',
                                        borderRadius: '0.5rem'
                                    }}
                                />
                                <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                                    {confidenceData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.color} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>

                    {/* Layer 1 Specialist Opinions */}
                    <div className="card">
                        <h3 className="text-xl font-bold mb-4">AI Specialist Opinions</h3>
                        <div className="space-y-3">
                            {layer1.specialist_opinions.map((opinion, idx) => (
                                <div key={idx} className="bg-slate-700/50 rounded-lg p-4">
                                    <div className="flex justify-between items-start mb-2">
                                        <span className="font-semibold text-sm text-primary-400">
                                            {opinion.model_name.replace('_', ' ').toUpperCase()}
                                        </span>
                                        <span className="text-sm font-bold">
                                            {(opinion.confidence * 100).toFixed(0)}%
                                        </span>
                                    </div>
                                    <p className="text-sm text-slate-300 mb-2">{opinion.diagnosis}</p>
                                    {opinion.detected_conditions && opinion.detected_conditions.length > 0 && (
                                        <div className="flex flex-wrap gap-2">
                                            {opinion.detected_conditions.slice(0, 3).map((cond, i) => (
                                                <span key={i} className="text-xs px-2 py-1 bg-slate-600 rounded-full">
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
                        <h3 className="text-xl font-bold mb-4">Supporting Evidence</h3>
                        <div className="space-y-3">
                            {layer3.evidence_items && layer3.evidence_items.map((evidence, idx) => (
                                <div key={idx} className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
                                    <div className="flex items-start">
                                        <svg className="w-5 h-5 text-yellow-500 mr-2 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                        </svg>
                                        <div className="flex-1">
                                            <div className="text-xs text-yellow-500 font-semibold mb-1">
                                                {evidence.location}
                                            </div>
                                            <p className="text-sm text-slate-200">{evidence.text}</p>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Patient Info */}
                    {patient.patient_info && Object.keys(patient.patient_info).length > 0 && (
                        <div className="card">
                            <h3 className="text-xl font-bold mb-4">Patient Information</h3>
                            <div className="grid grid-cols-2 gap-4">
                                {Object.entries(patient.patient_info).map(([key, value]) => (
                                    value && (
                                        <div key={key}>
                                            <div className="text-xs text-slate-400 uppercase mb-1">
                                                {key.replace('_', ' ')}
                                            </div>
                                            <div className="font-semibold">{value}</div>
                                        </div>
                                    )
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Processing Stats */}
                    <div className="card bg-slate-700/30">
                        <h3 className="text-lg font-bold mb-3">Processing Stats</h3>
                        <div className="space-y-2 text-sm">
                            <div className="flex justify-between">
                                <span className="text-slate-400">Total Time:</span>
                                <span className="font-semibold">{results.total_processing_time.toFixed(2)}s</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-slate-400">Specialists Run:</span>
                                <span className="font-semibold">{layer1.specialist_opinions.length}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-slate-400">Cross-Validation:</span>
                                <span className="font-semibold">{(diagnosis.cross_validation_score * 100).toFixed(0)}%</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Full Explanation */}
            <div className="card">
                <h3 className="text-xl font-bold mb-4">Clinical Explanation</h3>
                <div className="prose prose-invert max-w-none">
                    <p className="text-slate-300 whitespace-pre-line leading-relaxed">
                        {layer3.explanation_text}
                    </p>
                </div>
            </div>

            {/* Disclaimer */}
            <div className="card bg-slate-700/30 border-slate-600">
                <div className="flex items-start">
                    <svg className="w-6 h-6 text-yellow-500 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    <div>
                        <h4 className="font-semibold mb-2">Medical Disclaimer</h4>
                        <p className="text-sm text-slate-400">
                            This AI-generated diagnosis should be reviewed by qualified medical professionals.
                            It is not a substitute for professional medical advice, diagnosis, or treatment.
                            Always consult with a healthcare provider for medical decisions.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    )
}
