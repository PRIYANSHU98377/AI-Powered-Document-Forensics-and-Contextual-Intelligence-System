import React, { useState } from 'react'
import { ZoomIn, Eye } from 'lucide-react'

export default function EvidenceCrop({ evidenceId, cropUrl, overlayUrl, detector, score }) {
  const [showOverlayModal, setShowOverlayModal] = useState(false)

  return (
    <div className="border border-slate-200 rounded-lg p-2.5 bg-slate-50">
      <div className="flex items-center justify-between text-xs mb-2">
        <span className="font-mono text-slate-500 font-semibold">{evidenceId || 'Evidence Crop'}</span>
        <span className="text-[11px] font-mono px-1.5 py-0.5 rounded bg-slate-200 text-slate-700">
          Score: {Math.round((score || 0) * 100)}%
        </span>
      </div>

      <div className="relative group bg-white border border-slate-200 rounded overflow-hidden flex items-center justify-center min-h-[90px] max-h-[140px]">
        {cropUrl ? (
          <img
            src={cropUrl}
            alt="Evidence region crop"
            className="object-contain max-h-[130px] w-auto"
            onError={(e) => { e.target.style.display = 'none' }}
          />
        ) : (
          <span className="text-xs text-slate-400">Crop not available</span>
        )}

        {overlayUrl && (
          <button
            onClick={() => setShowOverlayModal(true)}
            className="absolute bottom-1 right-1 bg-slate-900/80 hover:bg-slate-900 text-white text-[11px] px-2 py-1 rounded shadow-xs flex items-center gap-1 opacity-90 group-hover:opacity-100 transition-opacity"
            title="View Full Page Overlay"
          >
            <Eye className="w-3 h-3" />
            <span>Overlay</span>
          </button>
        )}
      </div>

      {/* Overlay Modal */}
      {showOverlayModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/80 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-4xl max-h-[90vh] overflow-hidden flex flex-col shadow-2xl">
            <div className="px-4 py-3 bg-slate-900 text-white flex justify-between items-center text-sm font-semibold">
              <span>Full Page Forensic Overlay ({detector})</span>
              <button
                onClick={() => setShowOverlayModal(false)}
                className="text-slate-400 hover:text-white px-2 py-0.5"
              >
                ✕ Close
              </button>
            </div>
            <div className="p-4 overflow-auto flex-1 flex justify-center bg-slate-100">
              <img src={overlayUrl} alt="Overlay" className="max-h-[75vh] object-contain rounded border border-slate-300" />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
