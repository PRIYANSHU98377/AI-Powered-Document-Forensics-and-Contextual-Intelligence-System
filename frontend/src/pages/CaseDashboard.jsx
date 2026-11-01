import React, { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Shield, AlertTriangle, FileText, CheckCircle2, GitFork, ExternalLink, ArrowRight } from 'lucide-react'
import ConfidenceBadge from '../components/ConfidenceBadge'

export default function CaseDashboard() {
  const { caseId } = useParams()
  const [caseInfo, setCaseInfo] = useState(null)
  const [documents, setDocuments] = useState([])
  const [findings, setFindings] = useState([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      fetch(`/api/v1/cases/${caseId}`).then(r => r.json()),
      fetch(`/api/v1/cases/${caseId}/documents`).then(r => r.json()),
      fetch(`/api/v1/cases/${caseId}/findings`).then(r => r.json())
    ]).then(([c, d, f]) => {
      setCaseInfo(c)
      setDocuments(d || [])
      setFindings(f || [])
      setIsLoading(false)
    }).catch(err => {
      console.error(err)
      setIsLoading(false)
    })
  }, [caseId])

  if (isLoading) {
    return <div className="p-8 text-center text-sm text-slate-500">Loading case intelligence...</div>
  }

  const manipCount = findings.filter(f => f.category === 'POTENTIAL_MANIPULATION').length
  const inconsistCount = findings.filter(f => f.category === 'INCONSISTENT').length
  const observedCount = findings.filter(f => f.category === 'OBSERVED').length

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Top Banner */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs mb-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs text-slate-500 font-mono mb-1">
            <span>CASE ID: {caseId}</span>
            <span>•</span>
            <span>Created {caseInfo?.created_at?.slice(0, 10)}</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900">{caseInfo?.name || "Investigation Case"}</h1>
          <p className="text-xs text-slate-600 mt-1">{caseInfo?.description}</p>
        </div>

        <div className="flex items-center gap-3 bg-slate-50 px-4 py-3 rounded-xl border border-slate-200">
          <div>
            <div className="text-[10px] uppercase font-bold text-slate-400">Overall Case Risk</div>
            <div className="text-lg font-extrabold text-slate-900 flex items-center gap-1.5">
              <span className={`inline-block w-3 h-3 rounded-full ${
                caseInfo?.overall_risk === 'HIGH' ? 'bg-rose-600 animate-pulse' :
                caseInfo?.overall_risk === 'MEDIUM' ? 'bg-amber-500' : 'bg-emerald-500'
              }`} />
              <span>{caseInfo?.overall_risk || 'LOW'}</span>
            </div>
          </div>
          <Link
            to={`/case/${caseId}/dossier`}
            className="ml-4 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg flex items-center gap-1"
          >
            <FileText className="w-3.5 h-3.5" />
            <span>View Dossier</span>
          </Link>
        </div>
      </div>

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white p-4 rounded-xl border border-slate-200">
          <div className="text-xs text-slate-500 font-medium">Total Documents</div>
          <div className="text-2xl font-extrabold text-slate-900 mt-1">{documents.length}</div>
          <div className="text-[11px] text-slate-400 mt-1">Multi-format ingested</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-rose-200 bg-rose-50/20">
          <div className="text-xs text-rose-700 font-medium">Potential Manipulations</div>
          <div className="text-2xl font-extrabold text-rose-700 mt-1">{manipCount}</div>
          <div className="text-[11px] text-rose-600 mt-1">Requires urgent review</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-amber-200 bg-amber-50/20">
          <div className="text-xs text-amber-700 font-medium">Detected Inconsistencies</div>
          <div className="text-2xl font-extrabold text-amber-700 mt-1">{inconsistCount}</div>
          <div className="text-[11px] text-amber-600 mt-1">Cross-check rule failures</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200">
          <div className="text-xs text-slate-500 font-medium">Total Forensic Signals</div>
          <div className="text-2xl font-extrabold text-slate-900 mt-1">{findings.length}</div>
          <div className="text-[11px] text-slate-400 mt-1">{observedCount} neutral characteristics</div>
        </div>
      </div>

      {/* Quick Navigation Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <Link
          to={`/case/${caseId}/viewer`}
          className="p-4 rounded-xl bg-white border border-slate-200 hover:border-blue-400 hover:shadow-xs transition-all group"
        >
          <div className="flex items-center justify-between">
            <span className="font-bold text-sm text-slate-800 group-hover:text-blue-600">Document Viewer</span>
            <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-blue-600 transition-transform group-hover:translate-x-1" />
          </div>
          <p className="text-xs text-slate-500 mt-1">Inspect page canvas, toggle ELA overlays, and view double-OCR bounding boxes.</p>
        </Link>

        <Link
          to={`/case/${caseId}/findings`}
          className="p-4 rounded-xl bg-white border border-slate-200 hover:border-blue-400 hover:shadow-xs transition-all group"
        >
          <div className="flex items-center justify-between">
            <span className="font-bold text-sm text-slate-800 group-hover:text-blue-600">Findings Review ({findings.length})</span>
            <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-blue-600 transition-transform group-hover:translate-x-1" />
          </div>
          <p className="text-xs text-slate-500 mt-1">Dual-view suspicious vs innocent breakdown with reviewer confirm/dismiss actions.</p>
        </Link>

        <Link
          to={`/case/${caseId}/graph`}
          className="p-4 rounded-xl bg-white border border-slate-200 hover:border-blue-400 hover:shadow-xs transition-all group"
        >
          <div className="flex items-center justify-between">
            <span className="font-bold text-sm text-slate-800 group-hover:text-blue-600">Cross-Doc Entity Graph</span>
            <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-blue-600 transition-transform group-hover:translate-x-1" />
          </div>
          <p className="text-xs text-slate-500 mt-1">Explore relationship network between documents, identities, accounts, and addresses.</p>
        </Link>
      </div>

      {/* Ingested Documents Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs mb-8 overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-200 flex justify-between items-center">
          <h3 className="font-bold text-sm text-slate-900">Ingested Case Documents</h3>
          <span className="text-xs text-slate-400">{documents.length} files</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 border-b border-slate-200 font-medium">
              <tr>
                <th className="py-2.5 px-4">Filename</th>
                <th className="py-2.5 px-4">Classified Type</th>
                <th className="py-2.5 px-4">Type Confidence</th>
                <th className="py-2.5 px-4">SHA-256 Digest</th>
                <th className="py-2.5 px-4">Pages</th>
                <th className="py-2.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {documents.map((d) => (
                <tr key={d.document_id} className="hover:bg-slate-50/70 transition-colors">
                  <td className="py-3 px-4 font-semibold text-slate-900">{d.filename}</td>
                  <td className="py-3 px-4">
                    <span className="bg-slate-100 px-2 py-0.5 rounded font-mono text-[11px] text-slate-700 border border-slate-200">
                      {d.doc_type}
                    </span>
                  </td>
                  <td className="py-3 px-4 font-mono">{Math.round(d.doc_type_confidence * 100)}%</td>
                  <td className="py-3 px-4 font-mono text-slate-400 text-[11px]">
                    {d.sha256_hash?.slice(0, 16)}...
                  </td>
                  <td className="py-3 px-4">{d.page_count}</td>
                  <td className="py-3 px-4 text-right">
                    <Link
                      to={`/case/${caseId}/viewer?doc=${d.document_id}`}
                      className="text-blue-600 hover:text-blue-800 font-semibold inline-flex items-center gap-1"
                    >
                      <span>Inspect</span>
                      <ExternalLink className="w-3 h-3" />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
