import React, { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Filter, AlertTriangle, ShieldCheck, FileText } from 'lucide-react'
import FindingCard from '../components/FindingCard'

export default function FindingsReview() {
  const { caseId } = useParams()
  const [findings, setFindings] = useState([])
  const [documents, setDocuments] = useState([])
  const [categoryFilter, setCategoryFilter] = useState('ALL')
  const [riskFilter, setRiskFilter] = useState('ALL')
  const [docFilter, setDocFilter] = useState('ALL')
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      fetch(`/api/v1/cases/${caseId}/findings`).then(r => r.json()),
      fetch(`/api/v1/cases/${caseId}/documents`).then(r => r.json())
    ]).then(([fnds, docs]) => {
      setFindings(fnds || [])
      setDocuments(docs || [])
      setIsLoading(false)
    }).catch(console.error)
  }, [caseId])

  const handleReviewUpdate = (findingId, newStatus, notes) => {
    setFindings(prev => prev.map(f => {
      if (f.finding_id === findingId) {
        return { ...f, status: newStatus, reviewer_notes: notes }
      }
      return f
    }))
  }

  const filteredFindings = findings.filter(f => {
    if (categoryFilter !== 'ALL' && f.category !== categoryFilter) return false
    if (riskFilter !== 'ALL' && f.risk_level !== riskFilter) return false
    if (docFilter !== 'ALL' && f.document_id !== docFilter) return false
    return true
  })

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
        <div>
          <div className="flex items-center gap-2 text-xs text-slate-500 font-mono mb-1">
            <Link to={`/case/${caseId}`} className="text-blue-600 hover:underline">← Case Dashboard</Link>
            <span>•</span>
            <span>Case ID: {caseId}</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900">Findings & Anomaly Review</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Balanced Dual-View forensic reasoning, mathematical confidence breakdowns, and reviewer decision logging.
          </p>
        </div>

        <Link
          to={`/case/${caseId}/dossier`}
          className="px-3.5 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg flex items-center gap-1.5 shadow-xs"
        >
          <FileText className="w-4 h-4" />
          <span>Export Case Dossier</span>
        </Link>
      </div>

      {/* Filter Toolbar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs mb-6 flex flex-wrap items-center gap-4 text-xs">
        <div className="flex items-center gap-1.5 font-bold text-slate-700">
          <Filter className="w-4 h-4 text-slate-400" />
          <span>Filters:</span>
        </div>

        {/* Category Filter */}
        <div className="flex items-center gap-1.5">
          <span className="text-slate-500">Category:</span>
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="border border-slate-300 rounded px-2.5 py-1 bg-white text-slate-800"
          >
            <option value="ALL">All Categories</option>
            <option value="POTENTIAL_MANIPULATION">Potential Manipulation</option>
            <option value="INCONSISTENT">Inconsistent</option>
            <option value="OBSERVED">Observed (Neutral)</option>
          </select>
        </div>

        {/* Risk Filter */}
        <div className="flex items-center gap-1.5">
          <span className="text-slate-500">Risk Level:</span>
          <select
            value={riskFilter}
            onChange={(e) => setRiskFilter(e.target.value)}
            className="border border-slate-300 rounded px-2.5 py-1 bg-white text-slate-800"
          >
            <option value="ALL">All Risk Levels</option>
            <option value="HIGH">High Risk</option>
            <option value="MEDIUM">Medium Risk</option>
            <option value="LOW">Low Risk</option>
          </select>
        </div>

        {/* Document Filter */}
        <div className="flex items-center gap-1.5">
          <span className="text-slate-500">Document:</span>
          <select
            value={docFilter}
            onChange={(e) => setDocFilter(e.target.value)}
            className="border border-slate-300 rounded px-2.5 py-1 bg-white text-slate-800"
          >
            <option value="ALL">All Documents</option>
            {documents.map(d => (
              <option key={d.document_id} value={d.document_id}>{d.filename}</option>
            ))}
          </select>
        </div>

        <div className="ml-auto text-slate-500 font-mono text-[11px]">
          Showing {filteredFindings.length} of {findings.length} findings
        </div>
      </div>

      {/* Findings List */}
      {isLoading ? (
        <div className="p-8 text-center text-sm text-slate-500">Loading forensic findings...</div>
      ) : filteredFindings.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 p-12 text-center text-slate-500">
          <ShieldCheck className="w-12 h-12 text-emerald-500 mx-auto mb-3" />
          <h3 className="text-base font-bold text-slate-800">No matching anomalies found</h3>
          <p className="text-xs text-slate-400 mt-1">Try adjusting the filter criteria above.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredFindings.map((f) => (
            <FindingCard
              key={f.finding_id}
              finding={f}
              onReviewUpdate={handleReviewUpdate}
            />
          ))}
        </div>
      )}
    </div>
  )
}
