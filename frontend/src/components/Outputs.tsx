import React, { useEffect, useRef, useState } from 'react'
import SpectrumPlot from './SpectrumPlot'
import TimePlot from './TimePlot'

interface OutputsProps {
  result: any
  expanded: any
  carrierAutoHz?: number
  outputConfig: {
    osaMode: 'auto' | 'manual'
    osaNode: string
    osaPort: string
    esaMode: 'auto' | 'esa' | 'time'
    esaNode: string
    esaPort: string
    includePower: boolean
  }
  outputPorts: {
    optical: { nodeId: string; port: string; label: string }[]
    electrical: { nodeId: string; port: string; label: string }[]
    any: { nodeId: string; port: string; label: string; type: string }[]
  }
  onOutputConfigChange: (patch: Partial<OutputsProps['outputConfig']>) => void
  labels: {
    title: string
    jobResult: string
    expandedGraph: string
    noResult: string
    notExpanded: string
    outputsConfig: string
    osaMode: string
    esaMode: string
    auto: string
    manual: string
    spectrum: string
    timePreview: string
    includePower: string
    noOutputs: string
    osa: string
    esa: string
    time: string
    meta: string
    range: string
    peak: string
    markers: string
    markerInput: string
    addMarker: string
    clearMarkers: string
    removeMarker: string
    unit: string
    unitHz: string
    unitNm: string
    unitOffset: string
    offset: string
    carrierCenter: string
    carrierAuto: string
    carrierManual: string
    carrierValue: string
    wavelengthNm: string
    frequencyHz: string
    saveImage: string
    saveCsv: string
    exportSettings: string
    exportScale: string
    exportFormat: string
    exportBackground: string
    exportPng: string
    exportSvg: string
    exportBgSolid: string
    exportBgTransparent: string
    osaPlotSettings: string
    esaPlotSettings: string
    showPeak: string
    showMinMax: string
    viewRange: string
    rangeAuto: string
    rangeCustom: string
    rangeMin: string
    rangeMax: string
  }
}

