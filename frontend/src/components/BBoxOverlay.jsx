import React, { useState, useRef, useEffect } from 'react'
import { ZoomIn, ZoomOut, RotateCcw, Layers } from 'lucide-react'

export default function BBoxOverlay({
  imageUrl,
  fields = [],
  findings = [],
  activeHighlightId = null,
  onBoxClick
}) {
  const [zoom, setZoom] = useState(1.0)
  const [layers, setLayers] = useState({
    suspicious: true,
    fields: true,
    ocr: true
  })
  const [hoveredBox, setHoveredBox] = useState(null)
  const imgRef = useRef(null)
  const [imgDim, setImgDim] = useState({ width: 800, height: 1000 })

  const handleImageLoad = (e) => {
    setImgDim({
      width: e.target.naturalWidth || 800,
      height: e.target.naturalHeight || 1000
    })
  }

  const toggleLayer = (layerName) => {
    setLayers(prev => ({ ...prev, [layerName]: !prev[layerName] }))
  }

  return (
    <div className="flex flex-col h-full bg-slate-900 rounded-xl overflow-hidden border border-slate-700">
      {/* Control Toolbar */}
      <div className="bg-slate-800 border-b border-slate-700 px-4 py-2 flex items-center justify-between text-xs text-slate-300">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-slate-400" />
          <span className="font-semibold text-white">Overlays:</span>
          
          <label className="flex items-center gap-1.5 cursor-pointer ml-2">
            <input
              type="checkbox"
              checked={layers.suspicious}
              onChange={() => toggleLayer('suspicious')}
              className="accent-rose-500 rounded"
            />
            <span className="text-rose-400 font-medium">Suspicious Regions ({findings.length})</span>
          </label>

          <label className="flex items-center gap-1.5 cursor-pointer ml-3">
            <input
              type="checkbox"
              checked={layers.fields}
              onChange={() => toggleLayer('fields')}
              className="accent-blue-500 rounded"
            />
            <span className="text-blue-400 font-medium">Extracted Fields ({fields.length})</span>
          </label>
        </div>

        {/* Zoom Controls */}
        <div className="flex items-center gap-1.5">
          <button
            onClick={() => setZoom(z => Math.max(0.5, z - 0.15))}
            className="p-1 rounded hover:bg-slate-700 text-slate-300"
            title="Zoom Out"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <span className="font-mono text-[11px] w-12 text-center">{Math.round(zoom * 100)}%</span>
          <button
            onClick={() => setZoom(z => Math.min(2.5, z + 0.15))}
            className="p-1 rounded hover:bg-slate-700 text-slate-300"
            title="Zoom In"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button
            onClick={() => setZoom(1.0)}
            className="p-1 rounded hover:bg-slate-700 text-slate-300 ml-1"
            title="Reset Zoom"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Canvas View Area */}
      <div className="flex-1 overflow-auto p-4 flex justify-center items-start">
        <div
          className="relative shadow-2xl transition-transform origin-top"
          style={{ transform: `scale(${zoom})` }}
        >
          {/* Base Document Page Image */}
          <img
            ref={imgRef}
            src={imageUrl}
            alt="Document Page"
            onLoad={handleImageLoad}
            className="max-w-none block rounded bg-white"
            style={{ width: imgDim.width }}
          />

          {/* SVG Overlay for Bounding Boxes */}
          <svg
            className="absolute inset-0 w-full h-full pointer-events-auto"
            viewBox={`0 0 ${imgDim.width} ${imgDim.height}`}
          >
            {/* 1. Field Bounding Boxes (Blue) */}
            {layers.fields && fields.map((fld) => {
              if (!fld.bbox) return null
              const { x, y, w, h } = fld.bbox
              const isActive = activeHighlightId === fld.field_id
              const isHovered = hoveredBox === fld.field_id

              return (
                <g key={fld.field_id}>
                  <rect
                    x={x}
                    y={y}
                    width={w}
                    height={h}
                    fill={isActive ? "rgba(59, 130, 246, 0.25)" : "rgba(59, 130, 246, 0.08)"}
                    stroke={isActive ? "#2563EB" : (isHovered ? "#3B82F6" : "#60A5FA")}
                    strokeWidth={isActive ? 3 : (isHovered ? 2 : 1.2)}
                    strokeDasharray={fld.reliability === "low" ? "4 2" : "none"}
                    className="cursor-pointer transition-all"
                    onClick={() => onBoxClick && onBoxClick("field", fld)}
                    onMouseEnter={() => setHoveredBox(fld.field_id)}
                    onMouseLeave={() => setHoveredBox(null)}
                  />
                  {(isHovered || isActive) && (
                    <text
                      x={x}
                      y={Math.max(12, y - 4)}
                      fill="#1D4ED8"
                      fontSize="11"
                      fontWeight="bold"
                      className="select-none pointer-events-none bg-white font-mono"
                    >
                      {fld.label || fld.name}: {fld.value}
                    </text>
                  )}
                </g>
              )
            })}

            {/* 2. Suspicious Findings Bounding Boxes (Red / Amber) */}
            {layers.suspicious && findings.map((fnd) => {
              if (!fnd.bbox) return null
              const { x, y, w, h } = fnd.bbox
              const isManip = fnd.category === "POTENTIAL_MANIPULATION"
              const color = isManip ? "#DC2626" : "#D97706"
              const isActive = activeHighlightId === fnd.finding_id
              const isHovered = hoveredBox === fnd.finding_id

              return (
                <g key={fnd.finding_id}>
                  <rect
                    x={x}
                    y={y}
                    width={w}
                    height={h}
                    fill={isManip ? "rgba(220, 38, 38, 0.22)" : "rgba(217, 119, 6, 0.20)"}
                    stroke={color}
                    strokeWidth={isActive ? 3.5 : (isHovered ? 2.5 : 2)}
                    className="cursor-pointer transition-all animate-pulse"
                    onClick={() => onBoxClick && onBoxClick("finding", fnd)}
                    onMouseEnter={() => setHoveredBox(fnd.finding_id)}
                    onMouseLeave={() => setHoveredBox(null)}
                  />
                  {(isHovered || isActive) && (
                    <text
                      x={x}
                      y={Math.max(14, y - 6)}
                      fill={color}
                      fontSize="12"
                      fontWeight="bold"
                      className="select-none pointer-events-none font-sans"
                    >
                      ⚠ {fnd.title} ({Math.round(fnd.confidence * 100)}%)
                    </text>
                  )}
                </g>
              )
            })}
          </svg>
        </div>
      </div>
    </div>
  )
}
