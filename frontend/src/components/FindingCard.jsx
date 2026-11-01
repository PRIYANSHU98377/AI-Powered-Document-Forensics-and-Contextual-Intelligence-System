import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ExternalLink, Check, X, AlertCircle, MessageSquare } from 'lucide-react'
import ConfidenceBadge from './ConfidenceBadge'
import DualViewPanel from './DualViewPanel'
import EvidenceCrop from './EvidenceCrop'

export default function FindingCard({ finding, onReviewUpdate }) {
  const navigate = useNavigate()
  const [reviewStatus, setReviewStatus] = useState(finding.status || 'PENDING')
  const [notes, setNotes] = useState(finding.reviewer_notes || '')
  const [showNotesInput, setShowNotesInput] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleReview = async (newStatus) => {
    setIsSubmitting(true)
    try {
      const res = await fetch(`/api/v1/findings/${finding.finding_id}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus, reviewer_notes: notes })
      })
      if (res.ok) {
        setReviewStatus(newStatus)
        if (onReviewUpdate) onReviewUpdate(finding.finding_id, newStatus, notes)
      }
    } catch (e) {
      console.error("Failed to update review", e)
    } finally {
      setIsSubmitting(false)
    }
  }

  const cropUrl = finding.evidence_id ? `/api/v1/evidence/${finding.evidence_id}/crop` : null
  const overlayUrl = finding.evidence_id ? `/api/v1/evidence/${finding.evidence_id}/overlay` : null

  return (
    <div className={`border rounded-xl p-5 mb-4 shadow-xs transition-all bg-white ${
      finding.category === 'POTENTIAL_MANIPULATION' ? 'border-rose-300 ring-1 ring-rose-100' :
      finding.category === 'INCONSISTENT' ? 'border-amber-300 ring-1 ring-amber-100' : 'border-slate-200'
    }`}>
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
        <div>
          <div className="flex items-center gap-2">
            <h4 className="text-base font-bold text-slate-900">{finding.title}</h4>
            <span className="font-mono text-xs text-slate-400">#{finding.finding_id.slice(-6)}</span>
          </div>
          <div className="text-xs text-slate-500 mt-0.5">
            Document: <span className="font-mono text-slate-700">{finding.document_id}</span> | Page {finding.page} | Detector: <span className="font-semibold text-slate-700">{finding.detector}</span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <ConfidenceBadge
            category={finding.category}
            riskLevel={finding.risk_level}
            confidence={finding.confidence}
          />
          <button
            onClick={() => navigate(`/case/${finding.case_id}/viewer?doc=${finding.document_id}&page=${finding.page}&fnd=${finding.finding_id}`)}
            className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800 font-semibold px-2.5 py-1 rounded-md bg-blue-50 border border-blue-200 hover:bg-blue-100 transition-colors"
          >
            <ExternalLink className="w-3.5 h-3.5" />
            <span>Trace to Source</span>
          </button>
        </div>
      </div>

      {/* Main Grid: Observation & Evidence Crop */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-3">
        <div className="md:col-span-2 space-y-2">
          <div className="text-xs leading-relaxed text-slate-800">
            <strong className="text-slate-900">Observed Characteristic: </strong>
            {finding.observation}
          </div>
          {finding.technical_details && (
            <div className="text-[11px] font-mono text-slate-500 bg-slate-50 p-2 rounded border border-slate-200">
              {finding.technical_details}
            </div>
          )}
        </div>

        <div>
          <EvidenceCrop
            evidenceId={finding.evidence_id}
            cropUrl={cropUrl}
            overlayUrl={overlayUrl}
            detector={finding.detector}
            score={finding.confidence}
          />
        </div>
      </div>

      {/* Dual-View Reasoning Component */}
      <DualViewPanel
        suspiciousView={finding.suspicious_view}
        innocentView={finding.innocent_view}
        recommendedVerification={finding.recommended_verification}
        formulaBreakdown={finding.formula_breakdown}
      />

      {/* Human-in-the-Loop Review Actions */}
      <div className="mt-4 pt-3 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-slate-600">Review Decision:</span>
          <span className={`px-2 py-0.5 rounded font-bold text-[11px] ${
            reviewStatus === 'CONFIRMED' ? 'bg-emerald-100 text-emerald-800 border border-emerald-300' :
            reviewStatus === 'DISMISSED' ? 'bg-slate-200 text-slate-700' :
            reviewStatus === 'NEEDS_INFO' ? 'bg-amber-100 text-amber-800' : 'bg-slate-100 text-slate-500'
          }`}>
            {reviewStatus}
          </span>
          {finding.reviewer_notes && (
            <span className="text-slate-500 italic ml-2">"{finding.reviewer_notes}"</span>
          )}
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => handleReview('CONFIRMED')}
            disabled={isSubmitting}
            className={`px-2.5 py-1 rounded text-xs font-semibold flex items-center gap-1 transition-colors ${
              reviewStatus === 'CONFIRMED'
                ? 'bg-emerald-700 text-white'
                : 'bg-emerald-50 text-emerald-700 border border-emerald-300 hover:bg-emerald-100'
            }`}
          >
            <Check className="w-3 h-3" />
            <span>Confirm Anomaly</span>
          </button>

          <button
            onClick={() => handleReview('DISMISSED')}
            disabled={isSubmitting}
            className={`px-2.5 py-1 rounded text-xs font-semibold flex items-center gap-1 transition-colors ${
              reviewStatus === 'DISMISSED'
                ? 'bg-slate-700 text-white'
                : 'bg-slate-100 text-slate-700 border border-slate-300 hover:bg-slate-200'
            }`}
          >
            <X className="w-3 h-3" />
            <span>Dismiss (Benign)</span>
          </button>

          <button
            onClick={() => handleReview('NEEDS_INFO')}
            disabled={isSubmitting}
            className={`px-2.5 py-1 rounded text-xs font-semibold flex items-center gap-1 transition-colors ${
              reviewStatus === 'NEEDS_INFO'
                ? 'bg-amber-700 text-white'
                : 'bg-amber-50 text-amber-700 border border-amber-300 hover:bg-amber-100'
            }`}
          >
            <AlertCircle className="w-3 h-3" />
            <span>Needs Info</span>
          </button>

          <button
            onClick={() => setShowNotesInput(!showNotesInput)}
            className="p-1 rounded text-slate-500 hover:text-slate-800 hover:bg-slate-100"
            title="Add reviewer notes"
          >
            <MessageSquare className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Reviewer Notes Expansion */}
      {showNotesInput && (
        <div className="mt-3 pt-2 border-t border-slate-100">
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Add forensic reviewer observations or action notes..."
            className="w-full text-xs p-2 border border-slate-200 rounded focus:ring-1 focus:ring-blue-500 outline-hidden"
            rows={2}
          />
          <div className="text-right mt-1">
            <button
              onClick={() => handleReview(reviewStatus)}
              className="text-xs bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded"
            >
              Save Notes to Audit Chain
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