export default function Outputs({
  result,
  expanded,
  labels,
  carrierAutoHz,
  outputConfig,
  outputPorts,
  onOutputConfigChange
}: OutputsProps) {
  const [showOutputSettings, setShowOutputSettings] = useState(false)
  const settingsRef = useRef<HTMLDivElement | null>(null)
  const osa = result?.osa || null
  const esa = result?.esa || null
  const meta = result?.meta || null
  const esaIsTime = esa?.kind === 'time'

  useEffect(() => {
    if (!showOutputSettings) return
    const handleClick = (event: MouseEvent) => {
      if (!settingsRef.current) return
      if (!settingsRef.current.contains(event.target as Node)) {
        setShowOutputSettings(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [showOutputSettings])

  return (
    <div className="panel">
      <div className="panel-header">
        <div className="panel-title">{labels.title}</div>
        <div className="panel-actions" ref={settingsRef}>
          <button
            className="panel-icon-button"
            type="button"
            onClick={() => setShowOutputSettings((v) => !v)}
            title={labels.outputsConfig}
          >
            ⚙
          </button>
          {showOutputSettings && (
            <div className="panel-options">
              <div className="output-config">
                <label className="field">
                  <span>{labels.osaMode}</span>
                  <select
                    value={outputConfig.osaMode}
                    onChange={(e) => onOutputConfigChange({ osaMode: e.target.value as 'auto' | 'manual' })}
                  >
                    <option value="auto">{labels.auto}</option>
                    <option value="manual">{labels.manual}</option>
                  </select>
                </label>
                {outputConfig.osaMode === 'manual' && (
                  <label className="field">
                    <span>{labels.osa}</span>
                    <select
                      value={`${outputConfig.osaNode}:${outputConfig.osaPort}`}
                      onChange={(e) => {
                        const [nodeId, port] = e.target.value.split(':')
                        onOutputConfigChange({ osaNode: nodeId || '', osaPort: port || '' })
                      }}
                    >
                      {outputPorts.optical.length === 0 && <option value="">{labels.noOutputs}</option>}
                      {outputPorts.optical.map((opt) => (
                        <option key={`${opt.nodeId}-${opt.port}`} value={`${opt.nodeId}:${opt.port}`}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </label>
                )}
                <label className="field">
                  <span>{labels.esaMode}</span>
                  <select
                    value={outputConfig.esaMode}
                    onChange={(e) => onOutputConfigChange({ esaMode: e.target.value as 'auto' | 'esa' | 'time' })}
                  >
                    <option value="auto">{labels.auto}</option>
                    <option value="esa">{labels.spectrum}</option>
                    <option value="time">{labels.timePreview}</option>
                  </select>
                </label>
                {outputConfig.esaMode !== 'auto' && (
                  <label className="field">
                    <span>{labels.esa}</span>
                    <select
                      value={`${outputConfig.esaNode}:${outputConfig.esaPort}`}
                      onChange={(e) => {
                        const [nodeId, port] = e.target.value.split(':')
                        onOutputConfigChange({ esaNode: nodeId || '', esaPort: port || '' })
                      }}
                    >
                      {outputConfig.esaMode === 'esa' && outputPorts.electrical.length === 0 && (
                        <option value="">{labels.noOutputs}</option>
                      )}
                      {outputConfig.esaMode === 'time' && outputPorts.any.length === 0 && (
                        <option value="">{labels.noOutputs}</option>
                      )}
                      {(outputConfig.esaMode === 'esa' ? outputPorts.electrical : outputPorts.any).map((opt) => (
                        <option key={`${opt.nodeId}-${opt.port}`} value={`${opt.nodeId}:${opt.port}`}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </label>
                )}
                <label className="field">
                  <span>{labels.includePower}</span>
                  <input
                    type="checkbox"
                    checked={outputConfig.includePower}
                    onChange={(e) => onOutputConfigChange({ includePower: e.target.checked })}
                  />
                </label>
              </div>
            </div>
          )}
        </div>
      </div>
      <div className="panel-body outputs">
        <SpectrumPlot
          title={labels.osa}
          data={osa?.kind === 'osa' ? osa : null}
          isOptical
          carrierAutoHz={carrierAutoHz}
          labels={{
            range: labels.range,
            peak: labels.peak,
            markers: labels.markers,
            markerInput: labels.markerInput,
            addMarker: labels.addMarker,
            clearMarkers: labels.clearMarkers,
            removeMarker: labels.removeMarker,
            unit: labels.unit,
            unitHz: labels.unitHz,
            unitNm: labels.unitNm,
            unitOffset: labels.unitOffset,
            offset: labels.offset,
            carrierCenter: labels.carrierCenter,
            carrierAuto: labels.carrierAuto,
            carrierManual: labels.carrierManual,
            carrierValue: labels.carrierValue,
            wavelengthNm: labels.wavelengthNm,
            frequencyHz: labels.frequencyHz,
            saveImage: labels.saveImage,
            saveCsv: labels.saveCsv,
            exportSettings: labels.osaPlotSettings,
            exportScale: labels.exportScale,
            exportFormat: labels.exportFormat,
            exportBackground: labels.exportBackground,
            exportPng: labels.exportPng,
            exportSvg: labels.exportSvg,
            exportBgSolid: labels.exportBgSolid,
            exportBgTransparent: labels.exportBgTransparent,
            showPeak: labels.showPeak,
            showMinMax: labels.showMinMax,
            viewRange: labels.viewRange,
            rangeAuto: labels.rangeAuto,
            rangeCustom: labels.rangeCustom,
            rangeMin: labels.rangeMin,
            rangeMax: labels.rangeMax
          }}
        />
        {esaIsTime ? (
          <TimePlot title={labels.time} data={esa} />
        ) : (
          <SpectrumPlot
            title={labels.esa}
            data={esa?.kind === 'esa' ? esa : null}
            isOptical={false}
            labels={{
              range: labels.range,
              peak: labels.peak,
              markers: labels.markers,
              markerInput: labels.markerInput,
              addMarker: labels.addMarker,
              clearMarkers: labels.clearMarkers,
              removeMarker: labels.removeMarker,
              unit: labels.unit,
              unitHz: labels.unitHz,
              unitNm: labels.unitNm,
              unitOffset: labels.unitOffset,
              offset: labels.offset,
              carrierCenter: labels.carrierCenter,
              carrierAuto: labels.carrierAuto,
              carrierManual: labels.carrierManual,
              carrierValue: labels.carrierValue,
              wavelengthNm: labels.wavelengthNm,
              frequencyHz: labels.frequencyHz,
              saveImage: labels.saveImage,
              saveCsv: labels.saveCsv,
              exportSettings: labels.esaPlotSettings,
              exportScale: labels.exportScale,
              exportFormat: labels.exportFormat,
              exportBackground: labels.exportBackground,
              exportPng: labels.exportPng,
              exportSvg: labels.exportSvg,
              exportBgSolid: labels.exportBgSolid,
              exportBgTransparent: labels.exportBgTransparent,
              showPeak: labels.showPeak,
              showMinMax: labels.showMinMax,
              viewRange: labels.viewRange,
              rangeAuto: labels.rangeAuto,
              rangeCustom: labels.rangeCustom,
              rangeMin: labels.rangeMin,
              rangeMax: labels.rangeMax
            }}
          />
        )}
        <div>
          <div className="section-title">{labels.meta}</div>
          {meta ? (
            <div className="meta-grid">
              <div>fs: {meta.fs}</div>
              <div>duration: {meta.duration_s}</div>
              <div>samples: {meta.n_samples ?? '-'}</div>
              <div>device: {meta.device}</div>
            </div>
          ) : (
            <div className="hint">{labels.noResult}</div>
          )}
        </div>
        <div>
          <div className="section-title">{labels.jobResult}</div>
          <pre>{result ? JSON.stringify(result, null, 2) : labels.noResult}</pre>
        </div>
        <div>
          <div className="section-title">{labels.expandedGraph}</div>
          <pre>{expanded ? JSON.stringify(expanded, null, 2) : labels.notExpanded}</pre>
        </div>
      </div>
    </div>
  )
}
