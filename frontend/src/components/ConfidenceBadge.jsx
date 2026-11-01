import React from 'react'

export default function ConfidenceBadge({ category, riskLevel, confidence }) {
  // Category colors: OBSERVED (grey), INCONSISTENT (amber), POTENTIAL_MANIPULATION (red)
  let badgeStyle = "bg-slate-100 text-slate-700 border-slate-300"
  let label = category || "OBSERVED"

  if (category === "POTENTIAL_MANIPULATION") {
    badgeStyle = "bg-rose-50 text-rose-700 border-rose-300"
  } else if (category === "INCONSISTENT") {
    badgeStyle = "bg-amber-50 text-amber-700 border-amber-300"
  } else if (category === "OBSERVED") {
    badgeStyle = "bg-slate-100 text-slate-700 border-slate-300"
  }

  return (
    <div className="inline-flex items-center gap-1.5 font-mono text-xs">
      <span className={`px-2 py-0.5 rounded border font-semibold ${badgeStyle}`}>
        {label}
      </span>
      {riskLevel && (
        <span className={`px-1.5 py-0.5 rounded text-[11px] font-bold ${
          riskLevel === "HIGH" ? "bg-rose-600 text-white" :
          riskLevel === "MEDIUM" ? "bg-amber-500 text-white" : "bg-slate-500 text-white"
        }`}>
          {riskLevel}
        </span>
      )}
      {confidence !== undefined && (
        <span className="text-slate-500 text-[11px]">
          ({Math.round(confidence * 100)}%)
        </span>
      )}
    </div>
  )
}
