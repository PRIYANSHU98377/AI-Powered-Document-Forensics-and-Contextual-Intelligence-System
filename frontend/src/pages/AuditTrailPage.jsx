import React, { useState, useEffect } from 'react'
import { ShieldCheck, ShieldAlert, RefreshCw, AlertTriangle, Link as LinkIcon, Lock } from 'lucide-react'

export default function AuditTrailPage() {
  const [events, setEvents] = useState([])
  const [verifyResult, setVerifyResult] = useState(null)
  const [isVerifying, setIsVerifying] = useState(false)
  const [tamperMessage, setTamperMessage] = useState(null)

  const loadEvents = () => {
    fetch('/api/v1/audit/events?limit=100')
      .then(r => r.json())
      .then(data => setEvents(data.events || []))
      .catch(console.error)
  }

  const handleVerify = async () => {
    setIsVerifying(true)
    try {
      const res = await fetch('/api/v1/audit/verify')
      const data = await res.json()
      setVerifyResult(data)
    } catch (e) {
      console.error(e)
    } finally {
      setIsVerifying(false)
    }
  }

  const handleTamperDemo = async () => {
    try {
      const res = await fetch('/api/v1/audit/tamper-demo', { method: 'POST' })
      const data = await res.json()
      setTamperMessage(data.message)
      // Immediately re-verify to show failure!
      await handleVerify()
      loadEvents()
    } catch (e) {
      console.error(e)
    }
  }

  useEffect(() => {
    loadEvents()
    handleVerify()
  }, [])

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <Lock className="w-5 h-5 text-blue-600" />
            <span>Tamper-Evident Audit Trail (Cryptographic Hash Chain)</span>
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Immutable chain-of-custody logging following ISO/IEC 27037 principles: identification, collection, acquisition, and preservation.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={handleVerify}
            disabled={isVerifying}
            className="px-3.5 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-lg flex items-center gap-1.5 shadow-xs transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isVerifying ? 'animate-spin' : ''}`} />
            <span>Verify Integrity</span>
          </button>

          <button
            onClick={handleTamperDemo}
            className="px-3.5 py-2 bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-300 text-xs font-bold rounded-lg flex items-center gap-1.5 transition-colors"
          >
            <AlertTriangle className="w-3.5 h-3.5 text-rose-600" />
            <span>Tamper Demo (Test Failure)</span>
          </button>
        </div>
      </div>

      {/* Verification Status Card */}
      {verifyResult && (
        <div className={`p-5 rounded-xl border mb-6 transition-all ${
          verifyResult.is_valid
            ? 'bg-emerald-50/70 border-emerald-300 text-emerald-900'
            : 'bg-rose-50 border-rose-300 text-rose-900 shadow-md'
        }`}>
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              {verifyResult.is_valid ? (
                <ShieldCheck className="w-8 h-8 text-emerald-600 shrink-0" />
              ) : (
                <ShieldAlert className="w-8 h-8 text-rose-600 shrink-0 animate-bounce" />
              )}
              <div>
                <h3 className="text-base font-bold">
                  {verifyResult.is_valid ? "Cryptographic Chain Integrity Verified" : "INTEGRITY BREACH DETECTED: Tampering Found!"}
                </h3>
                <p className="text-xs mt-0.5">{verifyResult.message}</p>
                {verifyResult.broken_event_id && (
                  <div className="mt-2 text-xs font-mono bg-rose-100 p-2 rounded border border-rose-200">
                    Broken Event ID: <strong>{verifyResult.broken_event_id}</strong> (Reason: {verifyResult.reason})
                  </div>
                )}
              </div>
            </div>

            <div className="text-right text-xs font-mono">
              <div>Total Events: <strong>{verifyResult.total_events}</strong></div>
              <div>Verified Blocks: <strong>{verifyResult.verified_count}</strong></div>
            </div>
          </div>
        </div>
      )}

      {tamperMessage && (
        <div className="bg-amber-50 border border-amber-300 text-amber-800 p-3 rounded-lg text-xs mb-6">
          <strong>Tamper Injection Notice: </strong> {tamperMessage}
        </div>
      )}

      {/* Audit Log Timeline Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-200 flex justify-between items-center bg-slate-50">
          <h3 className="font-bold text-sm text-slate-800">Immutable Event Ledger ({events.length} Events)</h3>
          <span className="text-[11px] font-mono text-slate-500">Hash Algorithm: SHA-256</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-100 text-slate-600 font-semibold border-b border-slate-200">
              <tr>
                <th className="py-2.5 px-3">#</th>
                <th className="py-2.5 px-3">Timestamp</th>
                <th className="py-2.5 px-3">Action</th>
                <th className="py-2.5 px-3">Actor</th>
                <th className="py-2.5 px-3">Previous Hash</th>
                <th className="py-2.5 px-3">Entry Hash</th>
                <th className="py-2.5 px-3">Payload Summary</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono text-[11px] text-slate-700">
              {events.map((ev) => (
                <tr key={ev.event_id} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-2.5 px-3 font-bold text-slate-900">{ev.id}</td>
                  <td className="py-2.5 px-3 text-slate-500">{ev.timestamp?.slice(0, 19).replace('T', ' ')}</td>
                  <td className="py-2.5 px-3 font-sans font-bold text-blue-700">{ev.action}</td>
                  <td className="py-2.5 px-3 text-slate-600">{ev.actor}</td>
                  <td className="py-2.5 px-3 text-slate-400 text-[10px]">{ev.prev_hash?.slice(0, 12)}...</td>
                  <td className="py-2.5 px-3 font-bold text-slate-800 text-[10px]">{ev.entry_hash?.slice(0, 12)}...</td>
                  <td className="py-2.5 px-3 font-sans text-slate-600 truncate max-w-xs">
                    {JSON.stringify(ev.details)}
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
