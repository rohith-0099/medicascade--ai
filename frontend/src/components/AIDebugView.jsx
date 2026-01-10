import React from 'react';
import { AlertCircle, Brain, CheckCircle, XCircle } from 'lucide-react';

const AIDebugView = ({ diagnosisResult }) => {
    if (!diagnosisResult) return null;

    const { layer1_opinions, layer2_validation } = diagnosisResult;

    return (
        <div className="mt-8 space-y-6">
            {/* Layer 1: Individual AI Specialists */}
            <div className="bg-white rounded-lg shadow-lg p-6">
                <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
                    <Brain className="w-6 h-6 text-blue-600" />
                    Layer 1: AI Specialist Analysis
                </h2>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {layer1_opinions && layer1_opinions.map((opinion, idx) => (
                        <div
                            key={idx}
                            className="border-2 rounded-lg p-4 hover:shadow-md transition-shadow"
                            style={{
                                borderColor: opinion.confidence >= 0.7 ? '#10b981' :
                                    opinion.confidence >= 0.5 ? '#f59e0b' : '#ef4444'
                            }}
                        >
                            {/* Specialist Header */}
                            <div className="flex items-center justify-between mb-3">
                                <h3 className="font-bold text-lg capitalize">
                                    {opinion.model_name.replace('_', ' ')}
                                </h3>
                                <div className="flex items-center gap-2">
                                    {opinion.confidence >= 0.5 ? (
                                        <CheckCircle className="w-5 h-5 text-green-600" />
                                    ) : (
                                        <XCircle className="w-5 h-5 text-red-600" />
                                    )}
                                    <span className="font-semibold text-lg">
                                        {(opinion.confidence * 100).toFixed(0)}%
                                    </span>
                                </div>
                            </div>

                            {/* Diagnosis */}
                            <div className="mb-3">
                                <p className="text-sm text-gray-500 font-medium">Diagnosis:</p>
                                <p className="text-gray-900 font-semibold">{opinion.diagnosis}</p>
                            </div>

                            {/* Reasoning */}
                            <div className="mb-3">
                                <p className="text-sm text-gray-500 font-medium">AI Reasoning:</p>
                                <p className="text-sm text-gray-700 italic">
                                    "{opinion.reasoning}"
                                </p>
                            </div>

                            {/* Detected Conditions */}
                            {opinion.detected_conditions && opinion.detected_conditions.length > 0 && (
                                <div>
                                    <p className="text-sm text-gray-500 font-medium mb-1">Detected Conditions:</p>
                                    <div className="flex flex-wrap gap-2">
                                        {opinion.detected_conditions.map((condition, i) => (
                                            <span
                                                key={i}
                                                className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs font-medium"
                                            >
                                                {condition}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Key Findings */}
                            {opinion.key_findings && (
                                <div className="mt-3 pt-3 border-t border-gray-200">
                                    <p className="text-xs text-gray-500 font-medium mb-1">Technical Details:</p>
                                    <pre className="text-xs bg-gray-50 p-2 rounded overflow-x-auto">
                                        {JSON.stringify(opinion.key_findings, null, 2)}
                                    </pre>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            </div>

            {/* Layer 2: Cross-Validation & Reasoning */}
            <div className="bg-gradient-to-br from-purple-50 to-blue-50 rounded-lg shadow-lg p-6">
                <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
                    <AlertCircle className="w-6 h-6 text-purple-600" />
                    Layer 2: AI Cross-Validation
                </h2>

                {layer2_validation ? (
                    <div className="space-y-4">
                        {/* Primary Diagnosis */}
                        <div className="bg-white rounded-lg p-4">
                            <p className="text-sm text-gray-500 font-medium">Primary Diagnosis:</p>
                            <p className="text-2xl font-bold text-gray-900">
                                {layer2_validation.primary_diagnosis}
                            </p>
                            <div className="mt-2 flex items-center gap-2">
                                <div className="flex-1 bg-gray-200 rounded-full h-3">
                                    <div
                                        className="bg-gradient-to-r from-blue-500 to-purple-600 h-3 rounded-full transition-all"
                                        style={{ width: `${layer2_validation.confidence * 100}%` }}
                                    />
                                </div>
                                <span className="font-bold text-lg">
                                    {(layer2_validation.confidence * 100).toFixed(0)}%
                                </span>
                            </div>
                        </div>

                        {/* AI Reasoning */}
                        <div className="bg-white rounded-lg p-4">
                            <p className="text-sm text-gray-500 font-medium mb-2">AI Reasoning Process:</p>
                            <p className="text-gray-700 leading-relaxed">
                                {layer2_validation.reasoning}
                            </p>
                        </div>

                        {/* Cross-Validation Score */}
                        <div className="bg-white rounded-lg p-4">
                            <p className="text-sm text-gray-500 font-medium mb-2">Cross-Validation Score:</p>
                            <div className="flex items-center gap-4">
                                <div className="flex-1 bg-gray-200 rounded-full h-4">
                                    <div
                                        className="bg-green-500 h-4 rounded-full"
                                        style={{ width: `${layer2_validation.cross_validation_score * 100}%` }}
                                    />
                                </div>
                                <span className="font-bold">
                                    {(layer2_validation.cross_validation_score * 100).toFixed(1)}%
                                </span>
                            </div>
                            <p className="text-xs text-gray-500 mt-1">
                                Agreement between {layer2_validation.num_specialists_used || 'multiple'} specialist AI models
                            </p>
                        </div>

                        {/* Anomaly Detection */}
                        {layer2_validation.anomaly_detected && (
                            <div className="bg-yellow-50 border-2 border-yellow-400 rounded-lg p-4">
                                <div className="flex items-start gap-3">
                                    <AlertCircle className="w-6 h-6 text-yellow-600 flex-shrink-0 mt-1" />
                                    <div>
                                        <p className="font-bold text-yellow-900">Unusual Pattern Detected</p>
                                        <p className="text-sm text-yellow-800 mt-1">
                                            {layer2_validation.anomaly_message}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Conflicts */}
                        {layer2_validation.conflicts && layer2_validation.conflicts !== "None" && (
                            <div className="bg-red-50 border-2 border-red-300 rounded-lg p-4">
                                <p className="font-bold text-red-900 mb-2">Model Conflicts Detected:</p>
                                <p className="text-sm text-red-800">{layer2_validation.conflicts}</p>
                            </div>
                        )}
                    </div>
                ) : (
                    <p className="text-gray-500 italic">Layer 2 validation not available</p>
                )}
            </div>

            {/* Raw Data Inspector (for debugging) */}
            <details className="bg-gray-100 rounded-lg p-4">
                <summary className="cursor-pointer font-bold text-gray-700 hover:text-gray-900">
                    🔍 Raw API Response (Developer View)
                </summary>
                <pre className="mt-4 bg-white p-4 rounded text-xs overflow-x-auto border border-gray-300">
                    {JSON.stringify(diagnosisResult, null, 2)}
                </pre>
            </details>
        </div>
    );
};

export default AIDebugView;
