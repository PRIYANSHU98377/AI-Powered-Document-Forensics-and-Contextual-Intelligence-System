import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Shield, FileSearch, GitFork, FileText, CheckCircle2, Upload, AlertTriangle } from 'lucide-react'

export default function Navbar({ activeCaseId }) {
  const location = useLocation()
  
  const navItems = [
    { label: 'Upload Cases', path: '/', icon: Upload },
    { label: 'Case Dashboard', path: activeCaseId ? `/case/${activeCaseId}` : '/', icon: Shield, disabled: !activeCaseId },
    { label: 'Document Viewer', path: activeCaseId ? `/case/${activeCaseId}/viewer` : '/', icon: FileSearch, disabled: !activeCaseId },
    { label: 'Findings Review', path: activeCaseId ? `/case/${activeCaseId}/findings` : '/', icon: AlertTriangle, disabled: !activeCaseId },
    { label: 'Entity Graph', path: activeCaseId ? `/case/${activeCaseId}/graph` : '/', icon: GitFork, disabled: !activeCaseId },
    { label: 'Dossier', path: activeCaseId ? `/case/${activeCaseId}/dossier` : '/', icon: FileText, disabled: !activeCaseId },
    { label: 'Audit Trail', path: '/audit', icon: CheckCircle2 },
  ]

  return (
    <header className="bg-slate-900 text-white shadow-md sticky top-0 z-50">
      {/* Mandatory Regulatory & Ethical Notice Banner */}
      <div className="bg-amber-500/15 border-b border-amber-500/30 px-4 py-1.5 text-center text-xs font-medium text-amber-200 flex items-center justify-center gap-2">
        <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
        <span>NOTICE: Automated findings are indicators for human review, never conclusions of fraud. OCR output is never ground truth. (ISO/IEC 27037 Principles)</span>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-14">
          <div className="flex items-center space-x-3">
            <Link to="/" className="flex items-center space-x-2">
              <div className="bg-blue-600 p-1.5 rounded-lg">
                <Shield className="w-5 h-5 text-white" />
              </div>
              <span className="font-bold text-lg tracking-tight text-white">DocDetective</span>
            </Link>
            <span className="text-xs bg-slate-800 text-slate-400 px-2 py-0.5 rounded border border-slate-700">v1.0.0</span>
            {activeCaseId && (
              <span className="text-xs bg-blue-900/60 text-blue-300 font-mono px-2 py-0.5 rounded border border-blue-700/50">
                Active: {activeCaseId}
              </span>
            )}
          </div>

          <nav className="flex space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = location.pathname === item.path
              if (item.disabled) return null

              return (
                <Link
                  key={item.label}
                  to={item.path}
                  className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                    isActive
                      ? 'bg-blue-600 text-white'
                      : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{item.label}</span>
                </Link>
              )
            })}
          </nav>
        </div>
      </div>
    </header>
  )
}
