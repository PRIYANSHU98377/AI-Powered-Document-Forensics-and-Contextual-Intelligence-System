import React, { useState, useEffect } from 'react'
import { useParams, useSearchParams, Link } from 'react-router-dom'
import { ChevronLeft, ChevronRight, FileSearch, CheckCircle, AlertTriangle, Layers, Info } from 'lucide-react'
import BBoxOverlay from '../components/BBoxOverlay'
import ConfidenceBadge from '../components/ConfidenceBadge'

export default function DocumentViewer() {
  const { caseId } = useParams()
  const [searchParams, setSearchParams] = useSearchParams()
  
  const [documents, setDocuments] = useState([])
  const [activeDocId, setActiveDocId] = useState(searchParams.get('doc') || '')
  const [currentPage, setCurrentPage] = useState(parseInt(searchParams.get('page') || '1', 10))
  const [fields, setFields] = useState([])
  const [findings, setFindings] = useState([])
  const [highlightId, setHighlightId] = useState(searchParams.get('fnd') || null)
  const [activeTab, setActiveTab] = useState('fields') // 'fields' | 'findings'

  // Load documents
  useEffect(() => {
    fetch(`/api/v1/cases/${caseId}/documents`)
      .then(r => r.json())
      .then(docs => {
        setDocuments(docs || [])
        if (!activeDocId && docs && docs.length > 0) {
          setActiveDocId(docs[0].document_id)
        }
      })
      .catch(console.error)
  }, [caseId])

  // Load document fields & findings
  useEffect(() => {
    if (!activeDocId) return

    Promise.all([
      fetch(`/api/v1/documents/${activeDocId}/fields`).then(r => r.json()),
      fetch(`/api/v1/cases/${caseId}/findings?document_id=${activeDocId}`).then(r => r.json())
    ]).then(([flds, fnds]) => {
      setFields(flds || [])
      setFindings(fnds || [])
    }).catch(console.error)
  }, [activeDocId, caseId])

  const activeDoc = documents.find(d => d.document_id === activeDocId)
  const imageUrl = activeDocId ? `/api/v1/documents/${activeDocId}/pages/${currentPage}/image` : null

  const handleBoxClick = (type, item) => {
    if (type === 'field') {
      setHighlightId(item.field_id)
      setActiveTab('fields')
    } else {
      setHighlightId(item.finding_id)
      setActiveTab('findings')
    }
  }

  return (
    <div className="h-[calc(100vh-6rem)] flex flex-col overflow-hidden bg-slate-100">
      {/* Top Document Switcher Bar */}
      <div className="bg-white border-b border-slate-200 px-6 py-2.5 flex items-center justify-between text-xs shrink-0">
        <div className="flex items-center gap-3">
          <Link to={`/case/${caseId}`} className="text-blue-600 font-semibold hover:underline">
            ← Case Dashboard
          </Link>
          <span className="text-slate-300">|</span>
          <span className="font-semibold text-slate-700">Document:</span>
          <select
            value={activeDocId}
            onChange={(e) => {
              setActiveDocId(e.target.value)
              setCurrentPage(1)
              setHighlightId(null)
            }}
            className="border border-slate-300 rounded px-2.5 py-1 text-xs bg-white text-slate-800 font-medium"
          >
            {documents.map((d) => (
              <option key={d.document_id} value={d.document_id}>
                {d.filename} ({d.doc_type})
              </option>
            ))}
          </select>
        </div>

        {/* Page Switcher */}
        {activeDoc && activeDoc.page_count > 1 && (
          <div className="flex items-center gap-2">
            <button
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage <= 1}
              className="p-1 rounded border border-slate-200 hover:bg-slate-50 disabled:opacity-40"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
            </button>
            <span className="font-mono text-xs">
              Page {currentPage} of {activeDoc.page_count}
            </span>
            <button
              onClick={() => setCurrentPage(p => Math.min(activeDoc.page_count, p + 1))}
              disabled={currentPage >= activeDoc.page_count}
              className="p-1 rounded border border-slate-200 hover:bg-slate-50 disabled:opacity-40"
            >
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        )}
      </div>

      {/* Main Workspace Split */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left / Center: Interactive BBox Overlay Viewport */}
        <div className="flex-1 p-3 overflow-hidden">
          {imageUrl ? (
            <BBoxOverlay
              imageUrl={imageUrl}
              fields={fields.filter(f => f.page === currentPage)}
              findings={findings.filter(f => f.page === currentPage)}
              activeHighlightId={highlightId}
              onBoxClick={handleBoxClick}
            />
          ) : (
            <div className="h-full flex items-center justify-center text-slate-400 text-sm">
              Select a document to inspect
            </div>
          )}
        </div>

        {/* Right Side Panel: Extracted Fields & Findings */}
        <div className="w-96 bg-white border-l border-slate-200 flex flex-col shrink-0 overflow-hidden shadow-xs">
          {/* Tabs */}
          <div className="flex border-b border-slate-200 bg-slate-50 text-xs font-semibold">
            <button
              onClick={() => setActiveTab('fields')}
              className={`flex-1 py-2.5 text-center transition-colors border-b-2 ${
                activeTab === 'fields'
                  ? 'border-blue-600 text-blue-600 bg-white'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              Extracted Fields ({fields.length})
            </button>
            <button
              onClick={() => setActiveTab('findings')}
              className={`flex-1 py-2.5 text-center transition-colors border-b-2 ${
                activeTab === 'findings'
                  ? 'border-blue-600 text-blue-600 bg-white'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              Forensic Findings ({findings.length})
            </button>
          </div>

          {/* Tab Content */}
          <div className="flex-1 overflow-auto p-4 space-y-3">
            {activeTab === 'fields' ? (
              fields.length === 0 ? (
                <div className="text-xs text-slate-400 text-center py-8">No structured fields extracted for this document type.</div>
              ) : (
                fields.map((fld) => {
                  const isHighlighted = highlightId === fld.field_id
                  return (
                    <div
                      key={fld.field_id}
                      onClick={() => setHighlightId(fld.field_id)}
                      className={`p-3 rounded-lg border text-xs cursor-pointer transition-all ${
                        isHighlighted
                          ? 'border-blue-500 bg-blue-50/70 shadow-xs'
                          : 'border-slate-200 bg-white hover:border-slate-300'
                      }`}
                    >
                      <div className="flex justify-between items-start gap-1">
                        <span className="font-semibold text-slate-700">{fld.label || fld.name}</span>
                        <span className="font-mono text-[10px] text-slate-400">p.{fld.page}</span>
                      </div>
                      <div className="font-bold text-slate-900 mt-1 break-words">{fld.value}</div>
                      
                      <div className="flex items-center justify-between mt-2 pt-2 border-t border-slate-100 text-[11px]">
                        <span className="text-slate-500">Conf: {Math.round(fld.confidence * 100)}%</span>
                        <span className={`px-1.5 py-0.5 rounded font-mono text-[10px] font-semibold ${
                          fld.reliability === 'high' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
                          fld.reliability === 'medium' ? 'bg-amber-50 text-amber-700 border border-amber-200' :
                          'bg-rose-50 text-rose-700 border border-rose-200'
                        }`}>
                          OCR Agr: {Math.round(fld.ocr_agreement * 100)}% ({fld.reliability})
                        </span>
                      </div>
                    </div>
                  )
                })
              )
            ) : (
              findings.length === 0 ? (
                <div className="text-xs text-slate-400 text-center py-8">No visual or contextual anomalies detected in this document.</div>
              ) : (
                findings.map((fnd) => {
                  const isHighlighted = highlightId === fnd.finding_id
                  return (
                    <div
                      key={fnd.finding_id}
                      onClick={() => setHighlightId(fnd.finding_id)}
                      className={`p-3 rounded-lg border text-xs cursor-pointer transition-all ${
                        isHighlighted
                          ? 'border-rose-500 bg-rose-50/70 shadow-xs'
                          : 'border-slate-200 bg-white hover:border-slate-300'
                      }`}
                    >
                      <div className="flex justify-between items-start mb-1">
                        <span className="font-bold text-slate-900">{fnd.title}</span>
                        <span className="font-mono text-[10px] text-slate-400">p.{fnd.page}</span>
                      </div>
                      <ConfidenceBadge
                        category={fnd.category}
                        riskLevel={fnd.risk_level}
                        confidence={fnd.confidence}
                      />
                      <p className="text-slate-600 mt-2 text-[11px] leading-relaxed line-clamp-3">
                        {fnd.observation}
                      </p>
                    </div>
                  )
                })
              )
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
