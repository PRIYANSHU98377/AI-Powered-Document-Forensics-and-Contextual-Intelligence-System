import React, { useState, useEffect, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import { GitFork, Info, ExternalLink, ShieldAlert, CheckCircle } from 'lucide-react'
import cytoscape from 'cytoscape'

export default function RelationshipGraphPage() {
  const { caseId } = useParams()
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] })
  const [selectedElement, setSelectedElement] = useState(null)
  const cyRef = useRef(null)
  const containerRef = useRef(null)

  useEffect(() => {
    fetch(`/api/v1/cases/${caseId}/graph`)
      .then(r => r.json())
      .then(data => {
        setGraphData(data)
      })
      .catch(console.error)
  }, [caseId])

  useEffect(() => {
    if (!containerRef.current || graphData.nodes.length === 0) return

    // Transform nodes and edges for Cytoscape
    const cyElements = [
      ...graphData.nodes.map(n => ({
        data: {
          id: n.id,
          label: n.label,
          type: n.type
        }
      })),
      ...graphData.edges.map(e => ({
        data: {
          id: e.id,
          source: e.source,
          target: e.target,
          status: e.status, // green, amber, red
          type: e.type,
          details: e.details,
          evidence_id: e.evidence_id
        }
      }))
    ]

    const cy = cytoscape({
      container: containerRef.current,
      elements: cyElements,
      style: [
        {
          selector: 'node',
          style: {
            'label': 'data(label)',
            'font-size': '11px',
            'font-family': 'sans-serif',
            'text-valign': 'center',
            'text-halign': 'center',
            'color': '#ffffff',
            'text-outline-width': 1.5,
            'text-outline-color': '#1e293b',
            'width': 65,
            'height': 65
          }
        },
        {
          selector: 'node[type = "document"]',
          style: {
            'background-color': '#2563EB', // Blue
            'shape': 'round-rectangle'
          }
        },
        {
          selector: 'node[type = "person"]',
          style: {
            'background-color': '#7C3AED', // Purple
            'shape': 'ellipse'
          }
        },
        {
          selector: 'node[type = "address"]',
          style: {
            'background-color': '#059669', // Emerald
            'shape': 'diamond'
          }
        },
        {
          selector: 'node[type = "id_number"], node[type = "account"]',
          style: {
            'background-color': '#D97706', // Amber
            'shape': 'hexagon'
          }
        },
        {
          selector: 'edge',
          style: {
            'width': 3,
            'curve-style': 'bezier'
          }
        },
        {
          selector: 'edge[status = "green"]',
          style: {
            'line-color': '#10B981',
            'target-arrow-color': '#10B981',
            'line-style': 'solid'
          }
        },
        {
          selector: 'edge[status = "amber"]',
          style: {
            'line-color': '#F59E0B',
            'target-arrow-color': '#F59E0B',
            'line-style': 'dashed'
          }
        },
        {
          selector: 'edge[status = "red"]',
          style: {
            'line-color': '#EF4444',
            'target-arrow-color': '#EF4444',
            'line-style': 'solid',
            'width': 4
          }
        }
      ],
      layout: {
        name: 'cose',
        animate: true,
        padding: 30
      }
    })

    cy.on('tap', 'node', (evt) => {
      const node = evt.target
      setSelectedElement({ kind: 'node', data: node.data() })
    })

    cy.on('tap', 'edge', (evt) => {
      const edge = evt.target
      setSelectedElement({ kind: 'edge', data: edge.data() })
    })

    cyRef.current = cy
    return () => cy.destroy()
  }, [graphData])

  return (
    <div className="h-[calc(100vh-6rem)] flex flex-col bg-slate-900 text-white overflow-hidden">
      {/* Top Header */}
      <div className="bg-slate-800/90 border-b border-slate-700 px-6 py-3 flex items-center justify-between text-xs shrink-0">
        <div className="flex items-center gap-3">
          <Link to={`/case/${caseId}`} className="text-blue-400 font-semibold hover:underline">
            ← Case Dashboard
          </Link>
          <span className="text-slate-600">|</span>
          <div className="flex items-center gap-2">
            <GitFork className="w-4 h-4 text-purple-400" />
            <span className="font-bold text-sm text-white">Cross-Document Entity & Conflict Graph</span>
          </div>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-4 text-[11px]">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-0.5 bg-emerald-500 inline-block" />
            <span className="text-slate-300">Exact Match</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-0.5 bg-amber-500 border-b border-dashed border-amber-500 inline-block" />
            <span className="text-slate-300">Tolerated Variation</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-0.5 bg-rose-500 inline-block" />
            <span className="text-rose-400 font-bold">Conflict / Discrepancy</span>
          </div>
        </div>
      </div>

      {/* Graph Canvas & Side Panel */}
      <div className="flex-1 flex overflow-hidden relative">
        <div ref={containerRef} className="flex-1 h-full w-full bg-slate-950" />

        {/* Selected Element Drawer */}
        {selectedElement && (
          <div className="w-80 bg-slate-800/95 border-l border-slate-700 p-4 overflow-auto shrink-0 shadow-2xl backdrop-blur-xs text-xs">
            <div className="flex justify-between items-center mb-3 pb-2 border-b border-slate-700">
              <span className="font-bold text-white uppercase tracking-wider text-[11px]">
                {selectedElement.kind === 'node' ? 'Entity Details' : 'Relationship Edge'}
              </span>
              <button
                onClick={() => setSelectedElement(null)}
                className="text-slate-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            {selectedElement.kind === 'node' ? (
              <div className="space-y-3">
                <div>
                  <div className="text-slate-400 text-[10px] uppercase font-bold">Label</div>
                  <div className="text-white font-bold text-sm mt-0.5">{selectedElement.data.label}</div>
                </div>
                <div>
                  <div className="text-slate-400 text-[10px] uppercase font-bold">Node Type</div>
                  <div className="text-blue-400 font-mono mt-0.5 uppercase">{selectedElement.data.type}</div>
                </div>
                <div>
                  <div className="text-slate-400 text-[10px] uppercase font-bold">Identifier</div>
                  <div className="text-slate-300 font-mono text-[11px] mt-0.5">{selectedElement.data.id}</div>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                <div>
                  <div className="text-slate-400 text-[10px] uppercase font-bold">Relationship Type</div>
                  <div className="font-bold text-white text-sm mt-0.5">{selectedElement.data.type}</div>
                </div>
                <div>
                  <div className="text-slate-400 text-[10px] uppercase font-bold">Edge Status</div>
                  <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold mt-1 ${
                    selectedElement.data.status === 'red' ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40' :
                    selectedElement.data.status === 'amber' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40' :
                    'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                  }`}>
                    {selectedElement.data.status.toUpperCase()}
                  </span>
                </div>
                <div>
                  <div className="text-slate-400 text-[10px] uppercase font-bold">Details</div>
                  <div className="text-slate-200 mt-1 leading-relaxed">{selectedElement.data.details}</div>
                </div>
                {selectedElement.data.evidence_id && (
                  <div className="pt-2 border-t border-slate-700">
                    <Link
                      to={`/case/${caseId}/findings`}
                      className="text-blue-400 hover:text-blue-300 flex items-center gap-1 font-semibold text-xs"
                    >
                      <span>View Corroborating Finding</span>
                      <ExternalLink className="w-3 h-3" />
                    </Link>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
