import React, { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Download, FileText, CheckCircle2, ShieldAlert, ArrowLeft } from 'lucide-react'

export default function DossierPage() {
  const { caseId } = useParams()
  const [dossierHtml, setDossierHtml] = useState('')
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    fetch(`/api/v1/cases/${caseId}/dossier/html`)
      .then(r => r.text())
      .then(html => {
        setDossierHtml(html)
        setIsLoading(false)
      })
      .catch(err => {
        console.error(err)
        setIsLoading(false)
      })
  }, [caseId])

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Top Header */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs mb-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs text-slate-500 font-mono mb-1">
            <Link to={`/case/${caseId}`} className="text-blue-600 hover:underline">← Case Dashboard</Link>
            <span>•</span>
            <span>Case ID: {caseId}</span>
          </div>
          <h1 className="text-xl font-bold text-slate-900">Investigation Dossier & Evidence Audit</h1>
        </div>

        <div className="flex items-center gap-2.5">
          <a
            href={`/api/v1/cases/${caseId}/dossier/json`}
            target="_blank"
            rel="noreferrer"
            className="px-3 py-1.5 rounded-lg border border-slate-300 text-slate-700 bg-white hover:bg-slate-50 text-xs font-semibold flex items-center gap-1.5 transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export JSON</span>
          </a>

          <a
            href={`/api/v1/cases/${caseId}/dossier/pdf`}
            download
            className="px-4 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold flex items-center gap-1.5 shadow-xs transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download Official PDF Dossier</span>
          </a>
        </div>
      </div>

      {/* Dossier Preview Container */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-md overflow-hidden min-h-[800px]">
        {isLoading ? (
          <div className="p-12 text-center text-sm text-slate-500">Generating forensic dossier...</div>
        ) : (
          <iframe
            srcDoc={dossierHtml}
            title="Dossier Preview"
            className="w-full h-[950px] border-none"
          />
        )}
      </div>
    </div>
  )
}
