import React from 'react'
import { CheckCircle2, Loader2, Circle } from 'lucide-react'

const PIPELINE_STAGES = [
  "Document Submission",
  "Classification",
  "OCR & Extraction",
  "Structural Understanding",
  "Visual Forensic Analysis",
  "Contextual Verification",
  "Cross-Document Correlation",
  "Anomaly Investigation",
  "Evidence Generation",
  "Investigation Dossier"
]

export default function ProgressStepper({ currentStage, progressPct, message, isComplete }) {
  const currentStageIndex = PIPELINE_STAGES.findIndex(
    s => currentStage && currentStage.toLowerCase().includes(s.toLowerCase().split(' ')[0])
  )
  const activeIdx = isComplete ? PIPELINE_STAGES.length : (currentStageIndex >= 0 ? currentStageIndex : 1)

  return (
    <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm mb-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-bold text-slate-800">Forensics Processing Pipeline</h3>
          <p className="text-xs text-slate-500">{message || "Processing documents through forensic analyzers..."}</p>
        </div>
        <div className="text-right">
          <span className="text-lg font-mono font-bold text-blue-600">{progressPct}%</span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-slate-100 rounded-full h-2 mb-6 overflow-hidden">
        <div
          className="bg-blue-600 h-2 rounded-full transition-all duration-300"
          style={{ width: `${progressPct}%` }}
        />
      </div>

      {/* Grid of Steps */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {PIPELINE_STAGES.map((stage, idx) => {
          const isDone = isComplete || idx < activeIdx
          const isCurrent = !isComplete && idx === activeIdx

          return (
            <div
              key={stage}
              className={`p-2.5 rounded-lg border text-xs flex items-center gap-2 ${
                isDone
                  ? 'bg-emerald-50 border-emerald-200 text-emerald-800 font-medium'
                  : isCurrent
                  ? 'bg-blue-50 border-blue-300 text-blue-800 font-bold shadow-xs'
                  : 'bg-slate-50 border-slate-200 text-slate-400'
              }`}
            >
              {isDone ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              ) : isCurrent ? (
                <Loader2 className="w-4 h-4 text-blue-600 animate-spin shrink-0" />
              ) : (
                <Circle className="w-4 h-4 text-slate-300 shrink-0" />
              )}
              <span className="truncate">{idx + 1}. {stage}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
