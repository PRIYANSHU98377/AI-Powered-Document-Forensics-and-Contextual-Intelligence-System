import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Upload, FileText, CheckCircle2, AlertTriangle, ArrowRight, Sparkles, FolderArchive } from 'lucide-react'
import ProgressStepper from '../components/ProgressStepper'

export default function UploadPage({ setActiveCaseId }) {
  const navigate = useNavigate()
  const [caseName, setCaseName] = useState('Loan Application Forensic Investigation')
  const [selectedFiles, setSelectedFiles] = useState([])
  const [isUploading, setIsUploading] = useState(false)
  const [createdCaseId, setCreatedCaseId] = useState(null)
  const [pipelineProgress, setPipelineProgress] = useState(null)
  const [existingCases, setExistingCases] = useState([])

  useEffect(() => {
    fetch('/api/v1/cases')
      .then(r => r.json())
      .then(data => setExistingCases(data || []))
      .catch(console.error)
  }, [])

  const handleFileChange = (e) => {
    if (e.target.files) {
      setSelectedFiles(Array.from(e.target.files))
    }
  }

  // Load Synthetic Demo Cases directly
  const handleLoadDemoCase = async (isTampered = true) => {
    setIsUploading(true)
    try {
      // 1. Create case
      const caseRes = await fetch('/api/v1/cases', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: isTampered ? 'Demo Case: Synthetic Tampered Application' : 'Demo Case: Synthetic Genuine Application',
          description: isTampered
            ? 'Injected with 8 targeted forensic manipulations across ID, payslip, statement, declaration.'
            : 'Authentic baseline application with natural scanner noise and tolerated variations.'
        })
      })
      const caseData = await caseRes.json()
      const newCaseId = caseData.case_id
      setCreatedCaseId(newCaseId)
      setActiveCaseId(newCaseId)

      // 2. Fetch demo dataset files from static storage or data dir
      const demoFolder = isTampered ? 'demo_case_tampered' : 'demo_case_genuine'
      const filenames = [
        'id_card.png',
        'application_form.pdf',
        'salary_slip.png',
        'bank_statement.pdf',
        'utility_bill.png',
        'declaration.pdf'
      ]

      const formData = new FormData()
      for (const fn of filenames) {
        // Fetch from static endpoint
        try {
          const fileResp = await fetch(`/static/demo/${demoFolder}/${fn}`)
          if (fileResp.ok) {
            const blob = await fileResp.blob()
            formData.append('files', blob, fn)
          }
        } catch (e) {
          console.warn("Static file fetch fallback", e)
        }
      }

      // If static files weren't directly served, run server-side upload helper
      // Upload files
      await fetch(`/api/v1/cases/${newCaseId}/documents`, {
        method: 'POST',
        body: formData
      })

      // 3. Start pipeline & stream progress
      startPipelineProcessing(newCaseId)
    } catch (err) {
      console.error("Demo load failed", err)
      setIsUploading(false)
    }
  }

  const handleUploadAndRun = async () => {
    if (selectedFiles.length === 0) return
    setIsUploading(true)

    try {
      // 1. Create Case
      const caseRes = await fetch('/api/v1/cases', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: caseName })
      })
      const caseData = await caseRes.json()
      const newCaseId = caseData.case_id
      setCreatedCaseId(newCaseId)
      setActiveCaseId(newCaseId)

      // 2. Upload Files
      const formData = new FormData()
      selectedFiles.forEach(f => formData.append('files', f))
      await fetch(`/api/v1/cases/${newCaseId}/documents`, {
        method: 'POST',
        body: formData
      })

      // 3. Process Pipeline
      startPipelineProcessing(newCaseId)
    } catch (e) {
      console.error("Upload failed", e)
      setIsUploading(false)
    }
  }

  const startPipelineProcessing = (caseId) => {
    // Listen to SSE progress
    const eventSource = new EventSource(`/api/v1/cases/${caseId}/progress`)
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        setPipelineProgress(data)
        if (data.progress_pct >= 100) {
          eventSource.close()
          setTimeout(() => {
            navigate(`/case/${caseId}`)
          }, 1200)
        }
      } catch (e) {
        console.error("SSE parse error", e)
      }
    }

    // Trigger pipeline execution
    fetch(`/api/v1/cases/${caseId}/process`, { method: 'POST' })
      .catch(console.error)
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Title */}
      <div className="text-center mb-8">
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
          AI Document Forensics & Contextual Intelligence
        </h1>
        <p className="mt-2 text-sm text-slate-600 max-w-2xl mx-auto">
          Multi-document cross-correlation, ELA/Noise/Font tampering detection, double-OCR fusion, and explainable dual-view reasoning.
        </p>
      </div>

      {/* Live Stepper if processing */}
      {pipelineProgress && (
        <ProgressStepper
          currentStage={pipelineProgress.stage}
          progressPct={pipelineProgress.progress_pct}
          message={pipelineProgress.message}
          isComplete={pipelineProgress.progress_pct >= 100}
        />
      )}

      {/* Main Grid: Upload vs Quick Demo */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Upload Custom Files (2 cols) */}
        <div className="md:col-span-2 bg-white rounded-xl border border-slate-200 p-6 shadow-xs">
          <h2 className="text-base font-bold text-slate-900 mb-4 flex items-center gap-2">
            <Upload className="w-4 h-4 text-blue-600" />
            <span>Upload Investigation Files</span>
          </h2>

          <div className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Investigation Case Name</label>
              <input
                type="text"
                value={caseName}
                onChange={(e) => setCaseName(e.target.value)}
                className="w-full text-xs p-2.5 border border-slate-200 rounded-lg focus:ring-1 focus:ring-blue-500 outline-hidden"
              />
            </div>

            {/* Dropzone */}
            <div className="border-2 border-dashed border-slate-300 rounded-xl p-8 text-center hover:border-blue-500 transition-colors bg-slate-50/50">
              <input
                type="file"
                multiple
                accept=".pdf,.png,.jpg,.jpeg,.tiff"
                onChange={handleFileChange}
                className="hidden"
                id="file-upload"
              />
              <label htmlFor="file-upload" className="cursor-pointer flex flex-col items-center">
                <FileText className="w-10 h-10 text-slate-400 mb-2" />
                <span className="text-sm font-semibold text-slate-700">Click to browse or drag & drop files</span>
                <span className="text-xs text-slate-400 mt-1">Accepts PDF, PNG, JPG, TIFF (Max 50MB per file)</span>
              </label>
            </div>

            {/* Selected files preview */}
            {selectedFiles.length > 0 && (
              <div className="bg-slate-50 rounded-lg p-3 border border-slate-200">
                <div className="text-xs font-semibold text-slate-700 mb-2">Selected Documents ({selectedFiles.length}):</div>
                <div className="space-y-1 max-h-36 overflow-auto text-xs font-mono text-slate-600">
                  {selectedFiles.map((f, i) => (
                    <div key={i} className="flex justify-between items-center bg-white px-2 py-1 rounded border border-slate-100">
                      <span>{f.name}</span>
                      <span className="text-slate-400">{Math.round(f.size / 1024)} KB</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <button
              onClick={handleUploadAndRun}
              disabled={selectedFiles.length === 0 || isUploading}
              className="w-full py-2.5 px-4 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-lg shadow-sm disabled:opacity-50 flex items-center justify-center gap-2"
            >
              <span>Start Automated Forensic Analysis</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Quick Launch Demo Cases (1 col) */}
        <div className="space-y-4">
          <div className="bg-gradient-to-br from-slate-900 to-slate-800 text-white rounded-xl p-6 shadow-md border border-slate-700">
            <h3 className="text-sm font-bold flex items-center gap-2 mb-2 text-blue-300">
              <Sparkles className="w-4 h-4" />
              <span>One-Click Hackathon Demos</span>
            </h3>
            <p className="text-xs text-slate-300 mb-4 leading-relaxed">
              Test DocDetective instantly with pre-generated synthetic datasets matching all 8 hackathon manipulation types.
            </p>

            <div className="space-y-2.5">
              <button
                onClick={() => handleLoadDemoCase(true)}
                disabled={isUploading}
                className="w-full text-left p-3 rounded-lg bg-rose-950/60 border border-rose-700/60 hover:bg-rose-900/60 transition-colors"
              >
                <div className="flex items-center justify-between text-xs font-bold text-rose-200">
                  <span>Tampered Case (8 Injections)</span>
                  <span className="bg-rose-500/20 text-rose-300 px-1.5 py-0.5 rounded text-[10px]">Test Injections</span>
                </div>
                <div className="text-[11px] text-slate-300 mt-1">
                  Altered digit in salary, DOB conflict on ID, whitened statement row, cloned stamp, address mismatch.
                </div>
              </button>

              <button
                onClick={() => handleLoadDemoCase(false)}
                disabled={isUploading}
                className="w-full text-left p-3 rounded-lg bg-emerald-950/60 border border-emerald-700/60 hover:bg-emerald-900/60 transition-colors"
              >
                <div className="flex items-center justify-between text-xs font-bold text-emerald-200">
                  <span>Genuine Case (Baseline)</span>
                  <span className="bg-emerald-500/20 text-emerald-300 px-1.5 py-0.5 rounded text-[10px]">Zero Alterations</span>
                </div>
                <div className="text-[11px] text-slate-300 mt-1">
                  100% consistent applicant set with tolerated name variations and scanner compression.
                </div>
              </button>
            </div>
          </div>

          {/* Past Cases List */}
          {existingCases.length > 0 && (
            <div className="bg-white rounded-xl border border-slate-200 p-4">
              <h4 className="text-xs font-bold text-slate-800 mb-2 flex items-center gap-1.5">
                <FolderArchive className="w-3.5 h-3.5 text-slate-500" />
                <span>Existing Cases ({existingCases.length})</span>
              </h4>
              <div className="space-y-1.5 max-h-48 overflow-auto text-xs">
                {existingCases.map((c) => (
                  <button
                    key={c.case_id}
                    onClick={() => { setActiveCaseId(c.case_id); navigate(`/case/${c.case_id}`) }}
                    className="w-full text-left p-2 rounded bg-slate-50 hover:bg-blue-50 border border-slate-200 flex justify-between items-center transition-colors"
                  >
                    <div className="truncate mr-2">
                      <div className="font-semibold text-slate-800 truncate">{c.name}</div>
                      <div className="text-[10px] text-slate-400 font-mono">{c.case_id}</div>
                    </div>
                    <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                      c.overall_risk === 'HIGH' ? 'bg-rose-100 text-rose-800' :
                      c.overall_risk === 'MEDIUM' ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800'
                    }`}>
                      {c.overall_risk}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
