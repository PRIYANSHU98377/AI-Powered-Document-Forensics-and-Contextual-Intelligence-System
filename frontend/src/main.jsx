import React, { lazy, Suspense, useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Navigate, Route, Routes, useLocation, useParams } from 'react-router-dom'
import Navbar from './components/Navbar'
import './index.css'

const UploadPage = lazy(() => import('./pages/UploadPage'))
const CaseDashboard = lazy(() => import('./pages/CaseDashboard'))
const DocumentViewer = lazy(() => import('./pages/DocumentViewer'))
const FindingsReview = lazy(() => import('./pages/FindingsReview'))
const RelationshipGraphPage = lazy(() => import('./pages/RelationshipGraphPage'))
const DossierPage = lazy(() => import('./pages/DossierPage'))
const AuditTrailPage = lazy(() => import('./pages/AuditTrailPage'))

function CaseRoute({ children, onCaseId }) {
  const { caseId } = useParams()

  useEffect(() => {
    if (caseId) onCaseId(caseId)
  }, [caseId, onCaseId])

  return children
}

function App() {
  const location = useLocation()
  const [activeCaseId, setActiveCaseId] = useState(null)
  const routeCaseId = location.pathname.match(/^\/case\/([^/]+)/)?.[1]

  useEffect(() => {
    if (routeCaseId) setActiveCaseId(routeCaseId)
  }, [routeCaseId])

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar activeCaseId={activeCaseId} />
      <main>
        <Suspense fallback={<div className="p-8 text-center text-sm text-slate-500">Loading workspace...</div>}>
          <Routes>
            <Route path="/" element={<UploadPage setActiveCaseId={setActiveCaseId} />} />
            <Route
              path="/case/:caseId"
              element={
                <CaseRoute onCaseId={setActiveCaseId}>
                  <CaseDashboard />
                </CaseRoute>
              }
            />
            <Route
              path="/case/:caseId/viewer"
              element={
                <CaseRoute onCaseId={setActiveCaseId}>
                  <DocumentViewer />
                </CaseRoute>
              }
            />
            <Route
              path="/case/:caseId/findings"
              element={
                <CaseRoute onCaseId={setActiveCaseId}>
                  <FindingsReview />
                </CaseRoute>
              }
            />
            <Route
              path="/case/:caseId/graph"
              element={
                <CaseRoute onCaseId={setActiveCaseId}>
                  <RelationshipGraphPage />
                </CaseRoute>
              }
            />
            <Route
              path="/case/:caseId/dossier"
              element={
                <CaseRoute onCaseId={setActiveCaseId}>
                  <DossierPage />
                </CaseRoute>
              }
            />
            <Route path="/audit" element={<AuditTrailPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </main>
    </div>
  )
}

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
)
