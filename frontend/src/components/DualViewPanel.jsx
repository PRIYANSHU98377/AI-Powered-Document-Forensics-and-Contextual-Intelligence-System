import React from 'react'
import { AlertCircle, HelpCircle, CheckSquare, Calculator } from 'lucide-react'

export default function DualViewPanel({ suspiciousView, innocentView, recommendedVerification, formulaBreakdown }) {
  return (
    <div className="space-y-3 mt-3">
      {/* Side-by-side Dual View */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {/* Suspicious View */}
        <div className="bg-rose-50/70 border border-rose-200/80 rounded-lg p-3 text-xs">
          <div className="flex items-center gap-1.5 font-bold text-rose-800 mb-1.5">
            <AlertCircle className="w-3.5 h-3.5 text-rose-600 shrink-0" />
            <span>Suspicious View (Potential Manipulation):</span>
          </div>
          <p className="text-slate-700 leading-relaxed">{suspiciousView || "Potential alteration detected by forensic detector."}</p>
        </div>

        {/* Innocent View */}
        <div className="bg-emerald-50/70 border border-emerald-200/80 rounded-lg p-3 text-xs">
          <div className="flex items-center gap-1.5 font-bold text-emerald-800 mb-1.5">
            <HelpCircle className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
            <span>Innocent View (Plausible Benign Reasons):</span>
          </div>
          <p className="text-slate-700 leading-relaxed">{innocentView || "Possible scanner calibration issue, compression artifact, or formatting variation."}</p>
        </div>
      </div>

      {/* Recommended Verification */}
      {recommendedVerification && (
        <div className="bg-blue-50/70 border border-blue-200 rounded-lg p-2.5 text-xs flex items-start gap-2">
          <CheckSquare className="w-3.5 h-3.5 text-blue-600 shrink-0 mt-0.5" />
          <div>
            <strong className="text-blue-900">Recommended Human Verification: </strong>
            <span className="text-slate-700">{recommendedVerification}</span>
          </div>
        </div>
      )}

      {/* Mathematical Breakdown Formula */}
      {formulaBreakdown && (
        <div className="bg-slate-50 border border-slate-200 rounded px-2.5 py-1.5 text-[11px] font-mono text-slate-500 flex items-center gap-1.5">
          <Calculator className="w-3 h-3 text-slate-400 shrink-0" />
          <span>Formula: {formulaBreakdown}</span>
        </div>
      )}
    </div>
  )
}
